"""StateGraph construction for the LangGraph RAG pipeline."""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_query,
    make_generate_answer,
    make_multi_query_retrieve,
    make_simple_retrieve,
)
from .routing import route_retrieval
from .state import RAGState


def build_graph(vectorstore, llm) -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("analyze_query", analyze_query)
    graph.add_node("simple_retrieve", make_simple_retrieve(vectorstore))
    graph.add_node("multi_query_retrieve", make_multi_query_retrieve(vectorstore, llm))
    graph.add_node("generate_answer", make_generate_answer(llm))

    graph.add_edge(START, "analyze_query")
    graph.add_conditional_edges(
        "analyze_query",
        route_retrieval,
        {
            "simple_retrieve": "simple_retrieve",
            "multi_query_retrieve": "multi_query_retrieve",
        },
    )
    graph.add_edge("simple_retrieve", "generate_answer")
    graph.add_edge("multi_query_retrieve", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph


async def compile_graph(vectorstore, llm):
    """Compile graph with PostgreSQL checkpointing."""
    from .checkpointer import get_or_create_checkpointer

    checkpointer = await get_or_create_checkpointer()
    return build_graph(vectorstore, llm).compile(checkpointer=checkpointer)


def compile_graph_without_checkpointing(vectorstore, llm):
    """Compile graph without checkpointing."""
    return build_graph(vectorstore, llm).compile()
