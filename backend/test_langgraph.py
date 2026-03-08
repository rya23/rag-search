"""
Quick test script for the adaptive matryoshka RAG pipeline.

Tests basic structure without requiring a full database or API setup.
"""

import asyncio
import sys


async def test_graph_structure():
    """Test that the graph compiles with the correct node set."""
    print("=" * 60)
    print("TEST 1: Graph Structure")
    print("=" * 60)

    try:
        from cli.langgraph.graph import build_graph
        from unittest.mock import MagicMock

        # Provide mock deps so graph can be built without real credentials
        mock_vs = MagicMock()
        mock_llm = MagicMock()
        mock_reranker = MagicMock()

        graph = build_graph(mock_vs, mock_vs, mock_llm, mock_reranker)
        print("✓ Graph built successfully")

        nodes = list(graph.nodes.keys())
        expected_nodes = [
            "low_dim_retrieve",
            "rerank",
            "evaluate_retrieval",
            "high_dim_multi_query_retrieve",
            "rerank_final",
            "generate_answer",
        ]

        for node in expected_nodes:
            if node in nodes:
                print(f"✓ Node '{node}' present")
            else:
                print(f"✗ Node '{node}' MISSING")
                return False

        print("\n✓ All nodes present in graph")
        return True

    except Exception as e:
        print(f"✗ Error building graph: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_state_schema():
    """Test that the state schema includes all required fields."""
    print("\n" + "=" * 60)
    print("TEST 2: State Schema")
    print("=" * 60)

    try:
        from cli.langgraph.state import RAGState

        test_state: RAGState = {
            "query": "Test query",
            "messages": [],
            "k": 5,
            "query_complexity": "",
            "query_length": 0,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "",
            "retrieval_attempts": 0,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
            "rerank_scores": [],
            "retrieval_quality": "",
            "embedding_dim": 0,
        }

        print(f"✓ RAGState schema validated with all fields")
        print(f"  - Query: {test_state['query']}")
        print(f"  - embedding_dim: {test_state['embedding_dim']}")
        print(f"  - retrieval_quality: '{test_state['retrieval_quality']}'")
        print(f"  - rerank_scores: {test_state['rerank_scores']}")

        return True

    except Exception as e:
        print(f"✗ Error with state schema: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_evaluate_retrieval_node():
    """Test the retrieval quality evaluation node logic."""
    print("\n" + "=" * 60)
    print("TEST 3: Evaluate Retrieval Node")
    print("=" * 60)

    try:
        import os

        os.environ.setdefault("RERANK_QUALITY_THRESHOLD", "0.3")

        from cli.langgraph.nodes import evaluate_retrieval
        from cli.langgraph.state import RAGState

        base_state: RAGState = {
            "query": "What is the revenue?",
            "messages": [],
            "k": 5,
            "query_complexity": "",
            "query_length": 0,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "low_dim",
            "retrieval_attempts": 1,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": ["low_dim_retrieve", "rerank"],
            "rerank_scores": [0.85, 0.60, 0.20],
            "retrieval_quality": "",
            "embedding_dim": 128,
        }

        result = evaluate_retrieval(base_state)
        print(f"✓ Strong retrieval (top score=0.85 >= 0.3):")
        print(f"  - retrieval_quality: {result['retrieval_quality']}")
        assert result["retrieval_quality"] == "strong", "Expected 'strong'"

        weak_state = dict(base_state)
        weak_state["rerank_scores"] = [0.15, 0.10, 0.05]
        result2 = evaluate_retrieval(weak_state)
        print(f"\n✓ Weak retrieval (top score=0.15 < 0.3):")
        print(f"  - retrieval_quality: {result2['retrieval_quality']}")
        assert result2["retrieval_quality"] == "weak", "Expected 'weak'"

        empty_state = dict(base_state)
        empty_state["rerank_scores"] = []
        result3 = evaluate_retrieval(empty_state)
        print(f"\n✓ Empty scores → weak:")
        print(f"  - retrieval_quality: {result3['retrieval_quality']}")
        assert result3["retrieval_quality"] == "weak", (
            "Expected 'weak' for empty scores"
        )

        return True

    except Exception as e:
        print(f"✗ Error in evaluate_retrieval: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_routing_logic():
    """Test the route_after_eval conditional routing."""
    print("\n" + "=" * 60)
    print("TEST 4: Routing Logic")
    print("=" * 60)

    try:
        from cli.langgraph.routing import route_after_eval
        from cli.langgraph.state import RAGState

        base_state: RAGState = {
            "query": "Test",
            "messages": [],
            "k": 5,
            "query_complexity": "",
            "query_length": 0,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "low_dim",
            "retrieval_attempts": 1,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
            "rerank_scores": [0.85],
            "retrieval_quality": "strong",
            "embedding_dim": 128,
        }

        route = route_after_eval(base_state)
        print(f"✓ Strong quality routes to: {route}")
        assert route == "generate_answer", f"Expected 'generate_answer', got '{route}'"

        weak_state = dict(base_state)
        weak_state["retrieval_quality"] = "weak"
        route2 = route_after_eval(weak_state)
        print(f"✓ Weak quality routes to: {route2}")
        assert route2 == "high_dim_multi_query_retrieve", (
            f"Expected 'high_dim_multi_query_retrieve', got '{route2}'"
        )

        return True

    except Exception as e:
        print(f"✗ Error in routing logic: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ADAPTIVE MATRYOSHKA RAG PIPELINE - STRUCTURE TESTS")
    print("=" * 60 + "\n")

    results = []

    results.append(await test_graph_structure())
    results.append(await test_state_schema())
    results.append(await test_evaluate_retrieval_node())
    results.append(await test_routing_logic())

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Run: rag ingest data/report.md  (creates 128d + 768d collections)")
        print("  2. Run: rag query -q 'What is the revenue?'")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
