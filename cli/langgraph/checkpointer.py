"""Checkpointer setup for LangGraph state persistence."""

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


def get_memory_checkpointer() -> MemorySaver:
    """
    Create an in-memory checkpointer for LangGraph.

    This is simpler and works well for development and single-session use.
    State is kept in memory only (not persisted across restarts).

    Returns:
        MemorySaver configured for checkpointing.
    """
    return MemorySaver()


def get_postgres_checkpointer() -> PostgresSaver:
    """
    Create a PostgreSQL checkpointer for LangGraph (synchronous only).

    Note: The PostgreSQL checkpointer in LangGraph currently only supports
    synchronous operations. For async usage, use MemorySaver instead.

    Uses the same database as the observability tracer.
    Creates the necessary checkpoint tables if they don't exist.

    Returns:
        PostgresSaver configured for the application database.
    """
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

    # Build PostgreSQL connection string
    conn_string = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

    # Create checkpointer
    # checkpointer = PostgresSaver.from_conn_string(conn_string)

    with PostgresSaver.from_conn_string(conn_string) as checkpointer:
        # Initialize schema (creates checkpoint tables if they don't exist)
        checkpointer.setup()

        return checkpointer


async def get_checkpointer() -> MemorySaver:
    """
    Get the default checkpointer for async operations.

    Currently returns MemorySaver as PostgresSaver doesn't fully support async.

    Returns:
        MemorySaver instance.
    """
    return get_memory_checkpointer()


# Singleton instance
_checkpointer: MemorySaver | None = None


async def get_or_create_checkpointer() -> MemorySaver:
    """Get or create the singleton checkpointer instance."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await get_checkpointer()
    return _checkpointer
