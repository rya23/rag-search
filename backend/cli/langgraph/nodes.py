"""Node implementations for the adaptive matryoshka RAG pipeline."""

import os

from langchain_classic.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from cli.pipeline import MultiQueryStep
from prompts.system_prompt import SYSTEM_PROMPT

from .state import RAGState


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
    input_variables=["question"],
)

_ANSWER_PROMPT = """\
You are a financial analysis assistant with expertise in market trends and financial data.

RETRIEVED INFORMATION:
{context}

USER QUESTION: {query}


Based STRICTLY on the RETRIEVED INFORMATION above, provide a detailed financial analysis addressing the user's question. Include relevant metrics, trends, and financial insights from the documents.

Instructions:

* Cite all numerical values.
* Specify fiscal years.
* Show calculations if applicable.
* Do not use external knowledge.
* If insufficient information exists, explicitly state that.

If the retrieved information doesn't contain sufficient data to answer the question, clearly state this limitation.
"""


# =============================================================================
# Retrieval Node Factories
# =============================================================================


def make_low_dim_retrieve(vectorstore_128d):
    """Return a low_dim_retrieve node using the 128d Chroma collection."""

    def low_dim_retrieve(state: RAGState) -> dict:
        docs = vectorstore_128d.similarity_search(state["query"], k=state.get("k", 5))
        steps = state.get("steps_taken", [])
        steps.append("low_dim_retrieve")
        return {
            "docs": docs,
            "retrieval_method": "low_dim",
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
            "embedding_dim": 128,
            "steps_taken": steps,
        }

    return low_dim_retrieve


def make_rerank(reranker, step_name: str = "rerank"):
    """
    Return a rerank node using a local cross-encoder.

    Scores all (query, doc) pairs, sorts by score descending, and stores
    scores in state so evaluate_retrieval can read them.

    step_name allows the same factory to produce both the initial rerank
    and the final rerank nodes without duplicating logic.
    """

    def rerank(state: RAGState) -> dict:
        query = state["query"]
        docs = state["docs"]
        steps = state.get("steps_taken", [])
        steps.append(step_name)

        if not docs:
            return {"docs": [], "rerank_scores": [], "steps_taken": steps}

        pairs = [(query, doc.page_content) for doc in docs]
        raw_scores = reranker.predict(pairs)

        ranked = sorted(zip(raw_scores, docs), key=lambda pair: pair[0], reverse=True)
        sorted_scores = [float(score) for score, _ in ranked]
        sorted_docs = [doc for _, doc in ranked]

        return {
            "docs": sorted_docs,
            "rerank_scores": sorted_scores,
            "steps_taken": steps,
        }

    return rerank


def evaluate_retrieval(state: RAGState) -> dict:
    """
    Check top-1 cross-encoder score against threshold to classify retrieval quality.

    Reads RERANK_QUALITY_THRESHOLD from environment (default 0.3).
    Sets retrieval_quality to 'strong' or 'weak' for routing.
    """
    threshold = float(os.environ.get("RERANK_QUALITY_THRESHOLD", "0.3"))
    scores = state.get("rerank_scores", [])
    top_score = scores[0] if scores else 0.0
    quality = "strong" if top_score >= threshold else "weak"

    steps = state.get("steps_taken", [])
    steps.append("evaluate_retrieval")

    return {"retrieval_quality": quality, "steps_taken": steps}


def make_high_dim_multi_query_retrieve(vectorstore_768d, llm):
    """
    Return a high_dim_multi_query_retrieve node using the 768d collection
    with multi-query expansion. Only invoked when retrieval quality is weak.
    """
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    def high_dim_multi_query_retrieve(state: RAGState) -> dict:
        k = state.get("k", 5)
        query = state["query"]

        base_retriever = vectorstore_768d.as_retriever(search_kwargs={"k": k})
        mq = MultiQueryRetriever.from_llm(
            retriever=base_retriever, llm=llm, prompt=MULTI_QUERY_PROMPT
        )

        prompt_sent = MULTI_QUERY_PROMPT.format(question=query)
        llm_result = mq.llm_chain.invoke({"question": query})

        per_query_docs: list[dict] = []
        all_docs: list[Document] = []

        for q in llm_result:
            docs = base_retriever.invoke(q)
            per_query_docs.append({"query": q, "docs": docs})
            all_docs.extend(docs)

        unique_docs = {doc.page_content: doc for doc in all_docs}

        steps = state.get("steps_taken", [])
        steps.append("high_dim_multi_query_retrieve")

        return {
            "docs": list(unique_docs.values()),
            "retrieval_method": "high_dim_multi",
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
            "embedding_dim": 768,
            "multiquery_steps": MultiQueryStep(
                prompt_sent=prompt_sent,
                generated_queries=list(llm_result),
                per_query_docs=per_query_docs,
            ),
            "steps_taken": steps,
        }

    return high_dim_multi_query_retrieve


# =============================================================================
# Generation Node Factory
# =============================================================================


def make_generate_answer(llm):
    """Return a generate_answer node with llm injected."""

    def generate_answer(state: RAGState) -> dict:
        context = "\n\n---\n\n".join(doc.page_content for doc in state["docs"])
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=_ANSWER_PROMPT.format(context=context, query=state["query"])
            ),
        ]
        response = llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)

        steps = state.get("steps_taken", [])
        steps.append("generate_answer")
        return {"answer": content, "steps_taken": steps}

    return generate_answer
