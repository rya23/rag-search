"""RAG Pipeline - LangGraph Implementation"""

import asyncio
from dataclasses import dataclass, field
from typing import Generator, List

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig


@dataclass
class MultiQueryStep:
    """Observability data produced by the multi-query retriever."""

    prompt_sent: str
    generated_queries: List[str]
    per_query_docs: List[dict] = field(default_factory=list)


def _build_initial_state(query: str, k: int) -> dict:
    return {
        "query": query,
        "messages": [HumanMessage(content=query)],
        "k": k,
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


class RAGPipeline:
    def __init__(self, k: int = 5, with_checkpointing: bool = False):
        self.k = k
        self._thread_id: str | None = None

        # Load deps and build graph here (sync context, no running event loop yet)
        from database.dependencies import (
            get_llm,
            get_reranker,
            get_vectorstore_128d,
            get_vectorstore_768d,
        )
        from cli.langgraph_pipeline import build_rag_graph

        vectorstore_128d = get_vectorstore_128d()
        vectorstore_768d = get_vectorstore_768d()
        llm = get_llm()
        reranker = get_reranker()
        self._graph = asyncio.run(
            build_rag_graph(
                vectorstore_128d, vectorstore_768d, llm, reranker, with_checkpointing
            )
        )

    def set_thread_id(self, thread_id: str) -> "RAGPipeline":
        self._thread_id = thread_id
        return self

    def _make_config(self) -> RunnableConfig:
        config: RunnableConfig = {}
        if self._thread_id:
            config["configurable"] = {"thread_id": self._thread_id}
        return config

    def run(self, query: str) -> str:
        async def _run():
            result = await self._graph.ainvoke(
                _build_initial_state(query, self.k), config=self._make_config()
            )
            return result["answer"]

        return asyncio.run(_run())

    def stream_run(self, query: str) -> Generator[str, None, None]:
        async def _async_stream():
            async for event in self._graph.astream_events(
                _build_initial_state(query, self.k),
                config=self._make_config(),
                version="v2",
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk is not None:
                        content = chunk.content
                        if isinstance(content, list):
                            content = "\n".join(str(i) for i in content)
                        if content:
                            yield content

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = _async_stream()
            while True:
                try:
                    yield loop.run_until_complete(async_gen.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            loop.close()


def build_pipeline(k: int = 5, with_checkpointing: bool = False) -> RAGPipeline:
    return RAGPipeline(k=k, with_checkpointing=with_checkpointing)
