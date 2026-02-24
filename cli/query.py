import os

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import SecretStr
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a helpful assistant. Answer the user's question using only the provided context.
If the context does not contain enough information to answer, say so clearly.
Be concise and accurate."""


def get_chroma_client():
    return chromadb.CloudClient(
        api_key=os.environ["CHROMA_API_KEY"],
        tenant="f32850a7-db5b-4f37-8855-2129db742041",
        database="10k_store",
    )


def get_vectorstore(embeddings):
    client = get_chroma_client()
    return Chroma(
        collection_name="langchain_store",
        embedding_function=embeddings,
        client=client,
    )


def retrieve(vectorstore, query: str, k: int = 5):
    return vectorstore.similarity_search(query, k=k)


def generate(query: str, docs) -> str:
    context = "\n\n---\n\n".join(doc.page_content for doc in docs)

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=SecretStr(os.environ["GROQ_API_KEY"]),
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}"),
    ]

    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "\n".join(str(item) for item in content)
    return content


def rag_query(query: str, k: int = 5) -> str:
    embeddings = SentenceTransformerEmbeddings(
        model_name="rya23/modernbert-embed-finance-matryoshka",
        model_kwargs={"device": "cpu", "trust_remote_code": True},
    )
    vectorstore = get_vectorstore(embeddings)
    docs = retrieve(vectorstore, query, k=k)
    return generate(query, docs)
