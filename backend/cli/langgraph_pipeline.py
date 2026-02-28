"""LangGraph-based RAG Pipeline — build and graph utilities."""

import uuid

from .langgraph.graph import compile_graph, compile_graph_without_checkpointing


async def build_rag_graph(vectorstore, llm, with_checkpointing: bool = True):
    """
    Build and compile the LangGraph RAG pipeline.

    Args:
        vectorstore: Pre-initialised Chroma vectorstore.
        llm: Pre-initialised language model.
        with_checkpointing: If True, enables PostgreSQL state persistence.

    Returns:
        Compiled LangGraph ready for execution.
    """
    if with_checkpointing:
        return await compile_graph(vectorstore, llm)
    else:
        return compile_graph_without_checkpointing(vectorstore, llm)


def generate_thread_id() -> str:
    """Generate a unique thread ID for conversation tracking."""
    return str(uuid.uuid4())
