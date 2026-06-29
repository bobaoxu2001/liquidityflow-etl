"""Unit tests for all required DQ controls."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.quality.rules import evaluate_rules


def clean_position() -> dict[str, object]:
    position_date = date.today() - timedelta(days=1)
    return {
        "fund_id": "S000009117", "security_id": "BOND-1",
        "position_date": position_date, "price_date": position_date,
        "security_name": "Test Bond", "issuer_name": "Test Issuer",
        "asset_class": "Corporate Bond", "quantity": 100.0, "price": 99.0,
        "market_value": 9_900.0, "currency": "USD", "coupon_rate": 4.0,
        "maturity_date": date.today() + timedelta(days=365), "modified_duration": 2.0,
        "days_to_liquidate": 2, "liquidity_bucket": "Weekly Liquid",
    }


def nav_for(positions: pd.DataFrame, override: float | None = None) -> pd.DataFrame:
    return pd.DataFrame(
        [{
            "fund_id": "S000009117",
            "nav_date": positions.iloc[0]["position_date"],
            "nav_value": override if override is not None else positions["market_value"].sum(),
        }]
    )


def rule_ids(positions: pd.DataFrame, nav: pd.DataFrame | None = None) -> set[str]:
    return set(evaluate_rules(positions, nav if nav is not None else nav_for(positions))["rule_id"])


def test_clean_position_passes_all_rules() -> None:
    positions = pd.DataFrame([clean_position()])
    assert evaluate_rules(positions, nav_for(positions)).empty


def test_required_identifiers_and_future_date_are_flagged() -> None:
    row = clean_position()
    row.update({"fund_id": None, "security_id": None, "position_date": date.today() + timedelta(days=1)})
    positions = pd.DataFrame([row])
    nav = pd.DataFrame([{"fund_id": None, "nav_date": row["position_date"], "nav_value": row["market_value"]}])
    assert {"DQ001", "DQ002", "DQ003"}.issubset(rule_ids(positions, nav))


def test_market_value_and_duplicate_rules_are_flagged() -> None:
    row = clean_position()
    row["market_value"] = 1.0
    positions = pd.DataFrame([row, row])
    assert {"DQ004", "DQ005"}.issubset(rule_ids(positions))


def test_stale_price_and_invalid_maturity_are_flagged() -> None:
    row = clean_position()
    row["price_date"] = pd.Timestamp(row["position_date"]) - pd.offsets.BDay(4)
    row["maturity_date"] = row["position_date"]
    positions = pd.DataFrame([row])
    assert {"DQ006", "DQ007"}.issubset(rule_ids(positions))


def test_liquidity_nav_and_asset_domain_are_flagged() -> None:
    row = clean_position()
    row["liquidity_bucket"] = None
    row["asset_class"] = "Cryptonite"
    positions = pd.DataFrame([row])
    assert {"DQ008", "DQ009", "DQ010"}.issubset(rule_ids(positions, nav_for(positions, override=20_000)))
