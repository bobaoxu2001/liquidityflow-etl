CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_fund (
    fund_id VARCHAR PRIMARY KEY,
    fund_name VARCHAR NOT NULL,
    class_id VARCHAR,
    cik VARCHAR,
    ticker VARCHAR,
    source_mode VARCHAR NOT NULL,
    effective_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_position (
    fund_id VARCHAR NOT NULL,
    security_id VARCHAR NOT NULL,
    position_date DATE NOT NULL,
    price_date DATE NOT NULL,
    security_name VARCHAR NOT NULL,
    issuer_name VARCHAR NOT NULL,
    asset_class VARCHAR NOT NULL,
    quantity DOUBLE NOT NULL,
    price DOUBLE NOT NULL,
    market_value DOUBLE NOT NULL,
    currency VARCHAR NOT NULL,
    coupon_rate DOUBLE,
    maturity_date DATE,
    modified_duration DOUBLE,
    days_to_liquidate INTEGER,
    liquidity_bucket VARCHAR NOT NULL,
    source_mode VARCHAR NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_fund_nav (
    fund_id VARCHAR NOT NULL,
    nav_date DATE NOT NULL,
    nav_value DOUBLE NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_rate (
    rate_date DATE NOT NULL,
    tenor VARCHAR NOT NULL,
    rate_pct DOUBLE,
    source_mode VARCHAR NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_margin_indicator (
    report_month DATE NOT NULL,
    debit_balances_mm DOUBLE,
    free_credit_cash_mm DOUBLE,
    free_credit_margin_mm DOUBLE,
    net_margin_leverage_mm DOUBLE,
    source_mode VARCHAR NOT NULL,
    loaded_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_liquidity_metric (
    metric_date DATE NOT NULL,
    fund_id VARCHAR NOT NULL,
    liquidity_bucket VARCHAR NOT NULL,
    market_value DOUBLE NOT NULL,
    exposure_pct DOUBLE NOT NULL,
    calculated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_rate_stress (
    scenario_date DATE NOT NULL,
    fund_id VARCHAR NOT NULL,
    scenario_bps INTEGER NOT NULL,
    estimated_pnl DOUBLE NOT NULL,
    estimated_nav_impact_pct DOUBLE NOT NULL,
    calculated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.etl_run_log (
    run_id VARCHAR PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR NOT NULL,
    records_read BIGINT DEFAULT 0,
    records_written BIGINT DEFAULT 0,
    dq_issue_count BIGINT DEFAULT 0,
    source_modes VARCHAR,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS warehouse.dq_issue (
    issue_id VARCHAR PRIMARY KEY,
    dq_run_id VARCHAR NOT NULL,
    etl_run_id VARCHAR,
    detected_at TIMESTAMP NOT NULL,
    rule_id VARCHAR NOT NULL,
    rule_name VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    fund_id VARCHAR,
    security_id VARCHAR,
    position_date DATE,
    issue_detail VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dq_run_summary (
    dq_run_id VARCHAR NOT NULL,
    etl_run_id VARCHAR,
    executed_at TIMESTAMP NOT NULL,
    rule_id VARCHAR NOT NULL,
    rule_name VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    issue_count BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.alert (
    alert_id VARCHAR PRIMARY KEY,
    dq_run_id VARCHAR,
    created_at TIMESTAMP NOT NULL,
    severity VARCHAR NOT NULL,
    alert_type VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    status VARCHAR NOT NULL
);
