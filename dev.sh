#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  RAG Search - Development Startup   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ] && [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found!${NC}"
    echo "Please create a .env file with your configuration."
    echo "See README.md for required environment variables."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "backend/.venv" ]; then
    echo -e "${YELLOW}⚠️  Python virtual environment not found!${NC}"
    echo "Run: cd backend && uv sync"
    echo ""
fi

echo -e "${GREEN}Starting services...${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"

    # Prevent recursive trap invocation while shutting down.
    trap - SIGINT SIGTERM

    # Stop only child background jobs started by this script.
    JOB_PIDS=$(jobs -p)
    if [ -n "$JOB_PIDS" ]; then
        kill $JOB_PIDS 2>/dev/null
        wait $JOB_PIDS 2>/dev/null
    fi

    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend in background
echo -e "${BLUE}[Backend]${NC} Starting FastAPI server on http://localhost:8000"
cd backend && source .venv/bin/activate && python main.py serve --reload 2>&1 | sed 's/^/[Backend] /' &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend in background
echo -e "${BLUE}[Frontend]${NC} Starting Next.js dev server on http://localhost:3000"
cd frontend && bun dev 2>&1 | sed 's/^/[Frontend] /' &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✓ Services started!${NC}"
echo ""
echo -e "  Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "  Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for all background processes
wait
