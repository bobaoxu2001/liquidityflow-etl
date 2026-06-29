# Technical Design

## Design goals

The design optimizes for traceability, deterministic local execution, pandas fluency, and credible migration seams. DuckDB supplies a zero-infrastructure analytical database; all application access still passes through SQLAlchemy.

## Component architecture

```text
Official public sources                         Synthetic local source
SEC Series/Class   FRED H.15   FINRA Margin     Aladdin-style positions + NAV
       |               |             |                    |
       +---------------+-------------+--------------------+
                               |
                     Python ingestion adapters
                 (timeouts, validation, provenance,
                    explicit snapshot fallback)
                               |
                        pandas transformations
                               |
                 +-------------+--------------+
                 |                            |
             ODS schema                  DQ rule engine
          source-shaped tables          issue + alert facts
                 |                            |
                 +-------------+--------------+
                               |
                        warehouse schema
           dimensions + positions + market context + run logs
                               |
              liquidity / concentration / rate stress
                               |
          FastAPI REST services + JSON/CSV report artifacts
```

## Daily sequence

1. Create an ETL run record with `RUNNING` status.
2. Read each source; record `official_download`, `official_web_table`, `bundled_public_snapshot`, or `synthetic_aladdin_style`.
3. Replace the current ODS snapshot.
4. Normalize portfolio columns and types with pandas.
5. Replace current curated facts/dimensions while preserving run, issue, and alert history.
6. Evaluate DQ controls and persist issue details.
7. Calculate liquidity and rate stress facts.
8. Write JSON/CSV fund reports.
9. Complete the run as `SUCCESS` or `COMPLETED_WITH_DQ_ERRORS`; on exception, persist `FAILED` and the error message.

## Database strategy

DuckDB is the local backend and implements `ods` and `warehouse` schemas. SQLAlchemy owns engine creation, parameterization, reads, and writes. An enterprise deployment would provide a URL such as an approved DB2 or SAP ASE dialect, install its driver, move secrets to a vault, and validate DDL/type differences through migrations. The repository does not claim a live DB2 or Sybase connection.

## Data quality model

Rules operate on DataFrames because the role emphasizes pandas transformations and because issue rows need portfolio context. Each issue contains rule, severity, fund, security, date, detail, ETL lineage, and DQ run lineage. Error rules generate summarized open alerts; warnings remain visible without escalating the pipeline to failure.

## Analytics methods

- Liquidity exposure is grouped market value divided by total fund market value.
- Concentration is ranked separately by issuer and security.
- Cash and illiquid percentages use explicit asset/bucket labels.
- Rate stress uses first-order modified duration: `-duration × yield shock × market value`. Convexity, optionality, spread shocks, and non-parallel curves are excluded and disclosed.

## Error handling and observability

Adapters use bounded timeouts and log fallback reasons. Pipeline exceptions are logged and persisted. Run counts, source modes, DQ counts, issues, and alerts create a small operational audit trail. A production version would add structured logs, metrics, distributed tracing, alert delivery, and retention policies.

## Security and governance

- No proprietary source or credential is included.
- SEC requests include a configurable user agent.
- SQL values are parameterized at API/query boundaries.
- Network access is opt-in for deterministic default runs.
- Generated reports state that they are demonstrations, not filings or investment advice.
