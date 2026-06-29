"""Shared isolated DuckDB fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine

from src.config import get_settings
from src.db import get_engine


@pytest.fixture()
def isolated_engine(tmp_path, monkeypatch) -> Iterator[Engine]:
    database_path = tmp_path / "test_liquidityflow.duckdb"
    monkeypatch.setenv("DATABASE_URL", f"duckdb:///{database_path}")
    monkeypatch.setenv("PUBLIC_DOWNLOADS_ENABLED", "false")
    get_settings.cache_clear()
    get_engine.cache_clear()
    engine = get_engine()
    yield engine
    engine.dispose()
    get_engine.cache_clear()
    get_settings.cache_clear()
