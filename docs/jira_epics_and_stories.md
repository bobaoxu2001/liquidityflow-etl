# Jira Epics and Stories

This backlog shows how the implementation could be delivered under a conventional SDLC. Story status reflects this repository, not a deployed enterprise environment.

## EPIC LF-100 — Source ingestion and provenance

- **LF-101 — SEC fund reference adapter (Done).** Parse Series/Class IDs and preserve official URL and source mode. Acceptance: duplicate series are removed and required identifiers are normalized.
- **LF-102 — FRED rate adapter (Done).** Reshape DGS2/DGS10 H.15 observations to long form. Acceptance: non-numeric observations are removed and tenor/date are retained.
- **LF-103 — FINRA margin adapter (Done).** Parse the official margin table and calculate net margin leverage. Acceptance: values are numeric and stored in $ millions.
- **LF-104 — Synthetic position generator (Done).** Generate deterministic, multi-asset positions and reconciling NAV. Acceptance: no proprietary data or vendor schema is included.

## EPIC LF-200 — ODS and warehouse

- **LF-201 — ODS schema (Done).** Store source-shaped fund, rate, margin, position, and NAV snapshots.
- **LF-202 — Curated warehouse (Done).** Load fund dimension, facts, operational logs, DQ issues, and alerts.
- **LF-203 — Enterprise database configuration (Design complete).** Support replacement SQLAlchemy URLs. Production acceptance requires approved DB2/Sybase driver, credentials vault, schema migration testing, and dialect-specific DDL.

## EPIC LF-300 — Data quality and controls

- **LF-301 — Row-level completeness and validity (Done).** Implement DQ001–DQ008 and DQ010.
- **LF-302 — Fund-level NAV reconciliation (Done).** Compare grouped position market value to NAV using configurable tolerance.
- **LF-303 — Alert persistence (Done).** Create one high-severity alert per failed error-level rule.
- **LF-304 — Control dashboard (Backlog).** A production UI is deliberately outside this API-first portfolio scope.

## EPIC LF-400 — Liquidity and risk analytics

- **LF-401 — Liquidity ladder (Done).** Calculate market value and exposure percentage by fund/bucket.
- **LF-402 — Concentration monitoring (Done).** Rank issuer and security exposure.
- **LF-403 — Rate stress (Done).** Apply transparent duration-based ±100 bps scenarios.
- **LF-404 — Regulatory-style extract (Done).** Produce JSON and CSV outputs with methodology disclosure.

## EPIC LF-500 — Services and operations

- **LF-501 — FastAPI service (Done).** Publish health, operations, DQ, portfolio, report, and alert routes.
- **LF-502 — CI pipeline (Done).** Compile, test with coverage, and execute the offline ETL smoke path on Python 3.11 and 3.12.
- **LF-503 — Containerized local runtime (Done).** Package the API with a persistent DuckDB volume.
- **LF-504 — Production scheduling (Backlog).** Airflow/Autosys/Control-M scheduling is documented as an integration point, not claimed as implemented.
