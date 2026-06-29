"""Liquidity and concentration analytics implemented with pandas."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def liquidity_bucket_exposure(positions: pd.DataFrame) -> pd.DataFrame:
    """Calculate market value and percentage exposure by fund and bucket."""

    grouped = (
        positions.groupby(["fund_id", "position_date", "liquidity_bucket"], as_index=False)["market_value"]
        .sum()
        .rename(columns={"position_date": "metric_date"})
    )
    totals = grouped.groupby("fund_id")["market_value"].transform("sum")
    grouped["exposure_pct"] = grouped["market_value"] / totals * 100
    grouped["calculated_at"] = datetime.now(UTC).replace(tzinfo=None)
    return grouped.sort_values(["fund_id", "liquidity_bucket"]).reset_index(drop=True)


def top_concentrations(positions: pd.DataFrame, fund_id: str, limit: int = 10) -> dict[str, list[dict[str, object]]]:
    """Return top issuer and security concentrations for one fund."""

    fund = positions[positions["fund_id"].eq(fund_id)].copy()
    total = float(fund["market_value"].sum())
    if total == 0:
        return {"by_issuer": [], "by_security": []}

    def ranked(column: str) -> list[dict[str, object]]:
        values = fund.groupby(column, as_index=False)["market_value"].sum()
        values["exposure_pct"] = values["market_value"] / total * 100
        return values.nlargest(limit, "market_value").round(4).to_dict(orient="records")

    return {"by_issuer": ranked("issuer_name"), "by_security": ranked("security_id")}


def cash_and_illiquid_percentages(positions: pd.DataFrame, fund_id: str) -> dict[str, float]:
    """Calculate cash and illiquid percentages for one fund."""

    fund = positions[positions["fund_id"].eq(fund_id)]
    total = float(fund["market_value"].sum())
    if total == 0:
        return {"total_market_value": 0.0, "cash_pct": 0.0, "illiquid_pct": 0.0}
    cash = fund.loc[fund["asset_class"].eq("Cash"), "market_value"].sum()
    illiquid = fund.loc[fund["liquidity_bucket"].eq("Illiquid"), "market_value"].sum()
    return {
        "total_market_value": round(total, 2),
        "cash_pct": round(float(cash / total * 100), 4),
        "illiquid_pct": round(float(illiquid / total * 100), 4),
    }
