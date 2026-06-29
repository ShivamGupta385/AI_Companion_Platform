from backend.app.core.config import settings

# LangGraph Postgres checkpointer
from langgraph.checkpoint.postgres import PostgresSaver


def get_checkpointer():
    """
    Create a PostgreSQL-backed LangGraph checkpointer.

    LangGraph PostgresSaver.from_conn_string(...) returns
    a context manager, so we must enter it before using it.
    """
    db_uri = settings.DATABASE_URL

    # SQLAlchemy-style URL -> psycopg-compatible URL
    if db_uri.startswith("postgresql+psycopg://"):
        db_uri = db_uri.replace(
            "postgresql+psycopg://",
            "postgresql://",
            1
        )

    return PostgresSaver.from_conn_string(db_uri)