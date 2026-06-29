"""FINRA customer margin statistics adapter."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime

import pandas as pd
import requests

from src.config import get_settings

LOGGER = logging.getLogger(__name__)
FINRA_MARGIN_URL = (
    "https://www.finra.org/rules-guidance/key-topics/"
    "margin-accounts/margin-statistics"
)


def _find_margin_table(html: str) -> pd.DataFrame:
    for table in pd.read_html(io.StringIO(html)):
        flattened = [str(column) for column in table.columns]
        if any("Debit Balances" in column for column in flattened):
            table.columns = flattened
            return table
    raise ValueError("FINRA margin table not found")


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False), errors="coerce"
    )


def ingest_finra_margin(use_network: bool | None = None) -> pd.DataFrame:
    """Return FINRA margin statistics with a net leverage indicator."""

    settings = get_settings()
    should_download = (
        settings.public_downloads_enabled if use_network is None else use_network
    )
    source_mode = "official_web_table"
    try:
        if not should_download:
            raise RuntimeError("Public downloads disabled")
        response = requests.get(FINRA_MARGIN_URL, timeout=settings.http_timeout_seconds)
        response.raise_for_status()
        raw = _find_margin_table(response.text)
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        LOGGER.warning("Using bundled FINRA snapshot: %s", exc)
        raw = pd.read_csv(
            settings.data_dir / "public_samples" / "finra_margin_sample.csv"
        )
        source_mode = "bundled_public_snapshot"

    columns = list(raw.columns)
    month_col = next(column for column in columns if "Month/Year" in column)
    debit_col = next(column for column in columns if "Debit Balances" in column)
    cash_col = next(c for c in columns if "Free Credit" in c and "Cash" in c)
    margin_col = next(
        c for c in columns if "Free Credit" in c and "Securities Margin" in c
    )
    result = pd.DataFrame(
        {
            "report_month": pd.to_datetime(raw[month_col], format="%b-%y", errors="coerce"),
            "debit_balances_mm": _numeric(raw[debit_col]),
            "free_credit_cash_mm": _numeric(raw[cash_col]),
            "free_credit_margin_mm": _numeric(raw[margin_col]),
        }
    ).dropna(subset=["report_month", "debit_balances_mm"])
    result["report_month"] = result["report_month"].dt.date
    result["net_margin_leverage_mm"] = result["debit_balances_mm"] - (
        result["free_credit_cash_mm"] + result["free_credit_margin_mm"]
    )
    result["source_mode"] = source_mode
    result["source_url"] = FINRA_MARGIN_URL
    result["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
    return result.sort_values("report_month").reset_index(drop=True)
