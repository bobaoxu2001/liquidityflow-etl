"""SEC Investment Company Series/Class reference-data adapter."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime

import pandas as pd
import requests

from src.config import get_settings

LOGGER = logging.getLogger(__name__)
SEC_SERIES_CLASS_URL = (
    "https://www.sec.gov/files/investment/data/other/"
    "investment-company-series-class-information/"
    "investment-company-series-class-2026.csv"
)

COLUMN_MAP = {
    "CIK Number": "cik",
    "Entity Name": "investment_company_name",
    "Entity Org Type": "organization_type",
    "Series ID": "fund_id",
    "Series Name": "fund_name",
    "Class ID": "class_id",
    "Class Name": "class_name",
    "Class Ticker": "ticker",
}


def _read_public_csv() -> pd.DataFrame:
    settings = get_settings()
    response = requests.get(
        SEC_SERIES_CLASS_URL,
        headers={"User-Agent": settings.sec_user_agent},
        timeout=settings.http_timeout_seconds,
    )
    response.raise_for_status()
    return pd.read_csv(io.BytesIO(response.content), dtype=str)


def ingest_sec_funds(use_network: bool | None = None, limit: int = 50) -> pd.DataFrame:
    """Return normalized SEC series/class rows with explicit provenance."""

    settings = get_settings()
    should_download = (
        settings.public_downloads_enabled if use_network is None else use_network
    )
    source_mode = "official_download"
    try:
        if not should_download:
            raise RuntimeError("Public downloads disabled")
        raw = _read_public_csv()
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        LOGGER.warning("Using bundled SEC snapshot: %s", exc)
        raw = pd.read_csv(
            settings.data_dir / "public_samples" / "sec_funds_sample.csv", dtype=str
        )
        source_mode = "bundled_public_snapshot"

    missing = set(COLUMN_MAP) - set(raw.columns)
    if missing:
        raise ValueError(f"SEC input missing columns: {sorted(missing)}")

    result = raw[list(COLUMN_MAP)].rename(columns=COLUMN_MAP)
    result = result[
        result["fund_id"].notna()
        & result["ticker"].notna()
        & result["organization_type"].eq("30")
    ].drop_duplicates("fund_id").head(limit)
    result["source_mode"] = source_mode
    result["source_url"] = SEC_SERIES_CLASS_URL
    result["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
    return result.reset_index(drop=True)
