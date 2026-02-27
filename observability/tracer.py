import os
import uuid as _uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from langchain_core.documents import Document
from sqlalchemy import UUID, ForeignKey, Index, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


class RagTrace(Base):
    __tablename__ = "rag_traces"
    __table_args__ = (Index("idx_rag_traces_created_at", "created_at"),)

    trace_id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    retriever_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    k: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )
    response: Mapped[str | None] = mapped_column(Text)
    retriever_ms: Mapped[int | None] = mapped_column(Integer)
    generator_ms: Mapped[int | None] = mapped_column(Integer)
    total_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    docs: Mapped[list["RagTraceDoc"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )
    multiquery_steps: Mapped[list["RagMultiqueryStep"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan"
    )


class RagTraceDoc(Base):
    __tablename__ = "rag_trace_docs"
    __table_args__ = (Index("idx_rag_trace_docs_trace_id", "trace_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_traces.trace_id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default={}
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    trace: Mapped["RagTrace"] = relationship(back_populates="docs")


class RagMultiqueryStep(Base):
    __tablename__ = "rag_multiquery_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_traces.trace_id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_sent: Mapped[str] = mapped_column(Text, nullable=False)
    generated_queries: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    trace: Mapped["RagTrace"] = relationship(back_populates="multiquery_steps")


class RagMultiqueryDoc(Base):
    __tablename__ = "rag_multiquery_docs"
    __table_args__ = (Index("idx_rag_multiquery_docs_trace", "trace_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_traces.trace_id", ondelete="CASCADE"),
        nullable=False,
    )
    query_index: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_query: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    doc_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default={}
    )


# ---------------------------------------------------------------------------
# Data transfer objects (kept for external consumers)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TraceStore
# ---------------------------------------------------------------------------


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

        url = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
        self._engine = create_async_engine(url, pool_size=10, max_overflow=0)
        self._session: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine, expire_on_commit=False
        )

    async def _ensure_schema(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_trace(
        self, trace_id: str, query: str, mode: str, k: int, created_at: float
    ):
        async with self._session() as session:
            session.add(
                RagTrace(
                    trace_id=_uuid.UUID(trace_id),
                    query=query,
                    retriever_mode=mode,
                    k=k,
                    status="in_progress",
                    created_at=datetime.fromtimestamp(created_at, tz=timezone.utc),
                )
            )
            await session.commit()

    async def save_docs(self, trace_id: str, docs: list[Document], retriever_ms: int):
        uid = _uuid.UUID(trace_id)
        async with self._session() as session:
            for i, doc in enumerate(docs):
                session.add(
                    RagTraceDoc(
                        trace_id=uid,
                        position=i,
                        content=doc.page_content,
                        doc_metadata=doc.metadata,
                    )
                )
            trace = await session.get(RagTrace, uid)
            if trace is None:
                raise ValueError(f"RagTrace {trace_id} not found")
            trace.retriever_ms = retriever_ms
            await session.commit()

    async def complete_trace(
        self,
        trace_id: str,
        response: str,
        generator_ms: int,
        total_ms: int,
    ):
        async with self._session() as session:
            trace = await session.get(RagTrace, _uuid.UUID(trace_id))
            if trace is None:
                raise ValueError(f"RagTrace {trace_id} not found")
            trace.status = "complete"
            trace.response = response
            trace.generator_ms = generator_ms
            trace.total_ms = total_ms
            trace.completed_at = datetime.now(tz=timezone.utc)
            await session.commit()

    async def fail_trace(self, trace_id: str, error: str):
        async with self._session() as session:
            trace = await session.get(RagTrace, _uuid.UUID(trace_id))
            if trace is None:
                raise ValueError(f"RagTrace {trace_id} not found")
            trace.status = "error"
            trace.response = error
            trace.completed_at = datetime.now(tz=timezone.utc)
            await session.commit()

    async def list_traces(self, limit: int = 50) -> list[dict]:
        async with self._session() as session:
            stmt = (
                select(
                    RagTrace.trace_id,
                    RagTrace.query,
                    RagTrace.retriever_mode,
                    RagTrace.k,
                    RagTrace.status,
                    RagTrace.retriever_ms,
                    RagTrace.generator_ms,
                    RagTrace.total_ms,
                    RagTrace.created_at,
                    RagTrace.completed_at,
                    func.count(RagTraceDoc.id).label("doc_count"),
                )
                .outerjoin(RagTraceDoc, RagTraceDoc.trace_id == RagTrace.trace_id)
                .group_by(RagTrace.trace_id)
                .order_by(RagTrace.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [row._asdict() for row in result]

    async def get_trace(self, trace_id: str) -> dict | None:
        async with self._session() as session:
            trace = await session.get(RagTrace, _uuid.UUID(trace_id))
            if trace is None:
                return None
            return {
                "trace_id": str(trace.trace_id),
                "query": trace.query,
                "retriever_mode": trace.retriever_mode,
                "k": trace.k,
                "status": trace.status,
                "response": trace.response,
                "retriever_ms": trace.retriever_ms,
                "generator_ms": trace.generator_ms,
                "total_ms": trace.total_ms,
                "created_at": trace.created_at,
                "completed_at": trace.completed_at,
            }

    async def get_docs(self, trace_id: str) -> list[dict]:
        async with self._session() as session:
            stmt = (
                select(
                    RagTraceDoc.position, RagTraceDoc.content, RagTraceDoc.doc_metadata
                )
                .where(RagTraceDoc.trace_id == _uuid.UUID(trace_id))
                .order_by(RagTraceDoc.position)
            )
            result = await session.execute(stmt)
            return [
                {"position": pos, "content": content, "metadata": metadata}
                for pos, content, metadata in result
            ]

    async def save_multiquery_steps(
        self,
        trace_id: str,
        prompt_sent: str,
        generated_queries: list[str],
        per_query_docs: list[dict],  # [{"query": str, "docs": list[Document]}]
    ):
        uid = _uuid.UUID(trace_id)
        async with self._session() as session:
            session.add(
                RagMultiqueryStep(
                    trace_id=uid,
                    prompt_sent=prompt_sent,
                    generated_queries=generated_queries,
                )
            )
            for query_idx, entry in enumerate(per_query_docs):
                for pos, doc in enumerate(entry["docs"]):
                    session.add(
                        RagMultiqueryDoc(
                            trace_id=uid,
                            query_index=query_idx,
                            generated_query=entry["query"],
                            position=pos,
                            content=doc.page_content,
                            doc_metadata=doc.metadata,
                        )
                    )
            await session.commit()

    async def get_multiquery_steps(self, trace_id: str) -> dict | None:
        uid = _uuid.UUID(trace_id)
        async with self._session() as session:
            step_result = await session.execute(
                select(
                    RagMultiqueryStep.prompt_sent, RagMultiqueryStep.generated_queries
                ).where(RagMultiqueryStep.trace_id == uid)
            )
            row = step_result.first()
            if row is None:
                return None
            prompt_sent, generated_queries = row

            doc_result = await session.execute(
                select(
                    RagMultiqueryDoc.query_index,
                    RagMultiqueryDoc.generated_query,
                    RagMultiqueryDoc.position,
                    RagMultiqueryDoc.content,
                    RagMultiqueryDoc.doc_metadata,
                )
                .where(RagMultiqueryDoc.trace_id == uid)
                .order_by(RagMultiqueryDoc.query_index, RagMultiqueryDoc.position)
            )

            per_query: dict[int, dict] = {}
            for query_index, generated_query, position, content, metadata in doc_result:
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


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_store: TraceStore | None = None


async def get_trace_store() -> TraceStore:
    global _store
    if _store is None:
        _store = TraceStore()
        await _store._ensure_schema()
    return _store
