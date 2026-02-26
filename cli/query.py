from dotenv import load_dotenv
from .pipeline import RAGPipeline
from .retrievers import simple_retriever, multi_query_retriever
from .generators import groq_generator, groq_stream_generator
from db.dependencies import get_llm, get_vectorstore

load_dotenv()

RETRIEVER_MODES = ("simple", "multi")


def build_pipeline(mode: str = "simple", k: int = 5) -> RAGPipeline:
    """
    Build and return a RAGPipeline for the given retriever mode.

    mode: "simple"  - direct similarity search
          "multi"   - LLM-generated query variants + deduplicated results
    k:    number of docs to retrieve per query
    """
    if mode not in RETRIEVER_MODES:
        raise ValueError(
            f"Unknown retriever mode {mode!r}. Choose from: {RETRIEVER_MODES}"
        )

    llm = get_llm()
    vectorstore = get_vectorstore()

    pipeline = RAGPipeline()

    if mode == "simple":
        pipeline.set_retriever(simple_retriever(vectorstore, k=k))
    elif mode == "multi":
        pipeline.set_retriever(multi_query_retriever(vectorstore, llm, k=k))

    pipeline.set_generator(groq_generator(llm))
    pipeline.set_stream_generator(groq_stream_generator(llm))
    return pipeline


def rag_query(query: str, mode: str = "simple", k: int = 5) -> str:
    pipeline = build_pipeline(mode=mode, k=k)
    return pipeline.run(query)


def rag_query_stream(query: str, mode: str = "simple", k: int = 5):
    llm = get_llm()
    vectorstore = get_vectorstore()

    pipeline = RAGPipeline()

    if mode == "simple":
        pipeline.set_retriever(simple_retriever(vectorstore, k=k))
    elif mode == "multi":
        pipeline.set_retriever(multi_query_retriever(vectorstore, llm, k=k))

    pipeline.set_stream_generator(groq_stream_generator(llm))
    return pipeline.stream_run(query)
