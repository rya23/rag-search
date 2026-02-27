"""Node implementations for the LangGraph RAG pipeline."""

from typing import Generator

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

from cli.pipeline_legacy import MultiQueryStep
from cli.retrievers import MULTI_QUERY_PROMPT
from prompts.system_prompt import SYSTEM_PROMPT

from .state import RAGState


# =============================================================================
# Query Analysis Node
# =============================================================================


def analyze_query(state: RAGState) -> dict:
    """
    Analyze the query to determine retrieval strategy.

    Uses rule-based heuristics to classify query complexity:
    - Simple queries: direct similarity search
    - Complex queries: multi-query retrieval with variants

    Returns state updates.
    """
    query = state["query"]

    # Count words
    word_count = len(query.split())

    # Keywords indicating complex intent
    complex_keywords = [
        "compare",
        "analyze",
        "trend",
        "over time",
        "versus",
        "vs",
        "difference between",
        "why did",
        "breakdown",
        "detailed analysis",
        "how does",
        "relationship between",
        "impact of",
        "correlation",
        "historical",
        "evolution",
        "change over",
    ]

    has_complex_intent = any(kw in query.lower() for kw in complex_keywords)

    # Decision logic
    if has_complex_intent or word_count > 15:
        complexity = "complex"
    else:
        complexity = "simple"

    # Track which nodes were executed
    steps = state.get("steps_taken", [])
    steps.append("analyze_query")

    return {
        "query_complexity": complexity,
        "query_length": word_count,
        "has_complex_keywords": has_complex_intent,
        "steps_taken": steps,
    }


# =============================================================================
# Retrieval Nodes
# =============================================================================


def simple_retrieve(state: RAGState) -> dict:
    """
    Simple similarity search retrieval.

    Directly searches the vector store for k most similar documents.
    """
    from db.dependencies import get_vectorstore

    vectorstore = get_vectorstore()
    k = state.get("k", 5)

    docs = vectorstore.similarity_search(state["query"], k=k)

    steps = state.get("steps_taken", [])
    steps.append("simple_retrieve")

    return {
        "docs": docs,
        "retrieval_method": "simple",
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
        "steps_taken": steps,
    }


def multi_query_retrieve(state: RAGState) -> dict:
    """
    Multi-query retrieval with LLM-generated query variants.

    Uses an LLM to generate semantically distinct query reformulations,
    searches for each, and returns deduplicated results.
    """
    from db.dependencies import get_llm, get_vectorstore

    vectorstore = get_vectorstore()
    llm = get_llm()
    k = state.get("k", 5)
    query = state["query"]

    # Generate query variants
    from langchain_classic.retrievers.multi_query import MultiQueryRetriever

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    mq = MultiQueryRetriever.from_llm(
        retriever=base_retriever, llm=llm, prompt=MULTI_QUERY_PROMPT
    )

    # Get the prompt and generated queries
    prompt_sent = MULTI_QUERY_PROMPT.format(question=query)
    llm_result = mq.llm_chain.invoke({"question": query})

    # Retrieve docs for each generated query
    per_query_docs: list[dict] = []
    all_docs: list[Document] = []

    for q in llm_result:
        docs = base_retriever.invoke(q)
        per_query_docs.append({"query": q, "docs": docs})
        all_docs.extend(docs)

    # Deduplicate by content
    unique_docs = {doc.page_content: doc for doc in all_docs}
    final_docs = list(unique_docs.values())

    # Build observability data
    multiquery_steps = MultiQueryStep(
        prompt_sent=prompt_sent,
        generated_queries=list(llm_result),
        per_query_docs=per_query_docs,
    )

    steps = state.get("steps_taken", [])
    steps.append("multi_query_retrieve")

    return {
        "docs": final_docs,
        "retrieval_method": "multi",
        "retrieval_attempts": state.get("retrieval_attempts", 0) + 1,
        "multiquery_steps": multiquery_steps,
        "steps_taken": steps,
    }


# =============================================================================
# Generation Nodes
# =============================================================================


def generate_answer(state: RAGState) -> dict:
    """
    Generate final answer using retrieved documents.

    Non-streaming version.
    """
    from db.dependencies import get_llm

    llm = get_llm()

    # Format context from retrieved docs
    context = "\n\n---\n\n".join(doc.page_content for doc in state["docs"])

    # Build messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
You are a financial analysis assistant with expertise in market trends and financial data.

RETRIEVED INFORMATION:
{context}

USER QUESTION: {state["query"]}


Based STRICTLY on the RETRIEVED INFORMATION above, provide a detailed financial analysis addressing the user's question. Include relevant metrics, trends, and financial insights from the documents.

Instructions:

* Cite all numerical values.
* Specify fiscal years.
* Show calculations if applicable.
* Do not use external knowledge.
* If insufficient information exists, explicitly state that.

If the retrieved information doesn't contain sufficient data to answer the question, clearly state this limitation.
"""
        ),
    ]

    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "\n".join(str(item) for item in content)

    steps = state.get("steps_taken", [])
    steps.append("generate_answer")

    return {
        "answer": content,
        "steps_taken": steps,
    }


def generate_answer_stream(state: RAGState) -> Generator[str, None, None]:
    """
    Generate final answer using retrieved documents (streaming version).

    Yields answer tokens as they are generated.
    """
    from db.dependencies import get_llm

    llm = get_llm()

    # Format context from retrieved docs
    context = "\n\n---\n\n".join(doc.page_content for doc in state["docs"])

    # Build messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
You are a financial analysis assistant with expertise in market trends and financial data.

RETRIEVED INFORMATION:
{context}

USER QUESTION: {state["query"]}


Based STRICTLY on the RETRIEVED INFORMATION above, provide a detailed financial analysis addressing the user's question. Include relevant metrics, trends, and financial insights from the documents.

Instructions:

* Cite all numerical values.
* Specify fiscal years.
* Show calculations if applicable.
* Do not use external knowledge.
* If insufficient information exists, explicitly state that.

If the retrieved information doesn't contain sufficient data to answer the question, clearly state this limitation.
"""
        ),
    ]

    for chunk in llm.stream(messages):
        content = chunk.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)
        if content:
            yield content
