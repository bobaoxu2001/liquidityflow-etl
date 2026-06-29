"""FastAPI contract smoke tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.etl.run_pipeline import run_pipeline


def test_health_and_portfolio_endpoints(isolated_engine) -> None:
    run_pipeline(use_network=False, engine=isolated_engine)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        funds = client.get("/funds")
        assert funds.status_code == 200
        assert len(funds.json()) >= 3

        fund_id = "S000009117"
        assert client.get(f"/portfolio/{fund_id}/positions").status_code == 200
        assert client.get(f"/portfolio/{fund_id}/liquidity").status_code == 200
        assert client.get(f"/portfolio/{fund_id}/rate-stress").status_code == 200
        report = client.get(f"/regulatory/liquidity-report/{fund_id}")
        assert report.status_code == 200
        assert report.json()["fund"]["fund_id"] == fund_id
        csv_report = client.get(f"/regulatory/liquidity-report/{fund_id}?format=csv")
        assert csv_report.status_code == 200
        assert "text/csv" in csv_report.headers["content-type"]


def test_dq_and_alert_endpoints(isolated_engine) -> None:
    run_pipeline(use_network=False, engine=isolated_engine)
    with TestClient(app) as client:
        dq_run = client.post("/dq/run")
        assert dq_run.status_code == 200
        assert dq_run.json()["status"] == "PASS"
        summary = client.get("/dq/summary")
        assert summary.status_code == 200
        assert len(summary.json()) == 10
        assert client.get("/dq/issues").json() == []
        assert client.get("/alerts").json() == []


def test_unknown_fund_returns_404(isolated_engine) -> None:
    run_pipeline(use_network=False, engine=isolated_engine)
    with TestClient(app) as client:
        assert client.get("/portfolio/UNKNOWN/positions").status_code == 404
