"""Portfolio risk summary and regulatory-style report assembly."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.analytics.liquidity_metrics import (
    cash_and_illiquid_percentages,
    liquidity_bucket_exposure,
    top_concentrations,
)
from src.analytics.rate_stress import calculate_rate_stress


def build_liquidity_report(
    fund_id: str,
    positions: pd.DataFrame,
    fund_nav: pd.DataFrame,
    fund_reference: pd.DataFrame | None = None,
) -> dict[str, object]:
    """Build a transparent regulatory-style liquidity monitoring payload."""

    fund = positions[positions["fund_id"].eq(fund_id)]
    if fund.empty:
        raise ValueError(f"Unknown fund_id: {fund_id}")
    exposure = liquidity_bucket_exposure(fund)
    stress = calculate_rate_stress(fund, fund_nav[fund_nav["fund_id"].eq(fund_id)])
    risk = cash_and_illiquid_percentages(fund, fund_id)
    reference: dict[str, object] = {"fund_id": fund_id}
    if fund_reference is not None and not fund_reference.empty:
        match = fund_reference[fund_reference["fund_id"].eq(fund_id)]
        if not match.empty:
            reference.update(
                {
                    "fund_name": match.iloc[0].get("fund_name"),
                    "ticker": match.iloc[0].get("ticker"),
                }
            )
    return {
        "report_type": "portfolio_liquidity_monitoring_demo",
        "as_of_date": str(pd.to_datetime(fund["position_date"]).max().date()),
        "fund": reference,
        "portfolio_summary": risk,
        "liquidity_buckets": exposure[
            ["liquidity_bucket", "market_value", "exposure_pct"]
        ].round(4).to_dict(orient="records"),
        "concentrations": top_concentrations(fund, fund_id),
        "rate_stress": stress[
            ["scenario_bps", "estimated_pnl", "estimated_nav_impact_pct"]
        ].to_dict(orient="records"),
        "methodology_note": (
            "Portfolio positions are synthetic. Public SEC/FRED/FINRA sources are "
            "reference and market-context inputs. This is a portfolio demonstration, "
            "not an official regulatory filing or investment recommendation."
        ),
    }


def write_liquidity_report(report: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    """Write JSON and flattened CSV versions of a liquidity report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fund_id = str(report["fund"]["fund_id"])
    json_path = output_dir / f"liquidity_report_{fund_id}.json"
    csv_path = output_dir / f"liquidity_report_{fund_id}.csv"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    rows = []
    for bucket in report["liquidity_buckets"]:
        rows.append(
            {
                "as_of_date": report["as_of_date"], "fund_id": fund_id,
                "liquidity_bucket": bucket["liquidity_bucket"],
                "market_value": bucket["market_value"], "exposure_pct": bucket["exposure_pct"],
                "cash_pct": report["portfolio_summary"]["cash_pct"],
                "illiquid_pct": report["portfolio_summary"]["illiquid_pct"],
            }
        )
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return json_path, csv_path
