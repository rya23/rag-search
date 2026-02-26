from dataclasses import dataclass, field
from typing import Callable, Generator, List, Union

from langchain_core.documents import Document


@dataclass
class PipelineState:
    query: str
    docs: List[Document] = field(default_factory=list)
    answer: str = ""


class RAGPipeline:
    """
    Extensible RAG pipeline.

    Stages (in order):
      1. retriever  - populates state.docs from state.query
      2. steps      - ordered middleware (reranking, deduplication, etc.)
      3. generator  - populates state.answer from state.query + state.docs

    Each callable has signature: (PipelineState) -> PipelineState
    Use add_step() to insert new stages between retrieval and generation.
    """

    def __init__(self):
        self._retriever: Callable[[PipelineState], PipelineState] | None = None
        self._steps: List[Callable[[PipelineState], PipelineState]] = []
        self._generator: Callable[[PipelineState], PipelineState] | None = None
        self._stream_generator: (
            Callable[[PipelineState], Generator[str, None, None]] | None
        ) = None

    def set_retriever(
        self, fn: Callable[[PipelineState], PipelineState]
    ) -> "RAGPipeline":
        self._retriever = fn
        return self

    def add_step(self, fn: Callable[[PipelineState], PipelineState]) -> "RAGPipeline":
        """Append a post-retrieval step. Returns self for chaining."""
        self._steps.append(fn)
        return self

    def set_generator(
        self, fn: Callable[[PipelineState], PipelineState]
    ) -> "RAGPipeline":
        self._generator = fn
        return self

    def set_stream_generator(
        self, fn: Callable[[PipelineState], Generator[str, None, None]]
    ) -> "RAGPipeline":
        """Set the generator for streaming. Returns self for chaining."""
        self._stream_generator = fn
        return self

    def run(self, query: str) -> str:
        if self._retriever is None:
            raise ValueError("No retriever set. Call set_retriever() before run().")
        if self._generator is None:
            raise ValueError("No generator set. Call set_generator() before run().")

        state = PipelineState(query=query)
        state = self._retriever(state)
        for step in self._steps:
            state = step(state)
        state = self._generator(state)
        return state.answer

    def stream_run(self, query: str) -> Generator[str, None, None]:
        if self._retriever is None:
            raise ValueError(
                "No retriever set. Call set_retriever() before stream_run()."
            )
        if self._stream_generator is None:
            raise ValueError(
                "No stream generator set. Call set_stream_generator() before stream_run()."
            )

        state = PipelineState(query=query)
        state = self._retriever(state)
        for step in self._steps:
            state = step(state)
        yield from self._stream_generator(state)
