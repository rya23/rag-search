"""
Query interface for the RAG pipeline.

This module provides the main functions for querying the RAG system.
Now powered by LangGraph with intelligent query routing.
"""

from dotenv import load_dotenv
from .pipeline import RAGPipeline, build_pipeline, rag_query, rag_query_stream

load_dotenv()

# Keep for backward compatibility
RETRIEVER_MODES = ("simple", "multi")

# Re-export for convenience
__all__ = [
    "build_pipeline",
    "rag_query",
    "rag_query_stream",
    "RAGPipeline",
]
