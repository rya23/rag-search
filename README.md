# RAG Search - Advanced RAG System with Fine-Tuned Embeddings

A production-grade RAG (Retrieval-Augmented Generation) system featuring a **fine-tuned embedding model** trained on financial data, intelligent query routing via LangGraph, and comprehensive observability. Achieves significant performance improvements over base models through Matryoshka representation learning.

![website_demo](public/demo.gif)

## 🎯 Key ML Features

### Fine-Tuned Embedding Model

- **Base Model**: `nomic-ai/modernbert-embed-base`
- **Fine-Tuned Model (Hugging Face)**: [rya23/modernbert-embed-finance-matryoshka](https://huggingface.co/rya23/modernbert-embed-finance-matryoshka)
- **Training Dataset**: [philschmid/financial-rag-embedding-dataset](https://huggingface.co/datasets/philschmid/finanical-rag-embedding-dataset) (~10k financial Q&A pairs)
- **Architecture**: Matryoshka Representation Learning with Multiple Negatives Ranking Loss
- **Output Dimensions**: [768, 512, 256, 128, 64] - flexible embedding sizes for different use cases

### Performance Improvements

Fine-tuning on domain-specific financial data achieved substantial gains across all metrics:

| Metric      | Dimension | Base Model | Fine-Tuned | Improvement |
| ----------- | --------- | ---------- | ---------- | ----------- |
| **NDCG@10** | 128d      | ~0.85      | ~0.95      | **+11.8%**  |
| **MRR@10**  | 128d      | ~0.83      | ~0.94      | **+13.3%**  |
| **MAP@100** | 128d      | ~0.84      | ~0.94      | **+11.9%**  |
| Accuracy@1  | 128d      | ~0.81      | ~0.92      | **+13.6%**  |

_Performance varies across embedding dimensions. See [notebooks](backend/notebooks/finetuning_embeddding_models.ipynb) for full evaluation._

### Training Configuration

```python
# Matryoshka Loss with MNRL
base_loss = MultipleNegativesRankingLoss(model=model)
train_loss = MatryoshkaLoss(
    model=model,
    loss=base_loss,
    matryoshka_dims=[768, 512, 256, 128, 64]
)

# Training: 4 epochs, global batch size 384
# Optimizer: AdamW with cosine LR scheduler (2e-5)
# Evaluated on NDCG@10 with 128d embeddings
```

### Intelligent Query Routing (LangGraph)

- **Query Analysis**: Automatic classification of query complexity
- **Adaptive Retrieval**: Routes to simple vs multi-query retrieval pipelines
- **Conversational Context**: Maintains thread-based conversation history
- **Streaming Generation**: Real-time token streaming with node execution updates

## Monorepo Structure

```
rag-search/
├── backend/              # Python FastAPI + LangGraph
│   ├── api/             # FastAPI server & endpoints
│   ├── cli/             # RAG pipeline & LangGraph logic
│   ├── db/              # Database & vector store
│   ├── observability/   # Trace storage & monitoring
│   └── main.py          # CLI entry point
├── frontend/            # Next.js + React + TypeScript
│   ├── app/            # Next.js 13+ App Router
│   ├── components/     # React components (shadcn/ui)
│   ├── lib/            # API client & utilities
│   └── hooks/          # Custom React hooks (SSE)
└── package.json        # Bun workspace config
```

## System Architecture

### ML Pipeline

1. **Document Ingestion**
    - Chunking strategy optimized for financial documents
    - Embedding generation using fine-tuned ModernBERT
    - ChromaDB vector storage with cosine similarity

2. **Query Processing**
    - Query embedding with fine-tuned model (128d optimized)
    - LangGraph-based routing: Simple vs Complex queries
    - Multi-query generation for complex information needs

3. **Retrieval & Generation**
    - Top-k similarity search with configurable k
    - Context-aware generation with conversation history
    - Groq LLM for fast inference

### Observability & Monitoring

- **Trace Storage**: PostgreSQL-backed complete query traces
- **Performance Metrics**: Retrieval time, generation time, total latency
- **Node Execution Tracking**: Full LangGraph pipeline visibility
- **Document Inspector**: Retrieved chunks with similarity scores

### Frontend Interface

- Real-time streaming chat with markdown rendering
- Trace viewer with performance analytics
- Document inspection and metadata display

## Quick Start

### Prerequisites

- **Python 3.13+** with `uv` package manager
- **Bun 1.2+** for frontend
- **PostgreSQL** for trace storage and checkpointing
- **ChromaDB** for vector storage
- **Docker + Docker Compose** (optional, for containerized deployment)

### 1. Install Dependencies

#### Backend

```bash
cd backend
uv sync
```

#### Frontend

```bash
cd frontend
bun install
```

### 2. Configure Environment

Create `.env` in the root directory:

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
CHROMA_PERSIST_DIRECTORY=./backend/data/chroma
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start the Application

#### Terminal 1: Backend API

```bash
cd backend
source .venv/bin/activate
python main.py serve --reload
```

Backend will run on `http://localhost:8000`

#### Terminal 2: Frontend

```bash
cd frontend
bun dev
```

Frontend will run on `http://localhost:3000`

### Dockerized Run (Recommended)

This application is fully dockerized with `Dockerfile`s and `docker-compose.yml`.

```bash
docker compose up --build
```

This starts the stack in containers with a single command.

### 4. Ingest Documents (First Time)

```bash
cd backend
source .venv/bin/activate
python main.py ingest path/to/your/document.md
```

## ML Model Training & Evaluation

### Fine-Tuning Your Own Embedding Model

The fine-tuned embedding model is available at [rya23/modernbert-embed-finance-matryoshka](https://huggingface.co/rya23/modernbert-embed-finance-matryoshka). To train your own:

1. **Prepare Your Dataset**

    ```python
    # Dataset format: anchor (query), positive (context), id
    dataset = load_dataset("your-dataset")
    dataset = dataset.rename_column("question", "anchor")
    dataset = dataset.rename_column("context", "positive")
    ```

2. **Configure Training**

    ```bash
    cd backend/notebooks
    # Edit finetuning_embeddding_models.ipynb
    # Adjust: dataset, model_id, matryoshka_dims, training args
    ```

3. **Train & Evaluate**
    - Training uses MultipleNegativesRankingLoss wrapped in MatryoshkaLoss
    - Evaluation is performed across Matryoshka dimensions `[768, 512, 256, 128, 64]`
    - Primary optimization target: `NDCG@10` at `128d`

## Evaluation Metrics

### Information Retrieval Metrics

The system evaluates embedding quality using:

- **NDCG@10** (Normalized Discounted Cumulative Gain): Primary optimization target
- **MRR@10** (Mean Reciprocal Rank): First relevant result position
- **MAP@100** (Mean Average Precision): Overall precision across results
- **Accuracy@k**: Exact match in top-k results
- **Precision@k**: Relevant results ratio in top-k
- **Recall@k**: Coverage of all relevant results

### Comparative Analysis

```python
# From evaluation notebook
metrics = ['ndcg@10', 'mrr@10', 'map@100', 'accuracy@1']
dims = [768, 512, 256, 128, 64]

# Base vs Fine-Tuned comparison shows:
# - Consistent improvements across all dimensions
# - 128d dimension offers best latency/quality tradeoff
# - Minimal quality degradation even at 64d
```

## API Endpoints

### Backend (FastAPI)

- `POST /api/query` - Stream query with SSE

    ```json
    {
        "query": "What was AMD's revenue?",
        "k": 5,
        "thread_id": "optional-uuid"
    }
    ```

- `GET /api/traces?limit=50` - List recent traces
- `GET /api/traces/{trace_id}` - Get trace details
- `GET /api/traces/{trace_id}/docs` - Get retrieved documents

## Technology Stack

### ML & Backend

| Component          | Technology              |
| ------------------ | ----------------------- |
| Embedding Model    | ModernBERT (fine-tuned) |
| Training Framework | Sentence Transformers   |
| Loss Function      | Matryoshka + MNRL       |
| Vector Store       | ChromaDB                |
| LLM                | Groq (Llama 3.1)        |
| Orchestration      | LangGraph               |
| API Framework      | FastAPI                 |
| Database           | PostgreSQL              |

### Frontend

| Layer            | Technology                    |
| ---------------- | ----------------------------- |
| Framework        | Next.js 15 (App Router)       |
| UI Components    | shadcn/ui                     |
| Styling          | Tailwind CSS v4               |
| State Management | TanStack Query                |
| SSE Handling     | Custom hook with native fetch |
| Markdown         | react-markdown                |

## Project Scripts

### Root

```bash
bun dev          # Start frontend dev server
bun build        # Build frontend for production
```

### Backend

```bash
python main.py ingest <file>        # Ingest documents with fine-tuned embeddings
python main.py query                # Interactive query mode
python main.py query --conversation # Conversation mode with context
python main.py serve                # Start API server with streaming
```

### ML Notebooks

```bash
cd backend/notebooks
jupyter notebook finetuning_embeddding_models.ipynb
# - Train custom embedding models
# - Evaluate on your dataset
# - Compare base vs fine-tuned performance
```

### Frontend

```bash
bun dev          # Start dev server
bun build        # Production build
bun start        # Start production server
bun lint         # Run ESLint
```

## Architecture

### Query Flow

```
User Input → Frontend (Next.js)
             ↓ SSE Connection
Backend (FastAPI) → LangGraph Pipeline
                    ↓
             Analyze Query
                    ↓
        ┌───────────┴──────────┐
   [Simple]              [Complex]
        ↓                     ↓
  Simple Retrieval    Multi-Query Retrieval
        └──────────┬──────────┘
                   ↓
            Generate Answer
                   ↓
        Stream Tokens via SSE
                   ↓
    Frontend Updates UI Real-time
```

## 🚀 Production Deployment

### Docker Compose

```bash
docker compose up --build
```

Run this from the repository root to start the dockerized application.

### Backend

```bash
cd backend
uv sync --no-dev
gunicorn api.server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend

```bash
cd frontend
bun run build
bun start
```

## Performance Considerations

### Embedding Dimension Selection

- **768d**: Highest accuracy, ~2x slower than 128d
- **512d**: Balanced, good for moderate-scale deployments
- **256d**: Fast with minimal accuracy loss
- **128d**: **Recommended** - optimal speed/accuracy tradeoff
- **64d**: Ultra-fast, suitable for initial filtering in cascade retrieval

### Optimization Strategies

1. **Matryoshka Embeddings**: Single model deployment, runtime dimension switching
2. **Batch Retrieval**: Process multiple queries in parallel
3. **Caching**: Store embeddings for frequently accessed documents
4. **Quantization**: Further reduce memory footprint (future work)

## References & Resources

- **Notebook**: [Fine-tuning Embedding Models](backend/notebooks/finetuning_embeddding_models.ipynb)
- **Dataset**: [Financial RAG Dataset](https://huggingface.co/datasets/philschmid/finanical-rag-embedding-dataset)
- **Fine-Tuned Model**: [rya23/modernbert-embed-finance-matryoshka](https://huggingface.co/rya23/modernbert-embed-finance-matryoshka)
- **Base Model**: `nomic-ai/modernbert-embed-base`
- **Framework**: [Sentence Transformers](https://www.sbert.net/)
- **Matryoshka Loss**: [Paper](https://arxiv.org/abs/2205.13147)

## Contributing

Contributions welcome! Areas of interest:

- Additional domain-specific fine-tuning datasets
- Alternative embedding architectures
- Improved query routing strategies
- Performance benchmarking tools
