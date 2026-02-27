"""
RAG Observability API
=====================
Endpoints:

  POST /api/query
    Body: { "query": str, "mode": "simple"|"multi", "k": int }
    Response: SSE stream
      - {"type":"trace_id", "data":"<uuid>"}   first event
      - {"type":"token",    "data":"..."}       one per LLM token
      - {"type":"error",    "data":"..."}       on failure
      - {"type":"done"}                         final event

  GET  /api/traces?limit=50
    Returns list of recent traces (summary).

  GET  /api/traces/{trace_id}
    Returns full trace including retrieved docs.

  GET  /api/traces/{trace_id}/docs
    Returns only the retrieved documents for a trace.
"""

import asyncio
import json
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Make project root importable when running via uvicorn from repo root
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

load_dotenv()

app = FastAPI(title="RAG Observability API")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    query: str
    mode: str = "simple"
    k: int = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_retrieval(query: str, mode: str, k: int):
    """Synchronous retrieval step; returns (state, retriever_ms)."""
    from cli.pipeline import PipelineState
    from cli.retrievers import multi_query_retriever, simple_retriever
    from db.dependencies import get_llm, get_vectorstore

    llm = get_llm()
    vs = get_vectorstore()

    if mode == "simple":
        retriever_fn = simple_retriever(vs, k=k)
    elif mode == "multi":
        retriever_fn = multi_query_retriever(vs, llm, k=k)
    else:
        raise ValueError(f"Unknown retriever mode: {mode!r}")

    state = PipelineState(query=query)
    t0 = time.perf_counter()
    state = retriever_fn(state)
    retriever_ms = int((time.perf_counter() - t0) * 1000)
    return state, retriever_ms


async def _sse_events(
    trace_id: str,
    query: str,
    mode: str,
    k: int,
) -> AsyncGenerator[str, None]:
    """Async generator that drives the full traced RAG pipeline and yields SSE lines."""
    from cli.generators import groq_stream_generator
    from db.dependencies import get_llm
    from observability.tracer import get_trace_store

    store = get_trace_store()
    t_start = time.perf_counter()

    # -- emit trace_id immediately so the client can link the stream --
    yield _sse({"type": "trace_id", "data": trace_id})

    # -- create the trace record --
    await asyncio.to_thread(
        store.create_trace,
        trace_id,
        query,
        mode,
        k,
        time.time(),
    )

    # -- retrieval (blocking, run in threadpool) --
    try:
        state, retriever_ms = await asyncio.to_thread(_run_retrieval, query, mode, k)
    except Exception as exc:
        await asyncio.to_thread(store.fail_trace, trace_id, str(exc))
        yield _sse({"type": "error", "data": str(exc)})
        yield _sse({"type": "done"})
        return

    # -- save retrieved docs + timing --
    await asyncio.to_thread(store.save_docs, trace_id, state.docs, retriever_ms)

    # -- save multi-query internals if applicable --
    if state.multiquery_steps is not None:
        mqs = state.multiquery_steps
        await asyncio.to_thread(
            store.save_multiquery_steps,
            trace_id,
            mqs.prompt_sent,
            mqs.generated_queries,
            mqs.per_query_docs,
        )

    # -- streaming generation bridged from sync to async via Queue --
    queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()
    loop = asyncio.get_event_loop()
    response_chunks: list[str] = []

    def _run_stream():
        try:
            llm = get_llm()
            gen_fn = groq_stream_generator(llm)
            for chunk in gen_fn(state):
                asyncio.run_coroutine_threadsafe(queue.put(("token", chunk)), loop)
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(queue.put(("error", str(exc))), loop)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(("done", None)), loop)

    t_gen = time.perf_counter()
    threading.Thread(target=_run_stream, daemon=True).start()

    while True:
        kind, data = await queue.get()
        if kind == "token":
            response_chunks.append(data)
            yield _sse({"type": "token", "data": data})
        elif kind == "error":
            await asyncio.to_thread(store.fail_trace, trace_id, data or "unknown error")
            yield _sse({"type": "error", "data": data})
            yield _sse({"type": "done"})
            return
        elif kind == "done":
            break

    generator_ms = int((time.perf_counter() - t_gen) * 1000)
    total_ms = int((time.perf_counter() - t_start) * 1000)
    full_response = "".join(response_chunks)

    await asyncio.to_thread(
        store.complete_trace,
        trace_id,
        full_response,
        generator_ms,
        total_ms,
    )

    yield _sse({"type": "done"})


def _sse(data: dict) -> str:
    """Format a dict as an SSE 'data:' line."""
    return f"data: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/api/query")
async def query_endpoint(req: QueryRequest) -> StreamingResponse:
    if req.mode not in ("simple", "multi"):
        raise HTTPException(status_code=400, detail="mode must be 'simple' or 'multi'")
    if req.k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    trace_id = str(uuid.uuid4())
    return StreamingResponse(
        _sse_events(trace_id, req.query, req.mode, req.k),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@app.get("/api/traces")
async def list_traces(limit: int = 50):
    from observability.tracer import get_trace_store

    store = get_trace_store()
    rows = await asyncio.to_thread(store.list_traces, limit)
    # make datetime objects JSON-serialisable
    return [_serialize_row(r) for r in rows]


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    from observability.tracer import get_trace_store

    store = get_trace_store()
    trace = await asyncio.to_thread(store.get_trace, trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    docs = await asyncio.to_thread(store.get_docs, trace_id)
    result = _serialize_row(trace)
    result["docs"] = docs
    return result


@app.get("/api/traces/{trace_id}/docs")
async def get_trace_docs(trace_id: str):
    from observability.tracer import get_trace_store

    store = get_trace_store()
    trace = await asyncio.to_thread(store.get_trace, trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    docs = await asyncio.to_thread(store.get_docs, trace_id)
    return docs


@app.get("/api/traces/{trace_id}/multiquery")
async def get_multiquery_steps(trace_id: str):
    from observability.tracer import get_trace_store

    store = get_trace_store()
    trace = await asyncio.to_thread(store.get_trace, trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    steps = await asyncio.to_thread(store.get_multiquery_steps, trace_id)
    if steps is None:
        raise HTTPException(
            status_code=404,
            detail="No multi-query steps for this trace — was it run with mode=multi?",
        )
    return steps


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _serialize_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
