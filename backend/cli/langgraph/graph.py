"""StateGraph construction for the adaptive matryoshka RAG pipeline."""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    evaluate_retrieval,
    make_generate_answer,
    make_high_dim_multi_query_retrieve,
    make_low_dim_retrieve,
    make_rerank,
)
from .routing import route_after_eval
from .state import RAGState


def build_graph(vectorstore_128d, vectorstore_768d, llm, reranker) -> StateGraph:
    """
    Build the adaptive matryoshka RAG graph.

    Flow:
        START → low_dim_retrieve → rerank → evaluate_retrieval
                                                ├── strong → generate_answer → END
                                                └── weak → high_dim_multi_query_retrieve
                                                               → rerank_final → generate_answer → END
    """
    graph = StateGraph(RAGState)

    graph.add_node("low_dim_retrieve", make_low_dim_retrieve(vectorstore_128d))
    graph.add_node("rerank", make_rerank(reranker, step_name="rerank"))
    graph.add_node("evaluate_retrieval", evaluate_retrieval)
    graph.add_node(
        "high_dim_multi_query_retrieve",
        make_high_dim_multi_query_retrieve(vectorstore_768d, llm),
    )
    graph.add_node("rerank_final", make_rerank(reranker, step_name="rerank_final"))
    graph.add_node("generate_answer", make_generate_answer(llm))

    graph.add_edge(START, "low_dim_retrieve")
    graph.add_edge("low_dim_retrieve", "rerank")
    graph.add_edge("rerank", "evaluate_retrieval")
    graph.add_conditional_edges(
        "evaluate_retrieval",
        route_after_eval,
        {
            "generate_answer": "generate_answer",
            "high_dim_multi_query_retrieve": "high_dim_multi_query_retrieve",
        },
    )
    graph.add_edge("high_dim_multi_query_retrieve", "rerank_final")
    graph.add_edge("rerank_final", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph


async def compile_graph(vectorstore_128d, vectorstore_768d, llm, reranker):
    """Compile graph with PostgreSQL checkpointing."""
    from .checkpointer import get_or_create_checkpointer

    checkpointer = await get_or_create_checkpointer()
    return build_graph(vectorstore_128d, vectorstore_768d, llm, reranker).compile(
        checkpointer=checkpointer
    )


def compile_graph_without_checkpointing(
    vectorstore_128d, vectorstore_768d, llm, reranker
):
    """Compile graph without checkpointing."""
    return build_graph(vectorstore_128d, vectorstore_768d, llm, reranker).compile()
