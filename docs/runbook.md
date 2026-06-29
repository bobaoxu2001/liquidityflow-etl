# Operations Runbook

## Service-level intent

The portfolio implementation models a once-daily post-valuation run. A production schedule would start only after positions, NAV, and pricing controls are complete. No production scheduler is included or claimed.

## Standard local run

```bash
make setup
make etl
make api
```

Use `make etl-public` to attempt current official downloads. The standard `make etl` path uses committed public snapshots so CI and demonstrations do not depend on internet availability.

## Successful-run checks

1. Confirm the command returns `SUCCESS`.
2. Query `warehouse.etl_run_log` for the run ID, counts, and source modes.
3. Confirm DQ status is `PASS` or investigate every issue before distribution.
4. Confirm six files exist in `outputs/`: JSON and CSV for each of three funds.
5. Check `/health`, `/dq/summary`, and one fund report endpoint.

## Failure triage

| Symptom | First check | Recovery |
|---|---|---|
| Public request fails | Adapter warning and timeout | Continue with explicit snapshot or rerun later with `--refresh-public` |
| Pipeline status `FAILED` | `error_message` in run log | Correct source/schema/config issue and rerun; current snapshot loads are idempotent |
| `COMPLETED_WITH_DQ_ERRORS` | `/dq/issues` grouped by rule | Repair source data or approved mapping; do not delete evidence to force a pass |
| DQ006 warnings | `price_date` and holiday calendar | Confirm stale-price policy and approved market calendar |
| DQ009 failures | Position total versus NAV | Check late holdings, cash, FX, and valuation timing |
| Database locked | Active API/test process | Stop competing local DuckDB writers and rerun |

## Alert handling

Each failed error rule creates an open `DATA_QUALITY` alert. This repository stores alerts but does not send email or pages. In production, an alert dispatcher would route high-severity records to the approved support channel and update acknowledgement/resolution status.

## Rerun and recovery

The current ODS and analytical facts use replace-current-snapshot semantics, while ETL logs, DQ issues, and alerts are append-only. A rerun receives a new run ID. For a production historical warehouse, use partition-level merge keys and retention policies rather than full current-table replacement.

## Configuration

Copy `.env.example` values into the shell or deployment environment. Never commit credentials. DB2/Sybase deployment requires an approved SQLAlchemy dialect, driver, encrypted connection, vault-managed secret, DDL compatibility testing, and enterprise change approval.

## Validation commands

```bash
make compile
make test
make coverage
docker compose config
```
