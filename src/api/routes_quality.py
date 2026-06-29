"""Data quality issue, summary, and alert routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.utils import dataframe_records
from src.db import get_engine, query_dataframe
from src.quality.checks import latest_dq_summary

router = APIRouter(tags=["data-quality"])


@router.get("/dq/issues")
def get_dq_issues(limit: int = Query(default=100, ge=1, le=1_000)) -> list[dict[str, object]]:
    frame = query_dataframe(
        f"SELECT * FROM warehouse.dq_issue ORDER BY detected_at DESC LIMIT {limit}",
        engine=get_engine(),
    )
    return dataframe_records(frame)


@router.get("/dq/summary")
def get_dq_summary() -> list[dict[str, object]]:
    return latest_dq_summary(get_engine())


@router.get("/alerts")
def get_alerts(limit: int = Query(default=100, ge=1, le=1_000)) -> list[dict[str, object]]:
    frame = query_dataframe(
        f"SELECT * FROM warehouse.alert ORDER BY created_at DESC LIMIT {limit}",
        engine=get_engine(),
    )
    return dataframe_records(frame)
