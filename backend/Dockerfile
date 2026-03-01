FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN uv sync --frozen --no-dev


FROM python:3.13-slim

WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
