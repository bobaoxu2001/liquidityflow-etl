CREATE SCHEMA IF NOT EXISTS ods;

CREATE TABLE IF NOT EXISTS ods.fund_reference (
    fund_id VARCHAR NOT NULL,
    class_id VARCHAR,
    cik VARCHAR,
    investment_company_name VARCHAR,
    fund_name VARCHAR NOT NULL,
    class_name VARCHAR,
    ticker VARCHAR,
    organization_type VARCHAR,
    source_mode VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.treasury_rates (
    rate_date DATE NOT NULL,
    tenor VARCHAR NOT NULL,
    rate_pct DOUBLE,
    source_mode VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.finra_margin (
    report_month DATE NOT NULL,
    debit_balances_mm DOUBLE,
    free_credit_cash_mm DOUBLE,
    free_credit_margin_mm DOUBLE,
    net_margin_leverage_mm DOUBLE,
    source_mode VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.positions_raw (
    fund_id VARCHAR,
    security_id VARCHAR,
    position_date DATE,
    price_date DATE,
    security_name VARCHAR,
    issuer_name VARCHAR,
    asset_class VARCHAR,
    quantity DOUBLE,
    price DOUBLE,
    market_value DOUBLE,
    currency VARCHAR,
    coupon_rate DOUBLE,
    maturity_date DATE,
    modified_duration DOUBLE,
    days_to_liquidate INTEGER,
    liquidity_bucket VARCHAR,
    source_mode VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.fund_nav (
    fund_id VARCHAR NOT NULL,
    nav_date DATE NOT NULL,
    nav_value DOUBLE NOT NULL,
    source_mode VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL
);
