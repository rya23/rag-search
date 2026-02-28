"""Node implementations for the LangGraph RAG pipeline."""

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
# Query Analysis Node (no deps needed)
# =============================================================================


def analyze_query(state: RAGState) -> dict:
    """Classify query complexity to determine retrieval strategy."""
    query = state["query"]
    word_count = len(query.split())

    complex_keywords = [
        "compare", "analyze", "trend", "over time", "versus", "vs",
        "difference between", "why did", "breakdown", "detailed analysis",
        "how does", "relationship between", "impact of", "correlation",
        "historical", "evolution", "change over",
    ]

    has_complex_intent = any(kw in query.lower() for kw in complex_keywords)
    complexity = "complex" if (has_complex_intent or word_count > 15) else "simple"

    steps = state.get("steps_taken", [])
    steps.append("analyze_query")

    return {
        "query_complexity": complexity,
        "query_length": word_count,
        "has_complex_keywords": has_complex_intent,
        "steps_taken": steps,
    }


# =============================================================================
# Retrieval Node Factories
# =============================================================================


def make_simple_retrieve(vectorstore):
    """Return a simple_retrieve node with vectorstore injected."""

    def simple_retrieve(state: RAGState) -> dict:
        docs = vectorstore.similarity_search(state["query"], k=state.get("k", 5))
        steps = state.get("steps_taken", [])
        steps.append("simple_retrieve")
        return {
            "docs": docs,
            "retrieval_method": "simple",
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
            "steps_taken": steps,
        }

    return simple_retrieve


def make_multi_query_retrieve(vectorstore, llm):
    """Return a multi_query_retrieve node with vectorstore and llm injected."""
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    def multi_query_retrieve(state: RAGState) -> dict:
        k = state.get("k", 5)
        query = state["query"]

        base_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
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
        steps.append("multi_query_retrieve")

        return {
            "docs": list(unique_docs.values()),
            "retrieval_method": "multi",
            "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
            "multiquery_steps": MultiQueryStep(
                prompt_sent=prompt_sent,
                generated_queries=list(llm_result),
                per_query_docs=per_query_docs,
            ),
            "steps_taken": steps,
        }

    return multi_query_retrieve


# =============================================================================
# Generation Node Factory
# =============================================================================


def make_generate_answer(llm):
    """Return a generate_answer node with llm injected."""

    def generate_answer(state: RAGState) -> dict:
        context = "\n\n---\n\n".join(doc.page_content for doc in state["docs"])
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_ANSWER_PROMPT.format(context=context, query=state["query"])),
        ]
        response = llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)

        steps = state.get("steps_taken", [])
        steps.append("generate_answer")
        return {"answer": content, "steps_taken": steps}

    return generate_answer
