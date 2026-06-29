"""Deterministic synthetic portfolio positions shaped like a vendor file.

No BlackRock Aladdin data, schema, credentials, or proprietary information is
used. The module produces an intentionally generic investment-book-of-record
extract for local development and portfolio demonstration.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

SYNTHETIC_SOURCE_MODE = "synthetic_aladdin_style"


def _last_business_day(as_of_date: date | None = None) -> date:
    candidate = pd.Timestamp(as_of_date or date.today())
    if candidate.dayofweek >= 5:
        candidate = candidate - pd.offsets.BDay(1)
    return candidate.date()


def generate_aladdin_positions(
    as_of_date: date | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate clean synthetic positions and a reconciling fund NAV file."""

    position_date = _last_business_day(as_of_date)
    price_date = position_date
    ingested_at = datetime.now(UTC).replace(tzinfo=None)
    funds = [
        ("S000009117", 1.00),
        ("S000006806", 0.82),
        ("S000009227", 1.18),
    ]
    templates = [
        {
            "security_id": "USD-CASH",
            "security_name": "US Dollar Cash",
            "issuer_name": "Cash",
            "asset_class": "Cash",
            "quantity": 8_000_000,
            "price": 1.0,
            "coupon_rate": None,
            "maturity_date": None,
            "modified_duration": 0.0,
            "days_to_liquidate": 0,
            "liquidity_bucket": "Daily Liquid",
        },
        {
            "security_id": "UST-2031",
            "security_name": "US Treasury Note 2031",
            "issuer_name": "United States Treasury",
            "asset_class": "Government Bond",
            "quantity": 180_000,
            "price": 98.50,
            "coupon_rate": 3.875,
            "maturity_date": date(2031, 6, 30),
            "modified_duration": 4.6,
            "days_to_liquidate": 1,
            "liquidity_bucket": "Daily Liquid",
        },
        {
            "security_id": "CORP-TECH-2029",
            "security_name": "Technology Corp 4.50% 2029",
            "issuer_name": "Technology Corp",
            "asset_class": "Corporate Bond",
            "quantity": 95_000,
            "price": 101.25,
            "coupon_rate": 4.50,
            "maturity_date": date(2029, 9, 15),
            "modified_duration": 2.9,
            "days_to_liquidate": 3,
            "liquidity_bucket": "Weekly Liquid",
        },
        {
            "security_id": "CORP-UTILITY-2034",
            "security_name": "Utility Holdings 5.10% 2034",
            "issuer_name": "Utility Holdings",
            "asset_class": "Corporate Bond",
            "quantity": 72_000,
            "price": 99.10,
            "coupon_rate": 5.10,
            "maturity_date": date(2034, 3, 1),
            "modified_duration": 6.1,
            "days_to_liquidate": 7,
            "liquidity_bucket": "Weekly Liquid",
        },
        {
            "security_id": "EQ-LARGE-1",
            "security_name": "Large Cap Equity A",
            "issuer_name": "Large Cap Issuer A",
            "asset_class": "Equity",
            "quantity": 120_000,
            "price": 186.40,
            "coupon_rate": None,
            "maturity_date": None,
            "modified_duration": 0.0,
            "days_to_liquidate": 1,
            "liquidity_bucket": "Daily Liquid",
        },
        {
            "security_id": "EQ-LARGE-2",
            "security_name": "Large Cap Equity B",
            "issuer_name": "Large Cap Issuer B",
            "asset_class": "Equity",
            "quantity": 88_000,
            "price": 142.75,
            "coupon_rate": None,
            "maturity_date": None,
            "modified_duration": 0.0,
            "days_to_liquidate": 2,
            "liquidity_bucket": "Daily Liquid",
        },
        {
            "security_id": "MUNI-2036",
            "security_name": "Metro Revenue Bond 2036",
            "issuer_name": "Metro Transit Authority",
            "asset_class": "Municipal Bond",
            "quantity": 45_000,
            "price": 102.20,
            "coupon_rate": 4.25,
            "maturity_date": date(2036, 1, 1),
            "modified_duration": 7.2,
            "days_to_liquidate": 12,
            "liquidity_bucket": "Monthly Liquid",
        },
        {
            "security_id": "ALT-INFRA-1",
            "security_name": "Private Infrastructure Vehicle",
            "issuer_name": "Infrastructure Sponsor LP",
            "asset_class": "Alternative",
            "quantity": 1,
            "price": 5_500_000,
            "coupon_rate": None,
            "maturity_date": None,
            "modified_duration": 0.0,
            "days_to_liquidate": 120,
            "liquidity_bucket": "Illiquid",
        },
    ]

    records: list[dict[str, object]] = []
    for fund_id, scale in funds:
        for template in templates:
            quantity = float(template["quantity"]) * scale
            price = float(template["price"])
            records.append(
                {
                    "fund_id": fund_id,
                    "position_date": position_date,
                    "price_date": price_date,
                    **template,
                    "quantity": quantity,
                    "price": price,
                    "market_value": round(quantity * price, 2),
                    "currency": "USD",
                    "source_mode": SYNTHETIC_SOURCE_MODE,
                    "ingested_at": ingested_at,
                }
            )

    positions = pd.DataFrame.from_records(records)
    nav = (
        positions.groupby("fund_id", as_index=False)["market_value"]
        .sum()
        .rename(columns={"market_value": "nav_value"})
    )
    nav["nav_date"] = position_date
    nav["source_mode"] = SYNTHETIC_SOURCE_MODE
    nav["ingested_at"] = ingested_at
    return positions, nav[["fund_id", "nav_date", "nav_value", "source_mode", "ingested_at"]]
