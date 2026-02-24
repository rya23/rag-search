import argparse


def cmd_ingest(args):
    from cli.ingest import (
        load_markdown,
        split_markdown,
        create_embeddings,
        build_vectorstore,
    )

    print(f"Loading {args.file}...")
    documents = load_markdown(args.file)
    split_docs = split_markdown(documents)
    print(f"Split into {len(split_docs)} chunks. Embedding and uploading...")
    embeddings = create_embeddings()
    build_vectorstore(split_docs, embeddings)
    print(f"Done. Indexed {len(split_docs)} chunks.")


def cmd_query(args):
    from cli.query import build_pipeline

    print(f"Initializing pipeline (retriever={args.retriever}, k={args.k})...")
    pipeline = build_pipeline(mode=args.retriever, k=args.k)

    if args.question:
        answer = pipeline.run(args.question)
        print(answer)
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
            answer = pipeline.run(question)
            print(f"Assistant: {answer}\n")


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
        "-q", "--question",
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
        "--retriever",
        choices=["simple", "multi"],
        default="simple",
        help=(
            "Retrieval strategy. "
            "'simple' = direct similarity search. "
            "'multi'  = LLM generates query variants, results are deduplicated. "
            "(default: simple)"
        ),
    )

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)


if __name__ == "__main__":
    main()
