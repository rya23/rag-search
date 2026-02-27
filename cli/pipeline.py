"""
RAG Pipeline - LangGraph Implementation

This module now uses LangGraph for intelligent query routing and state management.
For the legacy linear pipeline implementation, see pipeline_legacy.py.

The new pipeline provides:
- Automatic query complexity analysis
- Conditional routing (simple vs multi-query retrieval)
- PostgreSQL state persistence and checkpointing
- Multi-turn conversation support
- Enhanced observability and debugging
"""

import asyncio
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable, Generator, List

from langchain_core.documents import Document


# Keep these dataclasses for backward compatibility and observability
@dataclass
class MultiQueryStep:
    """Observability data produced by the multi-query retriever."""

    prompt_sent: str
    generated_queries: List[str]
    # Each entry: {"query": str, "docs": List[Document]}
    per_query_docs: List[dict] = field(default_factory=list)


@dataclass
class PipelineState:
    """Legacy state class - kept for backward compatibility."""

    query: str
    docs: List[Document] = field(default_factory=list)
    answer: str = ""
    multiquery_steps: "MultiQueryStep | None" = None


class RAGPipeline:
    """
    LangGraph-based RAG pipeline with intelligent routing.

    This replaces the simple linear pipeline with a graph-based approach:

    1. Query Analysis - Classifies query complexity automatically
    2. Conditional Routing - Routes to simple or multi-query retrieval
    3. Generation - Produces answer with full context

    Features:
    - Automatic query complexity detection
    - PostgreSQL state persistence
    - Multi-turn conversations
    - Full observability

    Usage:
        pipeline = RAGPipeline(k=5)
        answer = pipeline.run("What was Apple's revenue?")

        # Or with streaming
        for chunk in pipeline.stream_run("Compare Apple and Microsoft"):
            print(chunk, end="")
    """

    def __init__(self, k: int = 5, with_checkpointing: bool = False):
        """
        Initialize the RAG pipeline.

        Args:
            k: Number of documents to retrieve
            with_checkpointing: Enable PostgreSQL state persistence
        """
        self.k = k
        self.with_checkpointing = with_checkpointing
        self._graph = None
        self._thread_id: str | None = None

    def _ensure_graph(self):
        """Lazily compile the graph when needed."""
        if self._graph is None:
            from cli.langgraph_pipeline import build_rag_graph

            self._graph = asyncio.run(build_rag_graph(self.with_checkpointing))
        return self._graph

    def set_thread_id(self, thread_id: str) -> "RAGPipeline":
        """Set thread ID for conversation continuity."""
        self._thread_id = thread_id
        return self

    def run(self, query: str) -> str:
        """
        Run a query through the pipeline (synchronous).

        Args:
            query: User question

        Returns:
            Generated answer
        """
        from cli.langgraph_pipeline import run_query

        return asyncio.run(
            run_query(
                query=query,
                k=self.k,
                thread_id=self._thread_id,
                with_checkpointing=self.with_checkpointing,
            )
        )

    def stream_run(self, query: str) -> Generator[str, None, None]:
        """
        Stream a query through the pipeline (synchronous generator).

        Args:
            query: User question

        Yields:
            Answer tokens and progress updates
        """

        async def _async_stream():
            from cli.langgraph_pipeline import stream_query_with_tokens

            async for event in stream_query_with_tokens(
                query=query,
                k=self.k,
                thread_id=self._thread_id,
            ):
                yield event

        # Bridge async generator to sync generator
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = _async_stream()
            while True:
                try:
                    event = loop.run_until_complete(async_gen.__anext__())
                    # Only yield actual tokens, not progress messages
                    if isinstance(event, dict):
                        if event.get("type") == "token":
                            yield event["content"]
                        elif event.get("type") == "complete":
                            # If we have a complete answer, yield it all at once
                            # This handles the case where streaming wasn't fully implemented
                            yield event["answer"]
                            break
                    else:
                        yield event
                except StopAsyncIteration:
                    break
        finally:
            loop.close()


# Backward compatibility functions
def build_pipeline(
    mode: str = "simple", k: int = 5, with_checkpointing: bool = False
) -> RAGPipeline:
    """
    Build a RAG pipeline (backward compatible interface).

    Note: The 'mode' parameter is now ignored. The pipeline automatically
    determines whether to use simple or multi-query retrieval based on
    query complexity analysis.

    Args:
        mode: Ignored (kept for backward compatibility)
        k: Number of documents to retrieve
        with_checkpointing: Enable PostgreSQL state persistence (required for conversations)

    Returns:
        RAGPipeline instance
    """
    return RAGPipeline(k=k, with_checkpointing=with_checkpointing)


def rag_query(query: str, mode: str = "simple", k: int = 5) -> str:
    """Run a query (backward compatible function)."""
    pipeline = build_pipeline(mode=mode, k=k)
    return pipeline.run(query)


def rag_query_stream(query: str, mode: str = "simple", k: int = 5):
    """Stream a query (backward compatible function)."""
    pipeline = build_pipeline(mode=mode, k=k)
    return pipeline.stream_run(query)
