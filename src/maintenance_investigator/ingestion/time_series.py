"""Pivot sensor extracts and describe batches."""

from __future__ import annotations

import pandas as pd

from maintenance_investigator.exceptions import DataQualityError

_LABELS = {"ground_truth", "label"}


def to_wide(frame: pd.DataFrame) -> pd.DataFrame:
    """Pivot a long sensor table onto a complete one-minute UTC index.

    Ground-truth columns are removed before the pivot so detection cannot see them.
    """
    if frame.empty:
        raise DataQualityError(
            "There are no sensor datapoints to pivot.",
            likely_cause="The time-series extract is empty.",
            action="Generate or ingest sample data, then run detection again.",
        )
    columns = [column for column in frame.columns if column.lower() not in _LABELS]
    working = frame.loc[:, columns].copy()
    working["timestamp"] = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
    if working["timestamp"].isna().any():
        raise DataQualityError(
            "The sensor extract contains an invalid timestamp.",
            likely_cause="A timestamp is blank or not ISO-8601.",
            action="Correct the timestamp and reload the extract.",
        )
    wide = working.pivot_table(
        index="timestamp",
        columns="sensor_external_id",
        values="value",
        aggfunc="mean",
    ).sort_index()
    wide.columns.name = None
    full_index = pd.date_range(wide.index.min(), wide.index.max(), freq="min", tz="UTC")
    return wide.reindex(full_index)
