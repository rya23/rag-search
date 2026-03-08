import argparse

from dataclasses import dataclass
from typing import Optional


@dataclass
class IngestArgs:
    file: str


@dataclass
class QueryArgs:
    question: Optional[str]
    k: int
    conversation: bool


@dataclass
class ServeArgs:
    host: str
    port: int
    reload: bool


def cmd_ingest(args: IngestArgs):
    from cli.preprocess_tables import run_extraction
    from cli.ingest import (
        load_markdown,
        split_markdown,
        build_vectorstores,
    )

    print(f"Extracting tables from {args.file}...")
    # table_docs = run_extraction(args.file)

    print(f"Loading {args.file}...")
    documents = load_markdown(args.file)
    split_docs = split_markdown(documents)
    all_docs = split_docs
    print(
        f"Split into {len(split_docs)} text chunks. Embedding and uploading to 128d + 768d collections..."
    )
    build_vectorstores(all_docs)
    print(f"Done. Indexed {len(all_docs)} total chunks into both collections.")


def cmd_query(args: QueryArgs):
    from cli.query import build_pipeline
    from cli.langgraph_pipeline import generate_thread_id

    thread_id = generate_thread_id() if args.conversation else None

    if thread_id:
        print(f"Starting conversation (thread: {thread_id[:8]}...)")
        print("Note: Follow-up questions will use conversation context.\n")

    print(f"Initializing LangGraph pipeline (auto-routing, k={args.k})...")
    pipeline = build_pipeline(k=args.k, with_checkpointing=args.conversation)

    if thread_id:
        pipeline.set_thread_id(thread_id)

    if args.question:
        print("Assistant: ", end="", flush=True)
        for chunk in pipeline.stream_run(args.question):
            print(chunk, end="", flush=True)
        print()
    else:
        print("RAG query mode. Type 'exit' or Ctrl-C to quit.\n")
        while True:
            try:
                question = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if not question:
                continue
            if question.lower() in ("exit", "quit"):
                break
            print("Assistant: ", end="", flush=True)
            for chunk in pipeline.stream_run(question):
                print(chunk, end="", flush=True)
            print("\n")


def cmd_serve(args: ServeArgs):
    import uvicorn

    print(f"Starting observability API on http://{args.host}:{args.port}")
    uvicorn.run("api.server:app", host=args.host, port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(
        prog="rag",
        description="RAG pipeline: ingest documents and query them with an LLM.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ingest subcommand
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a markdown file into the vector store."
    )
    ingest_parser.add_argument("file", help="Path to the markdown file to ingest.")

    # query subcommand
    query_parser = subparsers.add_parser("query", help="Query the RAG pipeline.")
    query_parser.add_argument(
        "-q",
        "--question",
        help="Single question to ask. If omitted, starts an interactive loop.",
        default=None,
    )
    query_parser.add_argument(
        "-k",
        help="Number of chunks to retrieve per query (default: 5).",
        type=int,
        default=5,
    )
    query_parser.add_argument(
        "--conversation",
        action="store_true",
        help="Enable multi-turn conversation mode with context retention.",
    )

    # serve subcommand
    serve_parser = subparsers.add_parser(
        "serve", help="Start the observability API server."
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)"
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Bind port (default: 8000)"
    )
    serve_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development."
    )

    args = parser.parse_args()
    # ns = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(IngestArgs(file=args.file))
    elif args.command == "query":
        cmd_query(
            QueryArgs(question=args.question, k=args.k, conversation=args.conversation)
        )
    elif args.command == "serve":
        cmd_serve(ServeArgs(host=args.host, port=args.port, reload=args.reload))


if __name__ == "__main__":
    main()
