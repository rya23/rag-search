"""StateGraph construction for the LangGraph RAG pipeline."""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    analyze_query,
    generate_answer,
    multi_query_retrieve,
    simple_retrieve,
)
from .routing import route_retrieval
from .state import RAGState


def build_graph() -> StateGraph:
    """
    Build the LangGraph StateGraph for the RAG pipeline.

    Graph structure:

        START
          ↓
      analyze_query (classify complexity)
          ↓
      [conditional routing]
          ↓
      ┌───────┴────────┐
      ↓                ↓
    simple_retrieve  multi_query_retrieve
      ↓                ↓
      └────────┬───────┘
               ↓
        generate_answer
               ↓
              END

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Initialize the graph
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("simple_retrieve", simple_retrieve)
    graph.add_node("multi_query_retrieve", multi_query_retrieve)
    graph.add_node("generate_answer", generate_answer)

    # Define edges
    graph.add_edge(START, "analyze_query")

    # Conditional routing based on query complexity
    graph.add_conditional_edges(
        "analyze_query",
        route_retrieval,
        {
            "simple_retrieve": "simple_retrieve",
            "multi_query_retrieve": "multi_query_retrieve",
        },
    )

    # Both retrieval strategies flow to generation
    graph.add_edge("simple_retrieve", "generate_answer")
    graph.add_edge("multi_query_retrieve", "generate_answer")

    # Generation flows to end
    graph.add_edge("generate_answer", END)

    return graph


async def compile_graph():
    """
    Compile the graph with PostgreSQL checkpointing enabled.

    Returns:
        Compiled graph ready for .invoke() or .stream() calls.
    """
    from .checkpointer import get_or_create_checkpointer

    graph = build_graph()
    checkpointer = await get_or_create_checkpointer()

    return graph.compile(checkpointer=checkpointer)


def compile_graph_without_checkpointing():
    """
    Compile the graph without checkpointing (for simpler use cases).

    Returns:
        Compiled graph without state persistence.
    """
    graph = build_graph()
    return graph.compile()
