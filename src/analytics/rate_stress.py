"""First-order fixed-income rate shock analytics."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from src.quality.rules import BOND_ASSET_CLASSES


def calculate_rate_stress(
    positions: pd.DataFrame,
    fund_nav: pd.DataFrame,
    shocks_bps: tuple[int, ...] = (100, -100),
) -> pd.DataFrame:
    """Estimate duration-based P&L for parallel yield-curve shocks.

    The approximation is ``P&L = -modified_duration * delta_yield * market_value``.
    It is intentionally transparent and is not a full pricing model.
    """

    bonds = positions[positions["asset_class"].isin(BOND_ASSET_CLASSES)].copy()
    nav_map = fund_nav.set_index("fund_id")["nav_value"].to_dict()
    scenario_date = pd.to_datetime(positions["position_date"]).max().date()
    now = datetime.now(UTC).replace(tzinfo=None)
    records: list[dict[str, object]] = []
    for fund_id in positions["fund_id"].dropna().unique():
        fund_bonds = bonds[bonds["fund_id"].eq(fund_id)]
        nav = float(nav_map.get(fund_id, 0.0))
        for shock in shocks_bps:
            delta_yield = shock / 10_000
            pnl = float(
                (-fund_bonds["modified_duration"].fillna(0) * delta_yield * fund_bonds["market_value"]).sum()
            )
            records.append(
                {
                    "scenario_date": scenario_date,
                    "fund_id": fund_id,
                    "scenario_bps": shock,
                    "estimated_pnl": round(pnl, 2),
                    "estimated_nav_impact_pct": round(pnl / nav * 100, 6) if nav else 0.0,
                    "calculated_at": now,
                }
            )
    return pd.DataFrame.from_records(records)
