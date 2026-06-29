"""Fund, portfolio analytics, stress, and reporting routes."""

from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.analytics.portfolio_risk import build_liquidity_report
from src.api.utils import dataframe_records
from src.db import get_engine, query_dataframe

router = APIRouter(tags=["portfolio"])


def _positions(fund_id: str) -> pd.DataFrame:
    return query_dataframe(
        "SELECT * FROM warehouse.fact_position WHERE fund_id=:fund_id ORDER BY market_value DESC",
        {"fund_id": fund_id}, get_engine(),
    )


def _require_positions(fund_id: str) -> pd.DataFrame:
    positions = _positions(fund_id)
    if positions.empty:
        raise HTTPException(status_code=404, detail=f"Unknown fund_id: {fund_id}")
    return positions


@router.get("/funds")
def get_funds() -> list[dict[str, object]]:
    frame = query_dataframe(
        "SELECT fund_id, fund_name, class_id, cik, ticker, source_mode FROM warehouse.dim_fund ORDER BY fund_name",
        engine=get_engine(),
    )
    return dataframe_records(frame)


@router.get("/portfolio/{fund_id}/positions")
def get_positions(fund_id: str) -> list[dict[str, object]]:
    return dataframe_records(_require_positions(fund_id))


@router.get("/portfolio/{fund_id}/liquidity")
def get_liquidity(fund_id: str) -> list[dict[str, object]]:
    _require_positions(fund_id)
    frame = query_dataframe(
        """
        SELECT metric_date, fund_id, liquidity_bucket, market_value, exposure_pct
        FROM warehouse.fact_liquidity_metric
        WHERE fund_id=:fund_id ORDER BY exposure_pct DESC
        """,
        {"fund_id": fund_id}, get_engine(),
    )
    return dataframe_records(frame)


@router.get("/portfolio/{fund_id}/rate-stress")
def get_rate_stress(fund_id: str) -> list[dict[str, object]]:
    _require_positions(fund_id)
    frame = query_dataframe(
        """
        SELECT scenario_date, fund_id, scenario_bps, estimated_pnl, estimated_nav_impact_pct
        FROM warehouse.fact_rate_stress
        WHERE fund_id=:fund_id ORDER BY scenario_bps DESC
        """,
        {"fund_id": fund_id}, get_engine(),
    )
    return dataframe_records(frame)


@router.get("/regulatory/liquidity-report/{fund_id}", response_model=None)
def get_regulatory_report(
    fund_id: str,
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> dict[str, object] | StreamingResponse:
    positions = _require_positions(fund_id)
    nav = query_dataframe(
        "SELECT * FROM warehouse.fact_fund_nav WHERE fund_id=:fund_id",
        {"fund_id": fund_id}, get_engine(),
    )
    funds = query_dataframe(
        "SELECT * FROM warehouse.dim_fund WHERE fund_id=:fund_id",
        {"fund_id": fund_id}, get_engine(),
    )
    report = build_liquidity_report(fund_id, positions, nav, funds)
    if format == "json":
        return report
    rows = []
    for bucket in report["liquidity_buckets"]:
        rows.append(
            {
                "as_of_date": report["as_of_date"], "fund_id": fund_id,
                **bucket, "cash_pct": report["portfolio_summary"]["cash_pct"],
                "illiquid_pct": report["portfolio_summary"]["illiquid_pct"],
            }
        )
    buffer = io.StringIO()
    pd.DataFrame(rows).to_csv(buffer, index=False)
    return StreamingResponse(
        iter([buffer.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=liquidity_report_{fund_id}.csv"},
    )
