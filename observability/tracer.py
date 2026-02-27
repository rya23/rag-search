import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import psycopg2
import psycopg2.pool
from langchain_core.documents import Document


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rag_traces (
    trace_id    UUID        PRIMARY KEY,
    query       TEXT        NOT NULL,
    retriever_mode VARCHAR(20) NOT NULL,
    k           INTEGER     NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    response    TEXT,
    retriever_ms INTEGER,
    generator_ms INTEGER,
    total_ms    INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS rag_trace_docs (
    id          SERIAL      PRIMARY KEY,
    trace_id    UUID        NOT NULL REFERENCES rag_traces(trace_id) ON DELETE CASCADE,
    position    INTEGER     NOT NULL,
    content     TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Multi-query: the prompt sent to the LLM and the queries it generated
CREATE TABLE IF NOT EXISTS rag_multiquery_steps (
    id                  SERIAL      PRIMARY KEY,
    trace_id            UUID        NOT NULL REFERENCES rag_traces(trace_id) ON DELETE CASCADE,
    prompt_sent         TEXT        NOT NULL,
    generated_queries   TEXT[]      NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Multi-query: docs retrieved for each generated query (before dedup)
CREATE TABLE IF NOT EXISTS rag_multiquery_docs (
    id              SERIAL      PRIMARY KEY,
    trace_id        UUID        NOT NULL REFERENCES rag_traces(trace_id) ON DELETE CASCADE,
    query_index     INTEGER     NOT NULL,
    generated_query TEXT        NOT NULL,
    position        INTEGER     NOT NULL,
    content         TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_rag_trace_docs_trace_id    ON rag_trace_docs(trace_id);
CREATE INDEX IF NOT EXISTS idx_rag_traces_created_at      ON rag_traces(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rag_multiquery_docs_trace  ON rag_multiquery_docs(trace_id);
"""


@dataclass
class DocRecord:
    position: int
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceDetail:
    trace_id: str
    query: str
    retriever_mode: str
    k: int
    status: str
    response: str | None
    retriever_ms: int | None
    generator_ms: int | None
    total_ms: int | None
    created_at: datetime
    completed_at: datetime | None
    docs: list[DocRecord] = field(default_factory=list)


class TraceStore:
    def __init__(self):
        USER = os.getenv("user")
        PASSWORD = os.getenv("password")
        HOST = os.getenv("host")
        PORT = os.getenv("PORT", "5432")
        DBNAME = os.getenv("dbname")

        missing = [
            name
            for name, value in {
                "user": USER,
                "password": PASSWORD,
                "host": HOST,
                "port": PORT,
                "dbname": DBNAME,
            }.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                f"Missing required database environment variables: {', '.join(missing)}"
            )

        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=int(PORT),
                database=DBNAME,
            )
        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to initialize connection pool: {e}") from e

        self._ensure_schema()

    def _conn(self):
        return self._pool.getconn()

    def _release(self, conn):
        self._pool.putconn(conn)

    def _ensure_schema(self):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA_SQL)
            conn.commit()
        finally:
            self._release(conn)

    def create_trace(
        self, trace_id: str, query: str, mode: str, k: int, created_at: float
    ):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_traces (trace_id, query, retriever_mode, k, status, created_at)
                    VALUES (%s, %s, %s, %s, 'in_progress', to_timestamp(%s))
                    """,
                    (trace_id, query, mode, k, created_at),
                )
            conn.commit()
        finally:
            self._release(conn)

    def save_docs(self, trace_id: str, docs: list[Document], retriever_ms: int):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                for i, doc in enumerate(docs):
                    cur.execute(
                        """
                        INSERT INTO rag_trace_docs (trace_id, position, content, metadata)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (trace_id, i, doc.page_content, json.dumps(doc.metadata)),
                    )
                cur.execute(
                    "UPDATE rag_traces SET retriever_ms = %s WHERE trace_id = %s",
                    (retriever_ms, trace_id),
                )
            conn.commit()
        finally:
            self._release(conn)

    def complete_trace(
        self,
        trace_id: str,
        response: str,
        generator_ms: int,
        total_ms: int,
    ):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE rag_traces
                    SET status = 'complete',
                        response = %s,
                        generator_ms = %s,
                        total_ms = %s,
                        completed_at = NOW()
                    WHERE trace_id = %s
                    """,
                    (response, generator_ms, total_ms, trace_id),
                )
            conn.commit()
        finally:
            self._release(conn)

    def fail_trace(self, trace_id: str, error: str):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE rag_traces
                    SET status = 'error',
                        response = %s,
                        completed_at = NOW()
                    WHERE trace_id = %s
                    """,
                    (error, trace_id),
                )
            conn.commit()
        finally:
            self._release(conn)

    def list_traces(self, limit: int = 50) -> list[dict]:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.trace_id,
                        t.query,
                        t.retriever_mode,
                        t.k,
                        t.status,
                        t.retriever_ms,
                        t.generator_ms,
                        t.total_ms,
                        t.created_at,
                        t.completed_at,
                        COUNT(d.id) AS doc_count
                    FROM rag_traces t
                    LEFT JOIN rag_trace_docs d ON d.trace_id = t.trace_id
                    GROUP BY t.trace_id
                    ORDER BY t.created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
            return [dict(zip(cols, row)) for row in rows]
        finally:
            self._release(conn)

    def get_trace(self, trace_id: str) -> dict | None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT trace_id, query, retriever_mode, k, status,
                           response, retriever_ms, generator_ms, total_ms,
                           created_at, completed_at
                    FROM rag_traces
                    WHERE trace_id = %s
                    """,
                    (trace_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
        finally:
            self._release(conn)

    def get_docs(self, trace_id: str) -> list[dict]:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT position, content, metadata
                    FROM rag_trace_docs
                    WHERE trace_id = %s
                    ORDER BY position
                    """,
                    (trace_id,),
                )
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
            return [dict(zip(cols, row)) for row in rows]
        finally:
            self._release(conn)

    def save_multiquery_steps(
        self,
        trace_id: str,
        prompt_sent: str,
        generated_queries: list[str],
        per_query_docs: list[dict],  # [{"query": str, "docs": list[Document]}]
    ):
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rag_multiquery_steps (trace_id, prompt_sent, generated_queries)
                    VALUES (%s, %s, %s)
                    """,
                    (trace_id, prompt_sent, generated_queries),
                )
                for query_idx, entry in enumerate(per_query_docs):
                    for pos, doc in enumerate(entry["docs"]):
                        cur.execute(
                            """
                            INSERT INTO rag_multiquery_docs
                                (trace_id, query_index, generated_query, position, content, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                trace_id,
                                query_idx,
                                entry["query"],
                                pos,
                                doc.page_content,
                                json.dumps(doc.metadata),
                            ),
                        )
            conn.commit()
        finally:
            self._release(conn)

    def get_multiquery_steps(self, trace_id: str) -> dict | None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT prompt_sent, generated_queries
                    FROM rag_multiquery_steps
                    WHERE trace_id = %s
                    """,
                    (trace_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                prompt_sent, generated_queries = row

                cur.execute(
                    """
                    SELECT query_index, generated_query, position, content, metadata
                    FROM rag_multiquery_docs
                    WHERE trace_id = %s
                    ORDER BY query_index, position
                    """,
                    (trace_id,),
                )
                doc_rows = cur.fetchall()

            # Group docs by query_index
            per_query: dict[int, dict] = {}
            for query_index, generated_query, position, content, metadata in doc_rows:
                if query_index not in per_query:
                    per_query[query_index] = {
                        "query_index": query_index,
                        "generated_query": generated_query,
                        "docs": [],
                    }
                per_query[query_index]["docs"].append(
                    {"position": position, "content": content, "metadata": metadata}
                )

            return {
                "prompt_sent": prompt_sent,
                "generated_queries": generated_queries,
                "per_query_docs": [per_query[i] for i in sorted(per_query)],
            }
        finally:
            self._release(conn)


@lru_cache(maxsize=1)
def get_trace_store() -> TraceStore:
    return TraceStore()
