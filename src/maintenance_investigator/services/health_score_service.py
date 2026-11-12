"""Current equipment health from the latest operating hour."""

from __future__ import annotations

from typing import Any

import pandas as pd

from maintenance_investigator.detection.severity import compute_health_score, severity_for_window


def current_health(wide: pd.DataFrame, app_config: dict[str, Any]) -> float:
    """Score the last 60 operating minutes."""
    operating = app_config["operating"]
    sensor = str(operating["sensor"])
    active = wide.loc[wide[sensor] >= float(operating["minimum"])].tail(60)
    if active.empty:
        return 100.0
    minimums = {
        column: float(active[column].min())
        for column in active.columns
        if active[column].notna().any()
    }
    maximums = {
        column: float(active[column].max())
        for column in active.columns
        if active[column].notna().any()
    }
    severity = severity_for_window(minimums, maximums, app_config)
    return compute_health_score(minimums, maximums, config=app_config, severity=severity)
