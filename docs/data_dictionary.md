# Data Dictionary

## ODS schema

| Table | Grain | Key fields | Purpose |
|---|---|---|---|
| `ods.fund_reference` | SEC series | `fund_id` | Source-shaped fund and class reference snapshot |
| `ods.treasury_rates` | Date and tenor | `rate_date`, `tenor` | FRED DGS2/DGS10 observations |
| `ods.finra_margin` | Month | `report_month` | FINRA margin balances in $ millions |
| `ods.positions_raw` | Fund/security/date | natural key | Synthetic source position snapshot |
| `ods.fund_nav` | Fund/date | `fund_id`, `nav_date` | Synthetic NAV control total |

## Warehouse schema

| Table | Grain | Important fields |
|---|---|---|
| `warehouse.dim_fund` | Fund | name, class, CIK, ticker, provenance |
| `warehouse.fact_position` | Fund/security/date | quantity, price, market value, asset class, maturity, duration, liquidity |
| `warehouse.fact_fund_nav` | Fund/date | NAV value |
| `warehouse.fact_rate` | Date/tenor | H.15 rate percentage |
| `warehouse.fact_margin_indicator` | Month | debit, free credit, net leverage |
| `warehouse.fact_liquidity_metric` | Fund/date/bucket | market value, exposure percentage |
| `warehouse.fact_rate_stress` | Fund/date/scenario | shock bps, estimated P&L, NAV impact |
| `warehouse.etl_run_log` | ETL run | status, timing, counts, provenance, error |
| `warehouse.dq_issue` | Issue | rule, severity, entity, detail, lineage |
| `warehouse.dq_run_summary` | DQ run/rule | pass/fail and issue count, including clean runs |
| `warehouse.alert` | Alert | severity, type, message, status |

## Position field definitions

| Field | Definition |
|---|---|
| `fund_id` | SEC Series ID used as the synthetic portfolio identifier |
| `security_id` | Synthetic security key; not a CUSIP or proprietary identifier |
| `position_date` | Accounting date of the holding |
| `price_date` | Valuation date of the unit price |
| `quantity` | Position units or par amount |
| `price` | Unit price used for valuation |
| `market_value` | `quantity × price`, in USD for this demonstration |
| `asset_class` | Approved instrument classification |
| `modified_duration` | First-order fixed-income rate sensitivity |
| `days_to_liquidate` | Synthetic liquidation horizon assumption |
| `liquidity_bucket` | Daily, weekly, monthly, or illiquid classification |

## Data quality controls

| Rule | Severity | Control |
|---|---|---|
| DQ001 | Error | Fund ID is populated |
| DQ002 | Error | Security ID is populated |
| DQ003 | Error | Position date is not in the future |
| DQ004 | Error | Market value matches quantity × price within configurable tolerance |
| DQ005 | Error | Fund/security/date natural key is unique |
| DQ006 | Warning | Price is no more than three business days old |
| DQ007 | Error | Bond maturity follows position date |
| DQ008 | Error | Liquidity bucket is assigned |
| DQ009 | Error | Position total reconciles to NAV within configurable tolerance |
| DQ010 | Error | Asset class belongs to the approved domain |
