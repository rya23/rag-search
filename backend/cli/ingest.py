from uuid import uuid4
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_experimental.text_splitter import SemanticChunker
from dotenv import load_dotenv
from backend.cli.preprocess_tables import format_table_compact, markdown_table_to_df
from database.dependencies import get_embeddings, get_vectorstore

load_dotenv()

BATCH_SIZE = 100
MAX_CHUNK_SIZE = 1000


def load_markdown(file_path: str):
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    return documents


def replace_tables_with_compact_format(
    text: str, filing_type: str = "10-K", unit: str | None = None
) -> str:

    lines = text.split("\n")
    result = []

    table_buffer = []
    current_section = "Unknown"
    table_counter = 0

    def flush_table():
        nonlocal table_buffer, table_counter

        if not table_buffer:
            return []

        table_md = "\n".join(table_buffer)

        # Parse markdown → DataFrame
        df = markdown_table_to_df(table_md)

        # Convert to compact format
        formatted = format_table_compact(
            df=df,
            section=current_section,
            filing_type=filing_type,
            unit=unit,
            table_id=table_counter,
        )

        table_counter += 1
        table_buffer = []

        return [formatted]

    for line in lines:
        # Track section headers
        if line.startswith("#"):
            # If we hit a header while inside table, flush first
            if table_buffer:
                result.extend(flush_table())
            current_section = line.lstrip("# ").strip()
            result.append(line)
            continue

        # Detect table lines
        if line.startswith("|"):
            table_buffer.append(line)
        else:
            if table_buffer:
                result.extend(flush_table())
            result.append(line)

    # Flush table at EOF
    if table_buffer:
        result.extend(flush_table())

    return "\n".join(result)


def split_markdown(documents):
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    md_docs = markdown_splitter.split_text(
        replace_tables_with_compact_format(documents[0].page_content)
    )

    # Further split large sections using semantic similarity
    text_splitter = SemanticChunker(
        embeddings=get_embeddings(),
    )

    semantic_docs = text_splitter.split_documents(md_docs)

    # Hard cap: break any oversized semantic chunks
    size_guard = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_SIZE,
        chunk_overlap=100,
    )
    final_docs = size_guard.split_documents(semantic_docs)

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
