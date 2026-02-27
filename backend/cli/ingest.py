from uuid import uuid4
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from ..database.dependencies import get_embeddings, get_vectorstore

load_dotenv()

BATCH_SIZE = 100


def load_markdown(file_path: str):
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    return documents


def split_markdown(documents):
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    md_docs = markdown_splitter.split_text(documents[0].page_content)

    # Further split large sections
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    final_docs = text_splitter.split_documents(md_docs)

    return final_docs


def build_vectorstore(docs):
    vectorstore = get_vectorstore()
    embeddings = get_embeddings()

    # Optional sanity check
    test_vector = embeddings.embed_query("test")
    print(f"Embedding dimension: {len(test_vector)}")

    # Batch insertion
    for i in range(0, len(docs), BATCH_SIZE):
        docs_batch = docs[i : i + BATCH_SIZE]
        ids_batch = [str(uuid4()) for _ in range(len(docs_batch))]

        vectorstore.add_documents(
            documents=docs_batch,
            ids=ids_batch,
        )

    return vectorstore


if __name__ == "__main__":
    file_path = "data/report.md"

    documents = load_markdown(file_path)
    split_docs = split_markdown(documents)
    vectorstore = build_vectorstore(split_docs)

    print(f"Indexed {len(split_docs)} chunks.")
