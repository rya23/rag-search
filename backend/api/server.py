"""
RAG Observability API
=====================
Endpoints:

  POST /api/query
    Body: { "query": str, "k": int, "thread_id": str? }
    Response: SSE stream
      - {"type":"trace_id", "data":"<uuid>"}   first event
      - {"type":"node",      "data":"<node_name>"} node execution start
      - {"type":"token",    "data":"..."}       one per LLM token
      - {"type":"error",    "data":"..."}       on failure
      - {"type":"done"}                         final event

    Note: Uses LangGraph with automatic query routing.
    The 'mode' parameter is deprecated (routing is now automatic).
    Provide 'thread_id' to continue a conversation.

  POST /api/conversation
    Body: { "query": str, "thread_id": str?, "k": int? }
    Response: SSE stream (same as /api/query)

    Creates or continues a conversation. If thread_id is not provided,
    a new conversation thread is created.

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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Make project root importable when running via uvicorn from repo root
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

load_dotenv()

app = FastAPI(title="RAG Observability API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    query: str
    k: int = 5
    thread_id: str | None = None  # for conversation continuity
    mode: str | None = None  # deprecated, kept for backward compatibility


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _sse_events_langgraph(
    trace_id: str,
    query: str,
    k: int,
    thread_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Async generator that drives the LangGraph RAG pipeline and yields SSE lines."""
    from langchain_core.messages import HumanMessage
    from langchain_core.runnables import RunnableConfig

    from cli.langgraph_pipeline import build_rag_graph, generate_thread_id
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    t_start = time.perf_counter()

    # Generate thread_id if not provided
    if thread_id is None:
        thread_id = generate_thread_id()

    # -- emit trace_id and thread_id immediately --
    yield _sse({"type": "trace_id", "data": trace_id})
    yield _sse({"type": "thread_id", "data": thread_id})

    # -- create the trace record (mode is "auto" for LangGraph) --
    await store.create_trace(trace_id, query, "auto", k, time.time())

    try:
        # Build the graph with checkpointing enabled for conversations
        graph = await build_rag_graph(with_checkpointing=(thread_id is not None))

        # Prepare initial state
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

        config: RunnableConfig = {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        # Collect response for tracing
        response_chunks: list[str] = []
        retriever_ms = 0
        generator_ms = 0
        docs = []
        retrieval_method = ""
        multiquery_steps = None
        final_state = None

        # Track timing
        t_retrieval = None
        t_generation = None

        # Stream node execution
        async for event in graph.astream(initial_state, config=config):
            for node_name, node_state in event.items():
                # Emit node execution event
                yield _sse({"type": "node", "data": node_name})

                # Store final state
                final_state = node_state

                # Track timing and extract data
                if node_name == "analyze_query":
                    pass  # Just analysis, no timing needed

                elif node_name in ["simple_retrieve", "multi_query_retrieve"]:
                    if t_retrieval is None:
                        t_retrieval = time.perf_counter()

                    # Extract docs and retrieval method
                    docs = node_state.get("docs", [])
                    retrieval_method = node_state.get("retrieval_method", node_name)
                    multiquery_steps = node_state.get("multiquery_steps")
                    retriever_ms = int((time.perf_counter() - t_retrieval) * 1000)

                    # Emit retrieval method
                    yield _sse({"type": "retrieval_method", "data": retrieval_method})

                elif node_name == "generate_answer":
                    if t_generation is None:
                        t_generation = time.perf_counter()

                    # Extract answer (note: not streaming tokens in this implementation)
                    answer = node_state.get("answer", "")
                    if answer:
                        response_chunks = [answer]
                        # Emit the complete answer as a single "token"
                        yield _sse({"type": "token", "data": answer})

                    generator_ms = int((time.perf_counter() - t_generation) * 1000)

        # Save retrieved docs + timing
        if docs:
            await store.save_docs(trace_id, docs, retriever_ms)

        # Save multi-query steps if available
        if multiquery_steps is not None:
            mqs = multiquery_steps
            await store.save_multiquery_steps(
                trace_id,
                mqs.prompt_sent,
                mqs.generated_queries,
                mqs.per_query_docs,
            )

        # Calculate total time
        total_ms = int((time.perf_counter() - t_start) * 1000)
        full_response = "".join(response_chunks)

        # Update trace with retrieval method
        await store.complete_trace(trace_id, full_response, generator_ms, total_ms)

        # Update the mode field to reflect actual retrieval method
        if retrieval_method:
            await store.update_trace_mode(trace_id, retrieval_method)

        yield _sse({"type": "done"})

    except Exception as exc:
        import traceback

        error_details = f"{exc}\n{traceback.format_exc()}"
        await store.fail_trace(trace_id, error_details)
        yield _sse({"type": "error", "data": str(exc)})
        yield _sse({"type": "done"})

    # except Exception as exc:
    #     import traceback

    #     error_details = f"{exc}\n{traceback.format_exc()}"
    #     await store.fail_trace(trace_id, error_details)
    #     yield _sse({"type": "error", "data": str(exc)})
    #     yield _sse({"type": "done"})

    # except Exception as exc:
    #     await store.fail_trace(trace_id, str(exc))
    #     yield _sse({"type": "error", "data": str(exc)})
    #     yield _sse({"type": "done"})


def _run_retrieval(query: str, mode: str, k: int):
    """Synchronous retrieval step; returns (state, retriever_ms).

    DEPRECATED: Legacy function for backward compatibility.
    New code should use LangGraph pipeline.
    """
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
    """Async generator that drives the full traced RAG pipeline and yields SSE lines.

    DEPRECATED: Legacy function for backward compatibility.
    New code should use _sse_events_langgraph.
    """
    from cli.generators import groq_stream_generator
    from db.dependencies import get_llm
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    t_start = time.perf_counter()

    # -- emit trace_id immediately so the client can link the stream --
    yield _sse({"type": "trace_id", "data": trace_id})

    # -- create the trace record --
    await store.create_trace(trace_id, query, mode, k, time.time())

    # -- retrieval (blocking, run in threadpool) --
    try:
        state, retriever_ms = await asyncio.to_thread(_run_retrieval, query, mode, k)
    except Exception as exc:
        await store.fail_trace(trace_id, str(exc))
        yield _sse({"type": "error", "data": str(exc)})
        yield _sse({"type": "done"})
        return

    # -- save retrieved docs + timing --
    await store.save_docs(trace_id, state.docs, retriever_ms)

    # -- save multi-query internals if applicable --
    if state.multiquery_steps is not None:
        mqs = state.multiquery_steps
        await store.save_multiquery_steps(
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
        if kind == "token" and data is not None:
            response_chunks.append(data)
            yield _sse({"type": "token", "data": data})
        elif kind == "error":
            await store.fail_trace(trace_id, data or "unknown error")
            yield _sse({"type": "error", "data": data})
            yield _sse({"type": "done"})
            return
        elif kind == "done":
            break

    generator_ms = int((time.perf_counter() - t_gen) * 1000)
    total_ms = int((time.perf_counter() - t_start) * 1000)
    full_response = "".join(response_chunks)

    await store.complete_trace(trace_id, full_response, generator_ms, total_ms)

    yield _sse({"type": "done"})


def _sse(data: dict) -> str:
    """Format a dict as an SSE 'data:' line."""
    return f"data: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/api/query")
async def query_endpoint(req: QueryRequest) -> StreamingResponse:
    """
    Query endpoint with automatic routing (LangGraph).

    The 'mode' parameter is deprecated - routing is now automatic.
    Provide 'thread_id' to continue a conversation.
    """
    if req.k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    # Backward compatibility: if mode is provided, log a warning
    if req.mode is not None:
        import logging

        logging.warning(
            f"'mode' parameter is deprecated and ignored. Query routing is now automatic."
        )

    trace_id = str(uuid.uuid4())

    # Use LangGraph implementation
    return StreamingResponse(
        _sse_events_langgraph(trace_id, req.query, req.k, req.thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@app.post("/api/conversation")
async def conversation_endpoint(req: QueryRequest) -> StreamingResponse:
    """
    Conversation endpoint with thread management.

    If thread_id is not provided, a new conversation is created.
    Otherwise, the conversation continues in the existing thread.
    """
    if req.k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    from cli.langgraph_pipeline import generate_thread_id

    # Generate thread_id if not provided
    thread_id = req.thread_id or generate_thread_id()
    trace_id = str(uuid.uuid4())

    return StreamingResponse(
        _sse_events_langgraph(trace_id, req.query, req.k, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/traces")
async def list_traces(limit: int = 50):
    from observability.tracer import get_trace_store

    store = await get_trace_store()
    rows = await store.list_traces(limit)
    # make datetime objects JSON-serialisable
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
    docs = await store.get_docs(trace_id)
    return docs


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
        elif isinstance(v, uuid.UUID):
            out[k] = str(v)
        else:
            out[k] = v
    return out
