"""SQLAlchemy connection and schema utilities.

The default dialect is DuckDB. Any SQLAlchemy-supported enterprise dialect can
be supplied through ``DATABASE_URL`` (for example DB2 or SAP/Sybase ASE) after
installing the appropriate driver and adapting schema DDL where necessary.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine, text

from src.config import get_settings


def _normalized_database_url(url: str) -> str:
    if not url.startswith("duckdb:///data/"):
        return url
    relative_path = url.removeprefix("duckdb:///")
    absolute_path = get_settings().project_root / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return f"duckdb:///{absolute_path}"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide SQLAlchemy engine."""

    url = _normalized_database_url(get_settings().database_url)
    return create_engine(url, future=True)


def _sql_statements(path: Path) -> list[str]:
    text_value = path.read_text(encoding="utf-8")
    return [statement.strip() for statement in text_value.split(";") if statement.strip()]


def initialize_database(engine: Engine | None = None) -> None:
    """Create ODS and warehouse objects idempotently."""

    active_engine = engine or get_engine()
    sql_dir = get_settings().project_root / "sql"
    with active_engine.begin() as connection:
        for filename in ("ods_schema.sql", "warehouse_schema.sql"):
            for statement in _sql_statements(sql_dir / filename):
                connection.execute(text(statement))


def query_dataframe(
    query: str,
    params: dict[str, Any] | None = None,
    engine: Engine | None = None,
) -> pd.DataFrame:
    """Execute a parameterized query and return a DataFrame."""

    active_engine = engine or get_engine()
    with active_engine.connect() as connection:
        return pd.read_sql_query(text(query), connection, params=params or {})


def append_dataframe(
    frame: pd.DataFrame,
    table: str,
    schema: str,
    engine: Engine | None = None,
) -> None:
    """Append a DataFrame to an existing table through SQLAlchemy."""

    if frame.empty:
        return
    active_engine = engine or get_engine()
    frame.to_sql(
        name=table,
        con=active_engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1_000,
    )


def execute_sql(
    query: str,
    params: dict[str, Any] | None = None,
    engine: Engine | None = None,
) -> None:
    """Execute a statement in a transaction."""

    active_engine = engine or get_engine()
    with active_engine.begin() as connection:
        connection.execute(text(query), params or {})
