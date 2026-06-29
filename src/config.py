"""Environment-backed application settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime configuration with safe local defaults."""

    project_root: Path
    database_url: str
    public_downloads_enabled: bool
    http_timeout_seconds: int
    sec_user_agent: str
    market_value_tolerance_pct: float
    nav_reconciliation_tolerance_pct: float

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build settings once per process; tests may clear the cache."""

    default_database = "duckdb:///data/liquidityflow.duckdb"
    return Settings(
        project_root=PROJECT_ROOT,
        database_url=os.getenv("DATABASE_URL", default_database),
        public_downloads_enabled=_as_bool(
            os.getenv("PUBLIC_DOWNLOADS_ENABLED", "false")
        ),
        http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
        sec_user_agent=os.getenv(
            "SEC_USER_AGENT", "LiquidityFlowETL portfolio-project contact@example.com"
        ),
        market_value_tolerance_pct=float(
            os.getenv("MARKET_VALUE_TOLERANCE_PCT", "0.001")
        ),
        nav_reconciliation_tolerance_pct=float(
            os.getenv("NAV_RECONCILIATION_TOLERANCE_PCT", "0.005")
        ),
    )
