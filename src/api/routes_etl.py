"""ETL and on-demand DQ API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.db import get_engine
from src.etl.run_pipeline import run_pipeline
from src.quality.checks import run_data_quality

router = APIRouter(tags=["operations"])


@router.post("/etl/run")
def trigger_etl(refresh_public: bool = False) -> dict[str, object]:
    """Execute one synchronous ETL run and return its operational summary."""

    try:
        return run_pipeline(use_network=refresh_public, engine=get_engine())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"ETL failed: {exc}") from exc


@router.post("/dq/run")
def trigger_dq() -> dict[str, object]:
    """Execute DQ against the latest warehouse snapshot."""

    try:
        return run_data_quality(get_engine())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DQ run failed: {exc}") from exc
