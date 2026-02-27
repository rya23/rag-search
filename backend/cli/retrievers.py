from typing import Callable

from langchain_chroma import Chroma
from langchain_classic.prompts import BasePromptTemplate, PromptTemplate
from langchain_classic.schema import Document

from .pipeline import MultiQueryStep, PipelineState


MULTI_QUERY_PROMPT = PromptTemplate(
    template="""
You are an AI language model assistant.

Your task is to generate **3 semantically distinct reformulations** of the user's question for the purpose of retrieving documents from a vector database.

Each reformulation must:

1. Focus on a **different conceptual angle or subtopic** of the original question.
2. Use **substantially different vocabulary and phrasing** (avoid simple paraphrasing).
3. Emphasize different:

   * technical dimensions,
   * use cases,
   * constraints,
   * stakeholders,
   * or theoretical foundations.
4. Share **minimal keyword overlap** with the other generated questions.
5. Be independently useful for retrieving different but relevant documents.

Avoid rewording the same intent. Instead, decompose the question into alternative perspectives.

Output exactly 3 questions, separated by newlines, with no numbering or commentary.
Question: {question}
""",
    input_variables=["question"],  # Exact match required
)


def simple_retriever(
    vectorstore: Chroma, k: int = 5
) -> Callable[[PipelineState], PipelineState]:
    """Retrieves top-k documents via direct similarity search."""

    def retrieve(state: PipelineState) -> PipelineState:
        state.docs = vectorstore.similarity_search(state.query, k=k)
        # state.docs = vectorstore.max_marginal_relevance_search(state.query, k=k)
        return state

    return retrieve


def multi_query_retriever(
    vectorstore: Chroma, llm, k: int = 5
) -> Callable[[PipelineState], PipelineState]:
    """
    Generates multiple query variants with an LLM, searches for each,
    and returns the deduplicated union of results.
    """
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    mq = MultiQueryRetriever.from_llm(
        retriever=base_retriever, llm=llm, prompt=MULTI_QUERY_PROMPT
    )

    # def retrieve(state: PipelineState) -> PipelineState:
    #     print(f"Generating multiple query variants for: {state.query!r}")
    #     state.docs = mq.invoke(state.query)
    #     return state

    def retrieve(state: PipelineState):
        prompt_sent = MULTI_QUERY_PROMPT.format(question=state.query)
        llm_result = mq.llm_chain.invoke({"question": state.query})

        per_query_docs: list[dict] = []
        all_docs: list[Document] = []

        for q in llm_result:
            docs = base_retriever.invoke(q)
            per_query_docs.append({"query": q, "docs": docs})
            all_docs.extend(docs)

        unique_docs = {doc.page_content: doc for doc in all_docs}
        state.docs = list(unique_docs.values())
        state.multiquery_steps = MultiQueryStep(
            prompt_sent=prompt_sent,
            generated_queries=list(llm_result),
            per_query_docs=per_query_docs,
        )

        return state

    return retrieve
