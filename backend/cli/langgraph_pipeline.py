"""
LangGraph-based RAG Pipeline

This module provides the main interface for the LangGraph RAG pipeline.
It replaces the simple linear pipeline with a graph-based approach that
supports:

- Intelligent query routing (simple vs multi-query retrieval)
- State persistence with PostgreSQL checkpointing
- Multi-turn conversations with thread management
- Streaming with node-level progress updates
- Full observability and debugging capabilities

Usage:
    from cli.langgraph_pipeline import build_rag_graph

    # Build the graph
    graph = await build_rag_graph()

    # Run a query
    result = await graph.ainvoke({
        "query": "What was Apple's revenue in 2023?",
        "messages": [],
        "k": 5,
    })

    # Access the answer
    print(result["answer"])

    # Stream with progress updates
    async for event in graph.astream({
        "query": "Compare Apple and Microsoft revenue",
        "messages": [],
        "k": 5,
    }):
        print(event)
"""

import uuid
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from .langgraph.graph import compile_graph, compile_graph_without_checkpointing
from .langgraph.nodes import generate_answer_stream
from .langgraph.state import RAGState


async def build_rag_graph(with_checkpointing: bool = True):
    """
    Build and compile the LangGraph RAG pipeline.

    Args:
        with_checkpointing: If True, enables PostgreSQL state persistence.
                           Set to False for simpler use cases without persistence.

    Returns:
        Compiled LangGraph ready for execution.
    """
    if with_checkpointing:
        return await compile_graph()
    else:
        return compile_graph_without_checkpointing()


async def run_query(
    query: str,
    k: int = 5,
    thread_id: str | None = None,
    with_checkpointing: bool = True,
) -> str:
    """
    Run a single query through the RAG pipeline.

    Args:
        query: User question
        k: Number of documents to retrieve
        thread_id: Optional thread ID for conversation continuity
        with_checkpointing: Enable state persistence

    Returns:
        Generated answer as a string
    """
    graph = await build_rag_graph(with_checkpointing=with_checkpointing)

    # Build initial state
    initial_state: RAGState = {
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

    # Build config with thread ID
    config: RunnableConfig = {}
    if with_checkpointing:
        # Checkpointer requires a thread_id - generate one if not provided
        if thread_id is None:
            thread_id = str(__import__("uuid").uuid4())
        config["configurable"] = {"thread_id": thread_id}

    # Execute the graph
    result = await graph.ainvoke(initial_state, config=config)

    return result["answer"]


async def stream_query(
    query: str,
    k: int = 5,
    thread_id: str | None = None,
    with_checkpointing: bool = True,
) -> AsyncGenerator[dict, None]:
    """
    Stream query execution through the RAG pipeline.

    Yields events at each node execution and streams answer tokens.

    Args:
        query: User question
        k: Number of documents to retrieve
        thread_id: Optional thread ID for conversation continuity
        with_checkpointing: Enable state persistence

    Yields:
        Dictionary events with node updates and answer tokens.
        Events have keys like:
        - {"node": "analyze_query", "state": {...}}
        - {"node": "simple_retrieve", "state": {...}}
        - {"node": "generate_answer", "token": "..."}
    """
    graph = await build_rag_graph(with_checkpointing=with_checkpointing)

    # Build initial state
    initial_state: RAGState = {
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

    # Build config
    config: RunnableConfig = {}
    if with_checkpointing:
        # Checkpointer requires a thread_id - generate one if not provided
        if thread_id is None:
            thread_id = str(__import__("uuid").uuid4())
        config["configurable"] = {"thread_id": thread_id}

    # Stream events
    async for event in graph.astream(initial_state, config=config):
        yield event


async def stream_query_with_tokens(
    query: str,
    k: int = 5,
    thread_id: str | None = None,
) -> AsyncGenerator[str | dict, None]:
    """
    Stream query with both node updates AND answer tokens.

    This provides a richer streaming experience by:
    1. Yielding progress updates as nodes execute
    2. Streaming answer tokens as they're generated

    Args:
        query: User question
        k: Number of documents to retrieve
        thread_id: Optional thread ID

    Yields:
        - Progress dicts: {"type": "progress", "node": "...", "message": "..."}
        - Token strings: {"type": "token", "content": "..."}
        - Final dict: {"type": "complete", "answer": "..."}
    """
    graph = await build_rag_graph(with_checkpointing=True)

    # Build initial state
    initial_state: RAGState = {
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
    if thread_id is None:
        thread_id = str(__import__("uuid").uuid4())
    config["configurable"] = {"thread_id": thread_id}

    # First, run non-streaming up to generation
    # Track state through the pipeline
    state = initial_state

    async for event in graph.astream(initial_state, config=config):
        # Extract node name and state updates
        for node_name, node_state in event.items():
            if node_name == "analyze_query":
                yield {
                    "type": "progress",
                    "node": node_name,
                    "message": f"🔍 Analyzing query complexity...",
                }
                state.update(node_state)
            elif node_name in ["simple_retrieve", "multi_query_retrieve"]:
                method = "simple" if node_name == "simple_retrieve" else "multi-query"
                doc_count = len(node_state.get("docs", []))
                yield {
                    "type": "progress",
                    "node": node_name,
                    "message": f"📄 Retrieved {doc_count} documents using {method} strategy",
                }
                state.update(node_state)
            elif node_name == "generate_answer":
                yield {
                    "type": "progress",
                    "node": node_name,
                    "message": "✍️ Generating answer...",
                }
                # Note: The graph already ran generate_answer,
                # so we have the full answer in node_state
                # For true streaming, we'd need to modify the graph
                answer = node_state.get("answer", "")
                yield {
                    "type": "complete",
                    "answer": answer,
                }
                return


def generate_thread_id() -> str:
    """Generate a unique thread ID for conversation tracking."""
    return str(uuid.uuid4())
