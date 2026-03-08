"""LangGraph-based RAG Pipeline — build and graph utilities."""

import uuid

from .langgraph.graph import compile_graph, compile_graph_without_checkpointing


async def build_rag_graph(
    vectorstore_128d, vectorstore_768d, llm, reranker, with_checkpointing: bool = True
):
    """
    Build and compile the adaptive matryoshka RAG pipeline.

    Args:
        vectorstore_128d: Pre-initialised 128d Chroma vectorstore.
        vectorstore_768d: Pre-initialised 768d Chroma vectorstore.
        llm: Pre-initialised language model.
        reranker: Pre-initialised cross-encoder reranker.
        with_checkpointing: If True, enables PostgreSQL state persistence.

    Returns:
        Compiled LangGraph ready for execution.
    """
    if with_checkpointing:
        return await compile_graph(vectorstore_128d, vectorstore_768d, llm, reranker)
    else:
        return compile_graph_without_checkpointing(
            vectorstore_128d, vectorstore_768d, llm, reranker
        )


def generate_thread_id() -> str:
    """Generate a unique thread ID for conversation tracking."""
    return str(uuid.uuid4())
