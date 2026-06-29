# Business Requirements

## Purpose

LiquidityFlow ETL demonstrates a controlled daily investment-management data workflow. It combines fund reference data, market context, synthetic portfolio positions, data quality controls, liquidity analytics, rate stress, operational lineage, and downstream reporting behind a REST API.

## Business problem

Investment teams depend on multiple sources that arrive at different frequencies and under different ownership. A late price, duplicated position, missing security identifier, or NAV mismatch can undermine portfolio oversight and regulatory reporting. The platform must make the daily process repeatable, observable, and explainable.

## Stakeholders

| Stakeholder | Need |
|---|---|
| Portfolio operations | Reconciled daily positions and NAV |
| Liquidity risk | Exposure by liquidity bucket and illiquid percentage |
| Market risk | Transparent parallel-rate stress results |
| Data governance | Rule-level issues, lineage, and source provenance |
| Regulatory reporting | Reproducible JSON and CSV liquidity output |
| Production support | Run status, errors, alerts, and recovery steps |

## Functional requirements

1. Ingest SEC Series/Class, FRED H.15-style rates, FINRA margin statistics, and synthetic position/NAV files.
2. Record whether each public source came from an official download or a bundled public snapshot.
3. Normalize data with pandas and load separate ODS and warehouse schemas.
4. Evaluate ten required data quality rules and persist issue-level detail.
5. Produce alert records for error-level rule failures.
6. Calculate liquidity, concentration, cash, illiquid exposure, and ±100 bps rate stress metrics.
7. Expose operational, DQ, fund, position, liquidity, stress, report, and alert endpoints.
8. Generate one JSON and one CSV liquidity report per synthetic fund.

## Non-functional requirements

- Python 3.11 or later; typed, modular, logged, and testable code.
- Deterministic offline execution for CI and interview demonstrations.
- Network failures must degrade to explicit snapshots, never silently pretend to be live.
- SQL access must use SQLAlchemy so an approved enterprise dialect can replace DuckDB.
- No proprietary portfolio data, credentials, or Aladdin intellectual property.
- The daily local run should complete in under one minute on a developer laptop.

## Acceptance criteria

- `make etl` completes with a persisted successful run and six report files.
- All ten DQ rules are covered by tests; the standard synthetic portfolio passes all rules.
- `make test` passes from a clean environment.
- All documented endpoints return a valid response after one ETL run.
- The README distinguishes official downloads, bundled snapshots, and synthetic data.

## Out of scope

Trade execution, official regulatory filing, investment advice, proprietary Aladdin integration, intraday pricing, derivatives pricing, authentication/authorization, and production orchestration are outside this portfolio implementation.
