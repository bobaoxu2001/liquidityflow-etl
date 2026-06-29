"""Persist operational alerts derived from DQ results."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from sqlalchemy import Engine

from src.db import append_dataframe


def create_dq_alerts(issues: pd.DataFrame, dq_run_id: str, engine: Engine) -> int:
    """Create one open alert per failed error-level rule."""

    if issues.empty:
        return 0
    errors = issues[issues["severity"].eq("ERROR")]
    records = []
    now = datetime.now(UTC).replace(tzinfo=None)
    for (rule_id, rule_name), group in errors.groupby(["rule_id", "rule_name"]):
        records.append(
            {
                "alert_id": str(uuid4()), "dq_run_id": dq_run_id, "created_at": now,
                "severity": "HIGH", "alert_type": "DATA_QUALITY",
                "message": f"{rule_id} {rule_name}: {len(group)} issue(s)", "status": "OPEN",
            }
        )
    append_dataframe(pd.DataFrame(records), "alert", "warehouse", engine)
    return len(records)
