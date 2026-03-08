# backend/test_query.py
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cli.pipeline import RAGPipeline, _build_initial_state


async def test_query(question: str, k: int = 5):
    from database.dependencies import (
        get_llm,
        get_reranker,
        get_vectorstore_128d,
        get_vectorstore_768d,
    )
    from cli.langgraph_pipeline import build_rag_graph
    from langchain_core.messages import HumanMessage

    vs_128 = get_vectorstore_128d()
    vs_768 = get_vectorstore_768d()
    llm = get_llm()
    reranker = get_reranker()
    graph = await build_rag_graph(
        vs_128, vs_768, llm, reranker, with_checkpointing=False
    )

    result = await graph.ainvoke(_build_initial_state(question, k))

    print(f"\n--- Query: {question}")
    print(f"Path taken:       {result['steps_taken']}")
    print(f"Retrieval method: {result['retrieval_method']}")
    print(f"Embedding dim:    {result['embedding_dim']}")
    print(f"Quality:          {result['retrieval_quality']}")
    print(f"Rerank scores:    {[round(s, 3) for s in result['rerank_scores'][:3]]}")
    print(f"Docs retrieved:   {len(result['docs'])}")
    print(f"\nAnswer:\n{result['answer'][:300]}...")


asyncio.run(test_query(sys.argv[1] if len(sys.argv) > 1 else "What is the revenue?"))
