"""ODS and warehouse loading functions."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
from sqlalchemy import Engine

from src.db import append_dataframe, execute_sql


def load_ods(
    funds: pd.DataFrame,
    rates: pd.DataFrame,
    margin: pd.DataFrame,
    positions: pd.DataFrame,
    nav: pd.DataFrame,
    engine: Engine,
) -> int:
    """Replace the current ODS snapshot and return rows written."""

    tables = {
        "fund_reference": funds,
        "treasury_rates": rates,
        "finra_margin": margin,
        "positions_raw": positions,
        "fund_nav": nav,
    }
    for table, frame in tables.items():
        execute_sql(f"DELETE FROM ods.{table}", engine=engine)
        append_dataframe(frame, table, "ods", engine)
    return sum(len(frame) for frame in tables.values())


def load_warehouse(
    funds: pd.DataFrame,
    rates: pd.DataFrame,
    margin: pd.DataFrame,
    positions: pd.DataFrame,
    nav: pd.DataFrame,
    engine: Engine,
) -> int:
    """Load curated dimensional and fact tables from normalized DataFrames."""

    now = datetime.now(UTC).replace(tzinfo=None)
    dim_fund = funds[
        ["fund_id", "fund_name", "class_id", "cik", "ticker", "source_mode"]
    ].copy()
    dim_fund["effective_at"] = now

    fact_position = positions.copy()
    fact_nav = nav[["fund_id", "nav_date", "nav_value"]].copy()
    fact_nav["loaded_at"] = now
    fact_rate = rates[["rate_date", "tenor", "rate_pct", "source_mode"]].copy()
    fact_rate["loaded_at"] = now
    fact_margin = margin[
        [
            "report_month", "debit_balances_mm", "free_credit_cash_mm",
            "free_credit_margin_mm", "net_margin_leverage_mm", "source_mode",
        ]
    ].copy()
    fact_margin["loaded_at"] = now

    tables = {
        "dim_fund": dim_fund,
        "fact_position": fact_position,
        "fact_fund_nav": fact_nav,
        "fact_rate": fact_rate,
        "fact_margin_indicator": fact_margin,
    }
    for table, frame in tables.items():
        execute_sql(f"DELETE FROM warehouse.{table}", engine=engine)
        append_dataframe(frame, table, "warehouse", engine)
    return sum(len(frame) for frame in tables.values())
