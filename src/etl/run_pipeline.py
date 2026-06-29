"""Daily LiquidityFlow ETL command and orchestration service."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

import pandas as pd
from sqlalchemy import Engine

from src.analytics.liquidity_metrics import liquidity_bucket_exposure
from src.analytics.portfolio_risk import build_liquidity_report, write_liquidity_report
from src.analytics.rate_stress import calculate_rate_stress
from src.config import get_settings
from src.db import append_dataframe, execute_sql, get_engine, initialize_database
from src.etl.load_warehouse import load_ods, load_warehouse
from src.etl.transform_positions import transform_positions
from src.ingest.aladdin_positions_mock import generate_aladdin_positions
from src.ingest.finra_margin import ingest_finra_margin
from src.ingest.fred_rates import ingest_fred_rates
from src.ingest.sec_funds import ingest_sec_funds
from src.quality.checks import run_data_quality

LOGGER = logging.getLogger(__name__)


def _start_log(run_id: str, engine: Engine) -> None:
    append_dataframe(
        pd.DataFrame(
            [{
                "run_id": run_id, "started_at": datetime.now(UTC).replace(tzinfo=None),
                "completed_at": None, "status": "RUNNING", "records_read": 0,
                "records_written": 0, "dq_issue_count": 0, "source_modes": None,
                "error_message": None,
            }]
        ),
        "etl_run_log", "warehouse", engine,
    )


def run_pipeline(use_network: bool | None = None, engine: Engine | None = None) -> dict[str, object]:
    """Run ingest, transform, load, DQ, analytics, and report generation."""

    active_engine = engine or get_engine()
    initialize_database(active_engine)
    run_id = str(uuid4())
    _start_log(run_id, active_engine)
    try:
        funds = ingest_sec_funds(use_network=use_network)
        rates = ingest_fred_rates(use_network=use_network)
        margin = ingest_finra_margin(use_network=use_network)
        raw_positions, nav = generate_aladdin_positions()
        records_read = sum(map(len, [funds, rates, margin, raw_positions, nav]))

        ods_written = load_ods(funds, rates, margin, raw_positions, nav, active_engine)
        positions = transform_positions(raw_positions)
        warehouse_written = load_warehouse(funds, rates, margin, positions, nav, active_engine)
        dq = run_data_quality(active_engine, etl_run_id=run_id)

        liquidity = liquidity_bucket_exposure(positions)
        stress = calculate_rate_stress(positions, nav)
        execute_sql("DELETE FROM warehouse.fact_liquidity_metric", engine=active_engine)
        execute_sql("DELETE FROM warehouse.fact_rate_stress", engine=active_engine)
        append_dataframe(liquidity, "fact_liquidity_metric", "warehouse", active_engine)
        append_dataframe(stress, "fact_rate_stress", "warehouse", active_engine)

        report_paths: list[str] = []
        for fund_id in positions["fund_id"].unique():
            report = build_liquidity_report(fund_id, positions, nav, funds)
            paths = write_liquidity_report(report, get_settings().outputs_dir)
            report_paths.extend(str(path.relative_to(get_settings().project_root)) for path in paths)

        source_modes = sorted(
            set(funds["source_mode"]) | set(rates["source_mode"]) | set(margin["source_mode"]) | set(raw_positions["source_mode"])
        )
        records_written = ods_written + warehouse_written + len(liquidity) + len(stress)
        final_status = "SUCCESS" if dq["status"] == "PASS" else "COMPLETED_WITH_DQ_ERRORS"
        execute_sql(
            """
            UPDATE warehouse.etl_run_log
            SET completed_at=:completed_at, status=:status, records_read=:records_read,
                records_written=:records_written, dq_issue_count=:dq_issue_count,
                source_modes=:source_modes
            WHERE run_id=:run_id
            """,
            {
                "completed_at": datetime.now(UTC).replace(tzinfo=None), "status": final_status,
                "records_read": records_read, "records_written": records_written,
                "dq_issue_count": dq["issue_count"], "source_modes": json.dumps(source_modes),
                "run_id": run_id,
            }, active_engine,
        )
        return {
            "run_id": run_id, "status": final_status, "records_read": records_read,
            "records_written": records_written, "source_modes": source_modes,
            "data_quality": dq, "reports": report_paths,
        }
    except Exception as exc:
        LOGGER.exception("ETL run %s failed", run_id)
        execute_sql(
            """
            UPDATE warehouse.etl_run_log
            SET completed_at=:completed_at, status='FAILED', error_message=:error_message
            WHERE run_id=:run_id
            """,
            {"completed_at": datetime.now(UTC).replace(tzinfo=None), "error_message": str(exc)[:2000], "run_id": run_id},
            active_engine,
        )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LiquidityFlow daily ETL")
    parser.add_argument("--refresh-public", action="store_true", help="Attempt official public-source downloads")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    result = run_pipeline(use_network=args.refresh_public)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
