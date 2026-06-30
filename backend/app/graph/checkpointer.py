from backend.app.core.config import settings

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def get_checkpointer():
    """
    Create an async PostgreSQL-backed LangGraph checkpointer.

    Returns an async context manager that must be used with:

        async with get_checkpointer() as checkpointer:
            ...
    """

    db_uri = settings.DATABASE_URL

    # SQLAlchemy URL -> psycopg URL
    if db_uri.startswith("postgresql+psycopg://"):
        db_uri = db_uri.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1
        )

    return AsyncPostgresSaver.from_conn_string(db_uri)