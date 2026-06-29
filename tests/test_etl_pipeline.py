"""End-to-end ETL integration tests."""

from __future__ import annotations

from src.db import execute_sql, query_dataframe
from src.etl.run_pipeline import run_pipeline
from src.quality.checks import run_data_quality


def test_pipeline_loads_warehouse_and_generates_reports(isolated_engine) -> None:
    result = run_pipeline(use_network=False, engine=isolated_engine)

    assert result["status"] == "SUCCESS"
    assert result["records_read"] > 0
    assert result["data_quality"]["rules_evaluated"] == 10
    assert result["data_quality"]["issue_count"] == 0
    assert len(result["reports"]) == 6

    counts = query_dataframe(
        """
        SELECT
          (SELECT COUNT(*) FROM warehouse.fact_position) AS positions,
          (SELECT COUNT(*) FROM warehouse.fact_liquidity_metric) AS liquidity_metrics,
          (SELECT COUNT(*) FROM warehouse.fact_rate_stress) AS stress_results,
          (SELECT COUNT(*) FROM warehouse.dq_run_summary) AS dq_summary_rows,
          (SELECT COUNT(*) FROM warehouse.etl_run_log WHERE status='SUCCESS') AS successful_runs
        """,
        engine=isolated_engine,
    ).iloc[0]
    assert counts["positions"] == 24
    assert counts["liquidity_metrics"] == 12
    assert counts["stress_results"] == 6
    assert counts["dq_summary_rows"] == 10
    assert counts["successful_runs"] == 1


def test_pipeline_provenance_is_explicit(isolated_engine) -> None:
    result = run_pipeline(use_network=False, engine=isolated_engine)
    assert "bundled_public_snapshot" in result["source_modes"]
    assert "synthetic_aladdin_style" in result["source_modes"]


def test_dq_failure_persists_issues_summary_and_alerts(isolated_engine) -> None:
    run_pipeline(use_network=False, engine=isolated_engine)
    execute_sql(
        """
        UPDATE warehouse.fact_position
        SET market_value = market_value + 1000000
        WHERE fund_id='S000009117' AND security_id='USD-CASH'
        """,
        engine=isolated_engine,
    )
    result = run_data_quality(isolated_engine)

    assert result["status"] == "FAIL"
    assert result["issue_count"] >= 2
    assert result["alert_count"] >= 2
    issue_count = query_dataframe(
        "SELECT COUNT(*) AS count FROM warehouse.dq_issue WHERE dq_run_id=:dq_run_id",
        {"dq_run_id": result["dq_run_id"]}, isolated_engine,
    ).iloc[0]["count"]
    assert issue_count == result["issue_count"]
