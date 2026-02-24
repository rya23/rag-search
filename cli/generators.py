from typing import Callable

from langchain_core.messages import SystemMessage, HumanMessage

from .pipeline import PipelineState

SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question using only the provided context.
If the context does not contain enough information to answer, say so clearly.
Be concise and accurate."""


def groq_generator(llm) -> Callable[[PipelineState], PipelineState]:
    """Generates an answer using a Groq LLM and the retrieved docs."""

    def generate(state: PipelineState) -> PipelineState:
        context = "\n\n---\n\n".join(doc.page_content for doc in state.docs)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {state.query}"),
        ]
        response = llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)
        state.answer = content
        return state

    return generate
