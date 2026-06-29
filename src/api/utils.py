"""API serialization helpers."""

from __future__ import annotations

import json

import pandas as pd


def dataframe_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Convert a DataFrame to JSON-safe records, preserving nulls."""

    if frame.empty:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))
