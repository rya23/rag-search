from typing import Callable, Generator

from langchain_core.messages import SystemMessage, HumanMessage

from .pipeline import PipelineState
from prompts.system_prompt import SYSTEM_PROMPT


def groq_generator(llm) -> Callable[[PipelineState], PipelineState]:
    """Generates an answer using a Groq LLM and the retrieved docs."""

    def generate(state: PipelineState) -> PipelineState:
        context = "\n\n---\n\n".join(doc.page_content for doc in state.docs)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""
You are a financial analysis assistant with expertise in market trends and financial data.

RETRIEVED INFORMATION:
{context}

USER QUESTION: {state.query}


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
        state.answer = content
        return state

    return generate


def groq_stream_generator(llm) -> Callable[[PipelineState], Generator[str, None, None]]:
    """Streams answer tokens from a Groq LLM using the retrieved docs."""

    def generate(state: PipelineState) -> Generator[str, None, None]:
        context = "\n\n---\n\n".join(doc.page_content for doc in state.docs)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""
You are a financial analysis assistant with expertise in market trends and financial data.

RETRIEVED INFORMATION:
{context}

USER QUESTION: {state.query}


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

    return generate
