# RAG Search - Monorepo

A production-ready RAG (Retrieval-Augmented Generation) application with intelligent query routing, powered by LangGraph and FastAPI backend with a modern Next.js frontend.

## 🏗️ Monorepo Structure

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

## ✨ Features

### Backend
- **🧠 Intelligent Query Routing**: Automatic analysis and routing to simple or multi-query retrieval
- **💾 State Persistence**: PostgreSQL checkpointing for conversation threads
- **📊 Observability**: Complete trace storage with performance metrics
- **🔄 SSE Streaming**: Real-time token streaming with node execution updates

### Frontend
- **💬 Chat Interface**: Real-time streaming chat with markdown support
- **🎨 Dark Theme**: Beautiful UI with shadcn/ui components
- **📈 Trace Viewer**: View all queries with performance metrics
- **🔍 Document Inspector**: See retrieved documents and metadata
- **⚡ SSE Integration**: Native Server-Sent Events handling

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** with `uv` package manager
- **Bun 1.2+** for frontend
- **PostgreSQL** for trace storage and checkpointing
- **ChromaDB** for vector storage

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

### 4. Ingest Documents (First Time)

```bash
cd backend
source .venv/bin/activate
python main.py ingest path/to/your/document.md
```

## 📖 Usage

### Chat Interface

1. Open `http://localhost:3000`
2. Type your question in the input box
3. Watch real-time streaming responses
4. Adjust `k` parameter to retrieve more/fewer documents

### View Traces

1. Click "View Traces" in the top right
2. See all queries with performance metrics
3. Click any trace to see:
   - Full query and response
   - Retrieved documents
   - Timing breakdown (retrieval, generation, total)
   - Node execution flow

### Conversation Mode

The application automatically maintains conversation context using thread IDs. Each chat session is a separate thread, allowing follow-up questions.

## 🔧 API Endpoints

### Backend (FastAPI)

- `POST /api/query` - Stream query with SSE
  ```json
  {
    "query": "What was Apple's revenue?",
    "k": 5,
    "thread_id": "optional-uuid"
  }
  ```

- `GET /api/traces?limit=50` - List recent traces
- `GET /api/traces/{trace_id}` - Get trace details
- `GET /api/traces/{trace_id}/docs` - Get retrieved documents

## 🎨 Frontend Technology Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) |
| UI Components | shadcn/ui |
| Styling | Tailwind CSS v4 |
| State Management | TanStack Query (React Query) |
| SSE Handling | Custom hook with native fetch |
| Icons | Lucide React |
| Markdown | react-markdown |

## 📦 Project Scripts

### Root
```bash
bun dev          # Start frontend dev server
bun build        # Build frontend for production
```

### Backend
```bash
python main.py ingest <file>        # Ingest documents
python main.py query                # Interactive query mode
python main.py query --conversation # Conversation mode
python main.py serve                # Start API server
```

### Frontend
```bash
bun dev          # Start dev server
bun build        # Production build
bun start        # Start production server
bun lint         # Run ESLint
```

## 🏛️ Architecture

### Query Flow

```
User Input → Frontend (Next.js)
             ↓ SSE Connection
Backend (FastAPI) → LangGraph Pipeline
                    ↓
             Analyze Query
                    ↓
        ┌──────────┴──────────┐
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

### SSE Event Types

```typescript
{ type: "trace_id", data: "uuid" }      // Trace identifier
{ type: "thread_id", data: "uuid" }     // Thread identifier
{ type: "node", data: "node_name" }     // LangGraph node execution
{ type: "token", data: "text" }         // Streaming token
{ type: "error", data: "message" }      // Error message
{ type: "done" }                        // Stream complete
```

## 🔍 How Query Routing Works

### Simple Queries → Direct Retrieval
- Short, straightforward questions
- Factual lookups
- Examples: "What is revenue?", "Define EBITDA"

### Complex Queries → Multi-Query Retrieval
Detected by:
- Keywords: `compare`, `analyze`, `trend`, `versus`, `why`
- Query length > 15 words
- Examples: "Compare Apple and Microsoft revenue trends"

## 🛠️ Development Tips

### Hot Reload
Both backend (`--reload`) and frontend (Next.js) support hot reload during development.

### Debugging
- Backend logs: Console output from FastAPI
- Frontend: Browser DevTools → Network → EventStream
- Traces: View in `/traces` page

### Adding New Components
```bash
cd frontend
bunx shadcn@latest add <component-name>
```

## 📊 Database Schema

### Traces Table
- `trace_id`: UUID primary key
- `query`: Text query
- `response`: Generated answer
- `k`: Number of documents retrieved
- `status`: pending | completed | failed
- `retriever_ms`, `generator_ms`, `total_ms`: Timing metrics
- `created_at`: Timestamp

### Documents Table
- Links retrieved documents to traces
- Stores content, metadata, and relevance scores

## 🚢 Production Deployment

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

Or deploy to Vercel:
```bash
vercel --prod
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both frontend and backend
5. Submit a pull request

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- **LangGraph** - Graph-based LLM workflows
- **LangChain** - RAG components
- **FastAPI** - Modern Python web framework
- **Next.js** - React framework
- **shadcn/ui** - Beautiful UI components
- **ChromaDB** - Vector database
- **PostgreSQL** - Trace storage and checkpointing

---

**Built with ❤️ using Python, TypeScript, and Bun**
