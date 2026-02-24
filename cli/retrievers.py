from typing import Callable

from .pipeline import PipelineState


def simple_retriever(
    vectorstore, k: int = 5
) -> Callable[[PipelineState], PipelineState]:
    """Retrieves top-k documents via direct similarity search."""

    def retrieve(state: PipelineState) -> PipelineState:
        state.docs = vectorstore.similarity_search(state.query, k=k)
        return state

    return retrieve


def multi_query_retriever(
    vectorstore, llm, k: int = 5
) -> Callable[[PipelineState], PipelineState]:
    """
    Generates multiple query variants with an LLM, searches for each,
    and returns the deduplicated union of results.
    """
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    mq = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

    def retrieve(state: PipelineState) -> PipelineState:
        state.docs = mq.invoke(state.query)
        return state

    return retrieve
