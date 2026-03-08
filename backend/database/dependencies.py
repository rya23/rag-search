import os
from functools import lru_cache
from typing import List

import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq
from pydantic import SecretStr
from sentence_transformers import CrossEncoder, SentenceTransformer

load_dotenv()

COLLECTION_NAME_128D = os.environ["CHROMA_COLLECTION_128D"]
COLLECTION_NAME_768D = os.environ["CHROMA_COLLECTION_768D"]
EMBEDDING_MODEL = os.environ["EMBEDDING_MODEL"]
LLM_MODEL = os.environ["LLM_MODEL"]
RERANKER_MODEL = os.environ.get(
    "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


class TruncatedSentenceTransformerEmbeddings(Embeddings):
    """
    Wraps a SentenceTransformer to produce embeddings at a specific matryoshka
    dimension via truncate_dim. A single model instance is shared across all
    dimension wrappers to avoid loading weights multiple times.
    """

    def __init__(
        self,
        model: SentenceTransformer,
        truncate_dim: int | None = None,
        normalize: bool = True,
    ):
        self._model = model
        self._truncate_dim = truncate_dim
        self._normalize = normalize

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(
            texts,
            truncate_dim=self._truncate_dim,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode(
            text,
            truncate_dim=self._truncate_dim,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
        )
        return vector.tolist()


@lru_cache(maxsize=1)
def _get_st_model() -> SentenceTransformer:
    """Load SentenceTransformer once; shared by all dimension wrappers."""
    return SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
        trust_remote_code=True,
    )


@lru_cache(maxsize=1)
def get_embeddings_128d() -> TruncatedSentenceTransformerEmbeddings:
    return TruncatedSentenceTransformerEmbeddings(
        model=_get_st_model(),
        truncate_dim=128,
    )


@lru_cache(maxsize=1)
def get_embeddings_768d() -> TruncatedSentenceTransformerEmbeddings:
    return TruncatedSentenceTransformerEmbeddings(
        model=_get_st_model(),
        truncate_dim=None,
    )


# Alias for backward compatibility — SemanticChunker in ingest.py calls get_embeddings()
get_embeddings = get_embeddings_768d


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.CloudClient(
        api_key=os.environ["CHROMA_API_KEY"],
        tenant=os.environ["CHROMA_TENANT"],
        database=os.environ["CHROMA_DATABASE"],
    )


@lru_cache(maxsize=1)
def get_vectorstore_128d() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME_128D,
        embedding_function=get_embeddings_128d(),
        client=get_chroma_client(),
    )


@lru_cache(maxsize=1)
def get_vectorstore_768d() -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME_768D,
        embedding_function=get_embeddings_768d(),
        client=get_chroma_client(),
    )


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Local cross-encoder for reranking. Loaded once, CPU inference."""
    return CrossEncoder(RERANKER_MODEL)


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    return ChatGroq(
        model=LLM_MODEL,
        api_key=SecretStr(os.environ["GROQ_API_KEY"]),
        streaming=True,
    )
