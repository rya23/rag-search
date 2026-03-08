"""
Graph visualization helper for the LangGraph RAG pipeline.

This script generates a visual representation of the graph structure.
"""

import asyncio


async def visualize_graph():
    """Generate and save a visualization of the RAG pipeline graph."""
    from unittest.mock import MagicMock
    from cli.langgraph.graph import build_graph

    mock_vs = MagicMock()
    mock_llm = MagicMock()
    mock_reranker = MagicMock()

    graph = build_graph(mock_vs, mock_vs, mock_llm, mock_reranker)

    # Compile the graph
    compiled = graph.compile()

    try:
        # Try to generate Mermaid diagram
        mermaid = compiled.get_graph().draw_mermaid()

        print("LangGraph RAG Pipeline - Mermaid Diagram")
        print("=" * 60)
        print(mermaid)
        print("=" * 60)

        # Save to file
        with open("graph_visualization.mmd", "w") as f:
            f.write(mermaid)
        print("\n✓ Saved to: graph_visualization.mmd")
        print("\nYou can visualize this at: https://mermaid.live/")

    except Exception as e:
        print(f"Could not generate Mermaid diagram: {e}")
        print("\nGraph structure:")
        print(f"Nodes: {list(graph.nodes.keys())}")
        print(f"Edges: {graph.edges}")


if __name__ == "__main__":
    asyncio.run(visualize_graph())
