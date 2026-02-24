import os

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_groq import ChatGroq
from pydantic import SecretStr
from dotenv import load_dotenv

from .pipeline import RAGPipeline
from .retrievers import simple_retriever, multi_query_retriever
from .generators import groq_generator

load_dotenv()

RETRIEVER_MODES = ("simple", "multi")


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=SecretStr(os.environ["GROQ_API_KEY"]),
    )


def get_vectorstore():
    embeddings = SentenceTransformerEmbeddings(
        model_name="rya23/modernbert-embed-finance-matryoshka",
        model_kwargs={"device": "cpu", "trust_remote_code": True},
    )
    client = chromadb.CloudClient(
        api_key=os.environ["CHROMA_API_KEY"],
        tenant="f32850a7-db5b-4f37-8855-2129db742041",
        database="10k_store",
    )
    return Chroma(
        collection_name="langchain_store",
        embedding_function=embeddings,
        client=client,
    )


def build_pipeline(mode: str = "simple", k: int = 5) -> RAGPipeline:
    """
    Build and return a RAGPipeline for the given retriever mode.

    mode: "simple"  - direct similarity search
          "multi"   - LLM-generated query variants + deduplicated results
    k:    number of docs to retrieve per query
    """
    if mode not in RETRIEVER_MODES:
        raise ValueError(f"Unknown retriever mode {mode!r}. Choose from: {RETRIEVER_MODES}")

    llm = get_llm()
    vectorstore = get_vectorstore()

    pipeline = RAGPipeline()

    if mode == "simple":
        pipeline.set_retriever(simple_retriever(vectorstore, k=k))
    elif mode == "multi":
        pipeline.set_retriever(multi_query_retriever(vectorstore, llm, k=k))

    pipeline.set_generator(groq_generator(llm))
    return pipeline


def rag_query(query: str, mode: str = "simple", k: int = 5) -> str:
    pipeline = build_pipeline(mode=mode, k=k)
    return pipeline.run(query)
