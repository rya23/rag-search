# RAG Search - LangGraph Pipeline

A production-ready RAG (Retrieval-Augmented Generation) pipeline with intelligent query routing, powered by LangGraph.

## Features

### 🧠 Intelligent Query Routing
- **Automatic complexity detection**: Queries are automatically analyzed and routed to the best retrieval strategy
- **Simple queries**: Direct similarity search for straightforward questions
- **Complex queries**: Multi-query retrieval with LLM-generated variants for analytical questions

### 💾 State Persistence
- **PostgreSQL checkpointing**: Full state saved at each node for debugging and resumption
- **Conversation threads**: Multi-turn conversations with context retention
- **Time-travel debugging**: Inspect pipeline state at any node

### 📊 Observability
- **Detailed tracing**: Track every step of query processing
- **Multi-query analytics**: See generated query variants and per-query results
- **Performance metrics**: Retrieval time, generation time, and total latency

### 🔄 Streaming Support
- **Token streaming**: Real-time answer generation
- **Progress updates**: Node-level execution updates
- **Enhanced UX**: Users see pipeline progress in real-time

## Architecture

```
┌──────────────────────────────────────────────┐
│         LangGraph RAG Pipeline               │
├──────────────────────────────────────────────┤
│                                              │
│  START → Analyze Query                      │
│              │                               │
│         (Rule-based)                         │
│              │                               │
│         ┌────┴────┐                          │
│    [Simple]  [Complex]                       │
│         │         │                          │
│    Simple    Multi-Query                     │
│    Retrieval  Retrieval                      │
│         │         │                          │
│         └────┬────┘                          │
│              │                               │
│         [Merge & Dedupe]                     │
│              │                               │
│         Generate Answer                      │
│         (streaming)                          │
│              │                               │
│            END                               │
│                                              │
└──────────────────────────────────────────────┘
```

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd rag-search

# Install dependencies using uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Required Environment Variables

```bash
# Database (PostgreSQL)
user=your_db_user
password=your_db_password
host=localhost
PORT=5432
dbname=your_db_name

# LLM API Keys
GROQ_API_KEY=your_groq_key

# Vector Store
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

## Usage

### 1. Ingest Documents

```bash
# Activate virtual environment
source .venv/bin/activate

# Ingest a markdown file
python main.py ingest path/to/document.md
```

This will:
- Extract tables from the document
- Split text into chunks
- Embed and store in ChromaDB

### 2. Query the Pipeline

#### Simple Query
```bash
python main.py query -q "What was Apple's revenue in 2023?"
```

#### Interactive Mode
```bash
python main.py query

# You'll see:
RAG query mode. Type 'exit' or Ctrl-C to quit.

You: What was Apple's revenue in 2023?
Assistant: [streaming answer]

You: exit
```

#### Conversation Mode (Multi-turn)
```bash
python main.py query --conversation

# The pipeline will maintain context across questions:
You: What was Apple's revenue in 2023?
Assistant: Apple's revenue in 2023 was...

You: How about Microsoft?  # Uses context from previous question
Assistant: Microsoft's revenue in 2023 was...
```

#### Query with Custom k
```bash
python main.py query -k 10  # Retrieve 10 documents instead of 5
```

### 3. Start Observability API

```bash
python main.py serve

# API will be available at http://localhost:8000
```

#### API Endpoints

- `POST /api/query` - Query with streaming response (automatic routing)
  ```json
  {
    "query": "What was Apple's revenue?",
    "k": 5,
    "thread_id": "optional-for-conversation-continuity"
  }
  ```
  
  Response: Server-Sent Events (SSE) stream
  ```
  data: {"type": "trace_id", "data": "uuid"}
  data: {"type": "thread_id", "data": "uuid"}
  data: {"type": "node", "data": "analyze_query"}
  data: {"type": "node", "data": "simple_retrieve"}
  data: {"type": "node", "data": "generate_answer"}
  data: {"type": "token", "data": "..."}
  data: {"type": "done"}
  ```

- `POST /api/conversation` - Multi-turn conversation with state persistence
  ```json
  {
    "query": "Tell me more about that",
    "thread_id": "uuid-from-previous-response",
    "k": 5
  }
  ```

- `GET /api/traces?limit=50` - List recent traces
- `GET /api/traces/{trace_id}` - Get full trace details
- `GET /api/traces/{trace_id}/docs` - Get retrieved documents
- `GET /api/traces/{trace_id}/multiquery` - Get multi-query steps (legacy)

## How Query Routing Works

The pipeline automatically analyzes your query and chooses the best retrieval strategy:

### Simple Queries → Direct Similarity Search
- "What is revenue?"
- "Define EBITDA"
- "List Apple products"

### Complex Queries → Multi-Query Retrieval
Detected by keywords like:
- `compare`, `analyze`, `trend`, `over time`
- `versus`, `difference between`, `why did`
- `breakdown`, `detailed analysis`, `impact of`

Or by query length (>15 words)

Examples:
- "Compare the revenue trends between Apple and Microsoft over the last 5 years"
- "Analyze the impact of cloud strategies on profitability"

## Advanced Usage

### Programmatic API

```python
import asyncio
from cli.langgraph_pipeline import run_query, stream_query

