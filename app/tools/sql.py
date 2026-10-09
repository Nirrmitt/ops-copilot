"""Bounded read-only SQL tool."""
import os

from sqlalchemy import create_engine, text

from app.guards import validate_select


def get_engine():
    """Create an engine using the configured database URL."""
    url = os.getenv("DATABASE_URL", "sqlite:///data/ops.db")
    return create_engine(url, connect_args={"timeout": 2} if url.startswith("sqlite") else {})


def sql_query(sql: str) -> dict[str, object]:
    """Execute validated SQL with a short timeout and return rows plus SQL."""
    safe_sql = validate_select(sql)
    with get_engine().connect() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SET LOCAL statement_timeout = '2000ms'"))
        rows = connection.execute(text(safe_sql)).mappings().all()
    return {"sql": safe_sql, "rows": [dict(row) for row in rows]}
