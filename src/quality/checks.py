"""Data quality execution and persistence service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from sqlalchemy import Engine

from src.db import append_dataframe, query_dataframe
from src.quality.alerting import create_dq_alerts
from src.quality.rules import RULES, evaluate_rules


def run_data_quality(engine: Engine, etl_run_id: str | None = None) -> dict[str, object]:
    """Run DQ against the current warehouse snapshot and persist issue details."""

    positions = query_dataframe("SELECT * FROM warehouse.fact_position", engine=engine)
    nav = query_dataframe("SELECT * FROM warehouse.fact_fund_nav", engine=engine)
    issues = evaluate_rules(positions, nav)
    dq_run_id = str(uuid4())
    now = datetime.now(UTC).replace(tzinfo=None)
    if not issues.empty:
        persisted = issues.copy()
        persisted.insert(0, "issue_id", [str(uuid4()) for _ in range(len(persisted))])
        persisted.insert(1, "dq_run_id", dq_run_id)
        persisted.insert(2, "etl_run_id", etl_run_id)
        persisted.insert(3, "detected_at", now)
        persisted["position_date"] = pd.to_datetime(persisted["position_date"], errors="coerce").dt.date
        append_dataframe(persisted, "dq_issue", "warehouse", engine)
    rule_counts = issues["rule_id"].value_counts().to_dict() if not issues.empty else {}
    summary = pd.DataFrame(
        [
            {
                "dq_run_id": dq_run_id,
                "etl_run_id": etl_run_id,
                "executed_at": now,
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "severity": rule.severity,
                "status": "FAIL" if rule_counts.get(rule.rule_id, 0) else "PASS",
                "issue_count": int(rule_counts.get(rule.rule_id, 0)),
            }
            for rule in RULES
        ]
    )
    append_dataframe(summary, "dq_run_summary", "warehouse", engine)
    alert_count = create_dq_alerts(issues, dq_run_id, engine)
    failed_rules = int(issues["rule_id"].nunique()) if not issues.empty else 0
    return {
        "dq_run_id": dq_run_id,
        "status": "PASS" if issues.empty else "FAIL",
        "rules_evaluated": len(RULES),
        "rules_failed": failed_rules,
        "issue_count": len(issues),
        "alert_count": alert_count,
    }


def latest_dq_summary(engine: Engine) -> list[dict[str, object]]:
    """Return pass/fail counts by rule for the most recent DQ run."""

    summary = query_dataframe(
        """
        SELECT rule_id, rule_name, severity, status, issue_count
        FROM warehouse.dq_run_summary
        WHERE dq_run_id = (
            SELECT dq_run_id FROM warehouse.dq_run_summary
            ORDER BY executed_at DESC LIMIT 1
        )
        ORDER BY rule_id
        """,
        engine=engine,
    )
    records = summary.to_dict(orient="records")
    for record in records:
        record["issue_count"] = int(record["issue_count"])
    return records
