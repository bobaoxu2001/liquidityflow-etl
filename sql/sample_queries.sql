-- Latest operational ETL runs
SELECT run_id, started_at, completed_at, status, records_read, records_written,
       dq_issue_count, source_modes
FROM warehouse.etl_run_log
ORDER BY started_at DESC
LIMIT 20;

-- Fund liquidity ladder
SELECT f.fund_name, m.metric_date, m.liquidity_bucket,
       ROUND(m.market_value, 2) AS market_value,
       ROUND(m.exposure_pct, 2) AS exposure_pct
FROM warehouse.fact_liquidity_metric m
JOIN warehouse.dim_fund f USING (fund_id)
ORDER BY f.fund_name, m.exposure_pct DESC;

-- Current concentration by issuer
WITH issuer_exposure AS (
    SELECT fund_id, issuer_name, SUM(market_value) AS issuer_market_value
    FROM warehouse.fact_position
    GROUP BY fund_id, issuer_name
), totals AS (
    SELECT fund_id, SUM(issuer_market_value) AS portfolio_market_value
    FROM issuer_exposure
    GROUP BY fund_id
)
SELECT i.fund_id, i.issuer_name, i.issuer_market_value,
       100.0 * i.issuer_market_value / t.portfolio_market_value AS exposure_pct
FROM issuer_exposure i
JOIN totals t USING (fund_id)
ORDER BY i.fund_id, exposure_pct DESC;

-- Latest data quality pass/fail summary (including a clean run)
SELECT rule_id, rule_name, severity, status, issue_count
FROM warehouse.dq_run_summary
WHERE dq_run_id = (
    SELECT dq_run_id FROM warehouse.dq_run_summary ORDER BY executed_at DESC LIMIT 1
)
ORDER BY rule_id;

-- Rate stress impact by fund
SELECT fund_id, scenario_bps, estimated_pnl, estimated_nav_impact_pct
FROM warehouse.fact_rate_stress
ORDER BY fund_id, scenario_bps DESC;
