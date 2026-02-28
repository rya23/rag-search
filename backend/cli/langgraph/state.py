"""State schema for the LangGraph RAG pipeline."""

from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from cli.pipeline import MultiQueryStep


class RAGState(TypedDict):
    """
    State schema for the RAG pipeline.

    This state is passed between all nodes in the graph and tracks:
    - User query and conversation history
    - Query analysis results for routing
    - Retrieved documents and metadata
    - Generated answer
    - Observability data for debugging
    """

    # ===== Input & Conversation =====
    query: str
    """The current user query."""

    messages: Annotated[list[BaseMessage], add_messages]
    """Conversation history for multi-turn support."""

    # ===== Query Analysis (for routing) =====
    query_complexity: str
    """Query complexity classification: 'simple' | 'complex'."""

    query_length: int
    """Number of words in the query."""

    has_complex_keywords: bool
    """Whether query contains keywords suggesting complex retrieval needed."""

    # ===== Retrieval =====
    docs: list[Document]
    """Retrieved documents from vector store."""

    retrieval_method: str
    """Which retrieval strategy was used: 'simple' | 'multi'."""

    retrieval_attempts: int
    """Number of retrieval attempts (for potential re-retrieval logic)."""

    # ===== Generation =====
    answer: str
    """Final generated answer."""

    # ===== Observability & Metadata =====
    multiquery_steps: MultiQueryStep | None
    """Detailed multi-query retrieval data (if applicable)."""

    steps_taken: list[str]
    """Audit trail of which nodes were executed."""

    k: int
    """Number of documents to retrieve (configurable parameter)."""
