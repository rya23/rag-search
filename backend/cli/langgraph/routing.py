"""Conditional routing logic for the adaptive matryoshka RAG pipeline."""

from .state import RAGState


def route_after_eval(state: RAGState) -> str:
    """
    Route based on retrieval quality established by evaluate_retrieval.

    Returns:
        'generate_answer'                if quality == 'strong'
        'high_dim_multi_query_retrieve'  if quality == 'weak'
    """
    if state.get("retrieval_quality", "weak") == "strong":
        return "generate_answer"
    return "high_dim_multi_query_retrieve"
