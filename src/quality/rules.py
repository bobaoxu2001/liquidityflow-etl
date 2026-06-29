"""pandas-native investment position data quality rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from src.config import get_settings

ALLOWED_ASSET_CLASSES = {
    "Cash", "Government Bond", "Corporate Bond", "Municipal Bond", "Equity",
    "Alternative", "Money Market", "Fund",
}
BOND_ASSET_CLASSES = {"Government Bond", "Corporate Bond", "Municipal Bond"}


@dataclass(frozen=True)
class QualityRule:
    rule_id: str
    name: str
    severity: str
    description: str


RULES = [
    QualityRule("DQ001", "Fund identifier completeness", "ERROR", "fund_id must not be null"),
    QualityRule("DQ002", "Security identifier completeness", "ERROR", "security_id must not be null"),
    QualityRule("DQ003", "Position date validity", "ERROR", "position_date cannot be in the future"),
    QualityRule("DQ004", "Market value calculation", "ERROR", "market value must reconcile to quantity times price"),
    QualityRule("DQ005", "Position uniqueness", "ERROR", "fund, security, and date must be unique"),
    QualityRule("DQ006", "Price freshness", "WARNING", "price must be no more than three business days old"),
    QualityRule("DQ007", "Bond maturity validity", "ERROR", "bond maturity must follow position date"),
    QualityRule("DQ008", "Liquidity classification", "ERROR", "liquidity bucket must be assigned"),
    QualityRule("DQ009", "NAV reconciliation", "ERROR", "position market value must reconcile to fund NAV"),
    QualityRule("DQ010", "Asset class domain", "ERROR", "asset class must be in the approved domain"),
]
RULE_BY_ID = {rule.rule_id: rule for rule in RULES}


def _business_day_age(price_date: object, position_date: object) -> float:
    if pd.isna(price_date) or pd.isna(position_date):
        return np.nan
    start = np.datetime64(pd.Timestamp(price_date).date())
    end = np.datetime64(pd.Timestamp(position_date).date())
    return float(np.busday_count(start, end))


def evaluate_rules(
    positions: pd.DataFrame,
    fund_nav: pd.DataFrame,
    as_of_date: date | None = None,
) -> pd.DataFrame:
    """Evaluate all ten rules and return one normalized row per issue."""

    settings = get_settings()
    frame = positions.copy()
    today = pd.Timestamp(as_of_date or date.today())
    for column in ("position_date", "price_date", "maturity_date"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    issues: list[dict[str, object]] = []

    def add_row_issues(mask: pd.Series, rule_id: str, detail: str) -> None:
        rule = RULE_BY_ID[rule_id]
        for index, row in frame.loc[mask.fillna(False)].iterrows():
            issues.append(
                {
                    "rule_id": rule_id,
                    "rule_name": rule.name,
                    "severity": rule.severity,
                    "fund_id": None if pd.isna(row.get("fund_id")) else str(row.get("fund_id")),
                    "security_id": None if pd.isna(row.get("security_id")) else str(row.get("security_id")),
                    "position_date": row.get("position_date"),
                    "issue_detail": f"row={index}: {detail}",
                }
            )

    add_row_issues(frame["fund_id"].isna() | frame["fund_id"].eq(""), "DQ001", "fund_id is null or blank")
    add_row_issues(frame["security_id"].isna() | frame["security_id"].eq(""), "DQ002", "security_id is null or blank")
    add_row_issues(frame["position_date"] > today, "DQ003", "position_date is in the future")

    expected_value = pd.to_numeric(frame["quantity"], errors="coerce") * pd.to_numeric(frame["price"], errors="coerce")
    actual_value = pd.to_numeric(frame["market_value"], errors="coerce")
    tolerance = np.maximum(1.0, expected_value.abs() * settings.market_value_tolerance_pct)
    add_row_issues((actual_value - expected_value).abs() > tolerance, "DQ004", "market_value differs from quantity * price beyond tolerance")

    duplicates = frame.duplicated(["fund_id", "security_id", "position_date"], keep=False)
    add_row_issues(duplicates, "DQ005", "duplicate natural key")

    ages = pd.Series(
        [_business_day_age(p, d) for p, d in zip(frame["price_date"], frame["position_date"], strict=False)],
        index=frame.index,
    )
    add_row_issues(ages > 3, "DQ006", "price is older than three business days")

    is_bond = frame["asset_class"].isin(BOND_ASSET_CLASSES)
    invalid_maturity = is_bond & (
        frame["maturity_date"].isna() | (frame["maturity_date"] <= frame["position_date"])
    )
    add_row_issues(invalid_maturity, "DQ007", "bond maturity is missing or not after position date")
    add_row_issues(frame["liquidity_bucket"].isna() | frame["liquidity_bucket"].eq(""), "DQ008", "liquidity bucket is unassigned")
    add_row_issues(~frame["asset_class"].isin(ALLOWED_ASSET_CLASSES), "DQ010", "asset class is outside approved domain")

    nav = fund_nav.copy()
    nav["nav_date"] = pd.to_datetime(nav["nav_date"], errors="coerce")
    totals = frame.groupby(["fund_id", "position_date"], dropna=False)["market_value"].sum().reset_index()
    totals["fund_id"] = totals["fund_id"].astype("string")
    nav["fund_id"] = nav["fund_id"].astype("string")
    reconciled = totals.merge(
        nav[["fund_id", "nav_date", "nav_value"]],
        left_on=["fund_id", "position_date"], right_on=["fund_id", "nav_date"], how="left",
    )
    difference_pct = (reconciled["market_value"] - reconciled["nav_value"]).abs() / reconciled["nav_value"].abs().replace(0, np.nan)
    failed = reconciled["nav_value"].isna() | (difference_pct > settings.nav_reconciliation_tolerance_pct)
    rule = RULE_BY_ID["DQ009"]
    for _, row in reconciled.loc[failed].iterrows():
        issues.append(
            {
                "rule_id": "DQ009", "rule_name": rule.name, "severity": rule.severity,
                "fund_id": None if pd.isna(row["fund_id"]) else str(row["fund_id"]),
                "security_id": None, "position_date": row["position_date"],
                "issue_detail": f"positions={row['market_value']}; nav={row['nav_value']}",
            }
        )

    columns = ["rule_id", "rule_name", "severity", "fund_id", "security_id", "position_date", "issue_detail"]
    return pd.DataFrame(issues, columns=columns)
