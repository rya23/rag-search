"""RAG Pipeline - LangGraph Implementation"""

import asyncio
from dataclasses import dataclass, field
from typing import Generator, List


@dataclass
class MultiQueryStep:
    """Observability data produced by the multi-query retriever."""

    prompt_sent: str
    generated_queries: List[str]
    per_query_docs: List[dict] = field(default_factory=list)


class RAGPipeline:
    def __init__(self, k: int = 5, with_checkpointing: bool = False):
        self.k = k
        self.with_checkpointing = with_checkpointing
        self._graph = None
        self._thread_id: str | None = None

    def _ensure_graph(self):
        if self._graph is None:
            from cli.langgraph_pipeline import build_rag_graph

            self._graph = asyncio.run(build_rag_graph(self.with_checkpointing))
        return self._graph

    def set_thread_id(self, thread_id: str) -> "RAGPipeline":
        self._thread_id = thread_id
        return self

    def run(self, query: str) -> str:
        from cli.langgraph_pipeline import run_query

        return asyncio.run(
            run_query(
                query=query,
                k=self.k,
                thread_id=self._thread_id,
                with_checkpointing=self.with_checkpointing,
            )
        )

    def stream_run(self, query: str) -> Generator[str, None, None]:
        async def _async_stream():
            from cli.langgraph_pipeline import stream_query_with_tokens

            async for event in stream_query_with_tokens(
                query=query,
                k=self.k,
                thread_id=self._thread_id,
            ):
                yield event

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = _async_stream()
            while True:
                try:
                    event = loop.run_until_complete(async_gen.__anext__())
                    if isinstance(event, dict):
                        if event.get("type") == "token":
                            yield event["content"]
                        elif event.get("type") == "complete":
                            yield event["answer"]
                            break
                    else:
                        yield event
                except StopAsyncIteration:
                    break
        finally:
            loop.close()


def build_pipeline(k: int = 5, with_checkpointing: bool = False) -> RAGPipeline:
    return RAGPipeline(k=k, with_checkpointing=with_checkpointing)
