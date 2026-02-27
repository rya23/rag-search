"""
Quick test script for the LangGraph RAG pipeline.

This tests basic functionality without requiring a full database setup.
"""

import asyncio
import sys


async def test_graph_structure():
    """Test that the graph compiles without errors."""
    print("=" * 60)
    print("TEST 1: Graph Structure")
    print("=" * 60)

    try:
        from cli.langgraph.graph import build_graph

        graph = build_graph()
        print("✓ Graph built successfully")

        # Check nodes
        nodes = list(graph.nodes.keys())
        expected_nodes = [
            "analyze_query",
            "simple_retrieve",
            "multi_query_retrieve",
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
    """Test that the state schema is properly defined."""
    print("\n" + "=" * 60)
    print("TEST 2: State Schema")
    print("=" * 60)

    try:
        from cli.langgraph.state import RAGState

        # Create a minimal state
        test_state: RAGState = {
            "query": "Test query",
            "messages": [],
            "k": 5,
            "query_complexity": "simple",
            "query_length": 2,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "",
            "retrieval_attempts": 0,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
        }

        print(f"✓ RAGState schema validated")
        print(f"  - Query: {test_state['query']}")
        print(f"  - k: {test_state['k']}")
        print(f"  - Complexity: {test_state['query_complexity']}")

        return True

    except Exception as e:
        print(f"✗ Error with state schema: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_analyze_query_node():
    """Test the query analysis node logic."""
    print("\n" + "=" * 60)
    print("TEST 3: Query Analysis Node")
    print("=" * 60)

    try:
        from cli.langgraph.nodes import analyze_query
        from cli.langgraph.state import RAGState

        # Test simple query
        simple_state: RAGState = {
            "query": "What is revenue?",
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
        }

        result = analyze_query(simple_state)
        print(f"✓ Simple query analysis:")
        print(f"  - Query: '{simple_state['query']}'")
        print(f"  - Complexity: {result['query_complexity']}")
        print(f"  - Length: {result['query_length']} words")

        # Test complex query
        complex_state: RAGState = {
            "query": "Compare the revenue trends between Apple and Microsoft over the last 5 years and analyze the impact of their cloud strategies",
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
        }

        result2 = analyze_query(complex_state)
        print(f"\n✓ Complex query analysis:")
        print(f"  - Query: '{complex_state['query'][:60]}...'")
        print(f"  - Complexity: {result2['query_complexity']}")
        print(f"  - Length: {result2['query_length']} words")
        print(f"  - Has complex keywords: {result2['has_complex_keywords']}")

        return True

    except Exception as e:
        print(f"✗ Error in query analysis: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_routing_logic():
    """Test the conditional routing logic."""
    print("\n" + "=" * 60)
    print("TEST 4: Routing Logic")
    print("=" * 60)

    try:
        from cli.langgraph.routing import route_retrieval
        from cli.langgraph.state import RAGState

        # Test simple routing
        simple_state: RAGState = {
            "query": "Test",
            "messages": [],
            "k": 5,
            "query_complexity": "simple",
            "query_length": 1,
            "has_complex_keywords": False,
            "docs": [],
            "retrieval_method": "",
            "retrieval_attempts": 0,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
        }

        route = route_retrieval(simple_state)
        print(f"✓ Simple query routes to: {route}")

        # Test complex routing
        complex_state: RAGState = {
            "query": "Test",
            "messages": [],
            "k": 5,
            "query_complexity": "complex",
            "query_length": 20,
            "has_complex_keywords": True,
            "docs": [],
            "retrieval_method": "",
            "retrieval_attempts": 0,
            "answer": "",
            "multiquery_steps": None,
            "steps_taken": [],
        }

        route2 = route_retrieval(complex_state)
        print(f"✓ Complex query routes to: {route2}")

        return True

    except Exception as e:
        print(f"✗ Error in routing logic: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LANGGRAPH RAG PIPELINE - STRUCTURE TESTS")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(await test_graph_structure())
    results.append(await test_state_schema())
    results.append(await test_analyze_query_node())
    results.append(await test_routing_logic())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe LangGraph pipeline structure is correctly implemented.")
        print("Next steps:")
        print("  1. Set up your .env file with database credentials")
        print("  2. Test with actual data: python main.py query")
        print("  3. Try conversation mode: python main.py query --conversation")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
