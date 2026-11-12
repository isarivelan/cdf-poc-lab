"""Date, sensor, and severity filters."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st


def render_filters(
    sensors: list[str], min_day: date, max_day: date
) -> tuple[list[str], date, date, list[str]]:
    """Return the selected sensors, date range, and severities."""
    selected_sensors = st.multiselect("Sensors", sensors, default=sensors[:4])
    start, end = st.date_input(
        "Date range", value=(min_day, max_day), min_value=min_day, max_value=max_day
    )
    if isinstance(start, tuple):
        start, end = start
    severities = st.multiselect(
        "Severity", ["warning", "critical"], default=["warning", "critical"]
    )
    return selected_sensors, start, end, severities


def apply_time_filter(frame: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Filter a wide frame by calendar date."""
    stamp = pd.to_datetime(frame["timestamp"], utc=True)
    mask = (stamp.dt.date >= start) & (stamp.dt.date <= end)
    return frame.loc[mask]
