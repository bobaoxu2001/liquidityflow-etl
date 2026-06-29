"""pandas transformations for synthetic portfolio positions."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

POSITION_COLUMNS = [
    "fund_id", "security_id", "position_date", "price_date", "security_name",
    "issuer_name", "asset_class", "quantity", "price", "market_value",
    "currency", "coupon_rate", "maturity_date", "modified_duration",
    "days_to_liquidate", "liquidity_bucket", "source_mode",
]


def transform_positions(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize types and text without silently repairing DQ failures."""

    missing = set(POSITION_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Position input missing columns: {sorted(missing)}")

    result = raw[POSITION_COLUMNS].copy()
    for column in ("fund_id", "security_id", "security_name", "issuer_name"):
        result[column] = result[column].astype("string").str.strip()
    result["asset_class"] = result["asset_class"].astype("string").str.strip().str.title()
    result["currency"] = result["currency"].astype("string").str.upper().str.strip()
    result["liquidity_bucket"] = (
        result["liquidity_bucket"].astype("string").str.strip().replace("", pd.NA)
    )
    for column in ("position_date", "price_date", "maturity_date"):
        result[column] = pd.to_datetime(result[column], errors="coerce").dt.date
    for column in (
        "quantity", "price", "market_value", "coupon_rate", "modified_duration",
        "days_to_liquidate",
    ):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["loaded_at"] = datetime.now(UTC).replace(tzinfo=None)
    return result
