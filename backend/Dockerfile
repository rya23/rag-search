# ===============================
# Stage 1: Builder
# ===============================
FROM python:3.13-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install system dependencies needed for psycopg and Python builds
RUN apt-get update && apt-get install -y \
    python3-venv python3-dev build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install uv tool
RUN pip install uv --no-cache-dir

# Copy project metadata
COPY pyproject.toml uv.lock ./

# Create virtualenv
RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install CPU-only PyTorch first (forces CPU wheels)
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# Then install other Python dependencies via uv
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY . .

# Final sync of project dependencies
RUN uv sync --frozen --no-dev

# ===============================
# Stage 2: Runtime
# ===============================
FROM python:3.13-slim AS runtime

# Create non-root user
RUN groupadd -r -g 1001 appgroup && \
    useradd --no-create-home --uid 1001 --gid 1001 appuser

WORKDIR /app

# Install runtime libpq for psycopg
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Copy everything from builder
COPY --from=builder /app /app

# Ensure virtualenv binaries in PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set permissions and switch to non-root
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]