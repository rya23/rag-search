"""
RAG Observability API
=====================
Endpoints:

  POST /api/query
    Body: { "query": str, "k": int, "thread_id": str? }
    Response: SSE stream
      - {"type":"trace_id", "data":"<uuid>"}
      - {"type":"thread_id", "data":"<thread_id>"}
      - {"type":"node",      "data":"<node_name>"}
      - {"type":"token",    "data":"..."}
      - {"type":"retrieval_method", "data":"simple"|"multi"}
      - {"type":"error",    "data":"..."}
      - {"type":"done"}

  POST /api/conversation
    Body: { "query": str, "thread_id": str?, "k": int? }
    Response: SSE stream (same as /api/query)

  GET  /api/traces?limit=50
  GET  /api/traces/{trace_id}
  GET  /api/traces/{trace_id}/docs
  GET  /api/traces/{trace_id}/multiquery
"""

import json
import sys
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

load_dotenv()

app = FastAPI(title="RAG Observability API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    k: int = 5
    thread_id: str | None = None


async def _sse_events(
    trace_id: str,
    query: str,
    k: int,
    thread_id: str | None = None,
) -> AsyncGenerator[str, None]:
    from langchain_core.messages import HumanMessage
    from langchain_core.runnables import RunnableConfig

    from cli.langgraph_pipeline import build_rag_graph, generate_thread_id
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    t_start = time.perf_counter()

    if thread_id is None:
        thread_id = generate_thread_id()

    yield _sse({"type": "trace_id", "data": trace_id})
    yield _sse({"type": "thread_id", "data": thread_id})

    await store.create_trace(trace_id, query, "auto", k, time.time())

    try:
        graph = await build_rag_graph(with_checkpointing=(thread_id is not None))

        initial_state = {
            "query": query,
            "messages": [HumanMessage(content=query)],
            "k": k,
            "query_complexity": "",
            "query_length": 0,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "",
            "retrieval_attempts": 0,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
        }

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        response_chunks: list[str] = []
        retriever_ms = 0
        generator_ms = 0
        docs = []
        retrieval_method = ""
        multiquery_steps = None
        t_retrieval = None
        t_generation = None

        _RAG_NODES = {
            "analyze_query",
            "simple_retrieve",
            "multi_query_retrieve",
            "generate_answer",
        }
        _emitted_nodes: set[str] = set()

        async for event in graph.astream_events(
            initial_state, config=config, version="v2"
        ):
            ev_type = event["event"]
            ev_name = event.get("name", "")

            if ev_type == "on_chain_start" and ev_name in _RAG_NODES:
                if ev_name not in _emitted_nodes:
                    _emitted_nodes.add(ev_name)
                    yield _sse({"type": "node", "data": ev_name})

                if (
                    ev_name in ("simple_retrieve", "multi_query_retrieve")
                    and t_retrieval is None
                ):
                    t_retrieval = time.perf_counter()
                elif ev_name == "generate_answer" and t_generation is None:
                    t_generation = time.perf_counter()

            elif ev_type == "on_chain_end" and ev_name in (
                "simple_retrieve",
                "multi_query_retrieve",
            ):
                output = event.get("data", {}).get("output", {}) or {}
                docs = output.get("docs", [])
                retrieval_method = output.get("retrieval_method", ev_name)
                multiquery_steps = output.get("multiquery_steps")
                if t_retrieval is not None:
                    retriever_ms = int((time.perf_counter() - t_retrieval) * 1000)
                yield _sse({"type": "retrieval_method", "data": retrieval_method})

            elif ev_type == "on_chain_end" and ev_name == "generate_answer":
                if t_generation is not None:
                    generator_ms = int((time.perf_counter() - t_generation) * 1000)

            elif ev_type == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                if isinstance(content, list):
                    content = "\n".join(str(item) for item in content)
                if content:
                    response_chunks.append(content)
                    yield _sse({"type": "token", "data": content})

        if docs:
            await store.save_docs(trace_id, docs, retriever_ms)

        if multiquery_steps is not None:
            mqs = multiquery_steps
            await store.save_multiquery_steps(
                trace_id,
                mqs.prompt_sent,
                mqs.generated_queries,
                mqs.per_query_docs,
            )

        total_ms = int((time.perf_counter() - t_start) * 1000)
        full_response = "".join(response_chunks)

        await store.complete_trace(trace_id, full_response, generator_ms, total_ms)

        if retrieval_method:
            await store.update_trace_mode(trace_id, retrieval_method)

        yield _sse({"type": "done"})

    except Exception as exc:
        import traceback

        error_details = f"{exc}\n{traceback.format_exc()}"
        await store.fail_trace(trace_id, error_details)
        yield _sse({"type": "error", "data": str(exc)})
        yield _sse({"type": "done"})


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/api/query")
async def query_endpoint(req: QueryRequest) -> StreamingResponse:
    if req.k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    trace_id = str(uuid.uuid4())
    return StreamingResponse(
        _sse_events(trace_id, req.query, req.k, req.thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/conversation")
async def conversation_endpoint(req: QueryRequest) -> StreamingResponse:
    if req.k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    from cli.langgraph_pipeline import generate_thread_id

    thread_id = req.thread_id or generate_thread_id()
    trace_id = str(uuid.uuid4())

    return StreamingResponse(
        _sse_events(trace_id, req.query, req.k, thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/traces")
async def list_traces(limit: int = 50):
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    rows = await store.list_traces(limit)
    return [_serialize_row(r) for r in rows]


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    trace = await store.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    docs = await store.get_docs(trace_id)
    multiquery_steps = await store.get_multiquery_steps(trace_id)

    result = _serialize_row(trace)
    result["docs"] = docs
    if multiquery_steps:
        result["multiquery_steps"] = multiquery_steps
    return result


@app.get("/api/traces/{trace_id}/docs")
async def get_trace_docs(trace_id: str):
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    trace = await store.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return await store.get_docs(trace_id)


@app.get("/api/traces/{trace_id}/multiquery")
async def get_multiquery_steps(trace_id: str):
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    trace = await store.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    steps = await store.get_multiquery_steps(trace_id)
    if steps is None:
        raise HTTPException(
            status_code=404, detail="No multi-query steps for this trace"
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
        elif isinstance(v, uuid.UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out