# Simple query
async def main():
    answer = await run_query(
        query="What was Apple's revenue in 2023?",
        k=5,
        thread_id=None,  # Or provide a thread_id for conversation
        with_checkpointing=True
    )
    print(answer)

asyncio.run(main())
```

### Streaming with Progress Updates

```python
import asyncio
from cli.langgraph_pipeline import stream_query_with_tokens

async def main():
    async for event in stream_query_with_tokens(
        query="Compare Apple and Microsoft",
        k=5
    ):
        if event["type"] == "progress":
            print(f"\r{event['message']}", end="", flush=True)
        elif event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "complete":
            print("\n\nComplete!")

asyncio.run(main())
```

## File Structure

```
rag-search/
├── cli/
│   ├── langgraph/              # LangGraph implementation
│   │   ├── state.py           # RAGState TypedDict schema
│   │   ├── nodes.py           # Node implementations
│   │   ├── routing.py         # Conditional routing logic
│   │   ├── graph.py           # StateGraph construction
│   │   └── checkpointer.py    # PostgreSQL persistence
│   ├── langgraph_pipeline.py  # Main pipeline entry point
│   ├── pipeline.py            # LangGraph-backed RAGPipeline class
│   ├── pipeline_legacy.py     # Legacy linear pipeline (backup)
│   ├── retrievers.py          # Retriever implementations
│   ├── generators.py          # Generator implementations
│   ├── query.py               # Query interface
│   └── ingest.py              # Document ingestion
├── api/
│   └── server.py              # FastAPI observability server
├── observability/
│   └── tracer.py              # PostgreSQL trace storage (SQLAlchemy ORM)
├── db/
│   ├── vector_db.py           # ChromaDB setup
│   └── dependencies.py        # Shared dependencies
├── main.py                    # CLI entry point
└── test_langgraph.py          # Structure tests
```

## Testing

```bash
# Run structure tests (no DB required)
source .venv/bin/activate
python test_langgraph.py

# Expected output:
✓ ALL TESTS PASSED!
```

## Migration from Legacy Pipeline

The new LangGraph pipeline is **backward compatible**. Existing code will continue to work:

```python
from cli.query import build_pipeline

# Old code still works
pipeline = build_pipeline(mode="simple", k=5)  # mode is now ignored
answer = pipeline.run("What was Apple's revenue?")

# Pipeline automatically routes based on query analysis
```

The `mode` parameter is now **deprecated** but kept for compatibility. The pipeline will automatically determine the best retrieval strategy.

## Advantages Over Legacy Pipeline

| Feature | Legacy | LangGraph |
|---------|--------|-----------|
| Query Routing | Manual (`mode="simple"` or `"multi"`) | Automatic based on analysis |
| State Management | None | PostgreSQL checkpointing |
| Conversations | Not supported | Full multi-turn support |
| Observability | Basic | Complete state tracking |
| Debugging | Limited | Time-travel debugging |
| Extensibility | Linear only | Graph-based with branches |
| Error Handling | Basic | Checkpointing & resumption |

## Roadmap

Future enhancements (v2):

- [ ] **LLM-based query analysis** (currently rule-based)
- [ ] **Self-correction** with answer quality evaluation
- [ ] **Parallel retrieval** from multiple sources (vector DB + BM25 + web search)
- [ ] **Agentic RAG** with tool use and self-refinement
- [ ] **Graph visualization** export for debugging
- [ ] **Reranking step** with cross-encoder models

## Troubleshooting

### Database Connection Errors

Ensure your `.env` file has correct credentials:
```bash
user=your_db_user
password=your_db_password
host=localhost
PORT=5432
dbname=your_db_name
```

### Import Errors

Always activate the virtual environment:
```bash
source .venv/bin/activate
```

### Checkpoint Tables Not Found

The checkpointer automatically creates tables on first run. If you see errors, try:
```python
from cli.langgraph.checkpointer import get_checkpointer
import asyncio

async def setup():
    checkpointer = await get_checkpointer()
    await checkpointer.setup()

asyncio.run(setup())
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Uses [LangChain](https://github.com/langchain-ai/langchain) components
- ChromaDB for vector storage
- PostgreSQL for state persistence and observability
