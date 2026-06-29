"""FRED H.15 Treasury constant-maturity rate adapter."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime

import pandas as pd
import requests

from src.config import get_settings

LOGGER = logging.getLogger(__name__)
FRED_RATES_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2,DGS10"


def ingest_fred_rates(use_network: bool | None = None) -> pd.DataFrame:
    """Download or load a bundled FRED snapshot and return long-form rates."""

    settings = get_settings()
    should_download = (
        settings.public_downloads_enabled if use_network is None else use_network
    )
    source_mode = "official_download"
    try:
        if not should_download:
            raise RuntimeError("Public downloads disabled")
        response = requests.get(FRED_RATES_URL, timeout=settings.http_timeout_seconds)
        response.raise_for_status()
        raw = pd.read_csv(io.BytesIO(response.content))
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        LOGGER.warning("Using bundled FRED snapshot: %s", exc)
        raw = pd.read_csv(
            settings.data_dir / "public_samples" / "fred_rates_sample.csv"
        )
        source_mode = "bundled_public_snapshot"

    date_column = "observation_date" if "observation_date" in raw.columns else "DATE"
    required = {date_column, "DGS2", "DGS10"}
    if not required.issubset(raw.columns):
        raise ValueError(f"FRED input missing columns: {sorted(required - set(raw.columns))}")

    result = raw.melt(
        id_vars=[date_column], value_vars=["DGS2", "DGS10"],
        var_name="tenor", value_name="rate_pct",
    ).rename(columns={date_column: "rate_date"})
    result["rate_date"] = pd.to_datetime(result["rate_date"], errors="coerce").dt.date
    result["rate_pct"] = pd.to_numeric(result["rate_pct"], errors="coerce")
    result = result.dropna(subset=["rate_date", "rate_pct"])
    result["source_mode"] = source_mode
    result["source_url"] = FRED_RATES_URL
    result["ingested_at"] = datetime.now(UTC).replace(tzinfo=None)
    return result.sort_values(["rate_date", "tenor"]).reset_index(drop=True)
