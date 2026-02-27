"""Conditional routing logic for the LangGraph RAG pipeline."""

from .state import RAGState


def route_retrieval(state: RAGState) -> str:
    """
    Route to appropriate retrieval strategy based on query analysis.

    Returns the name of the node to execute next:
    - "simple_retrieve": for straightforward queries
    - "multi_query_retrieve": for complex analytical queries
    """
    complexity = state.get("query_complexity", "simple")

    if complexity == "complex":
        return "multi_query_retrieve"
    else:
        return "simple_retrieve"
