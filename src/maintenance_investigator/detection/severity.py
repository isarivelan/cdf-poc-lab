"""Transparent equipment health score from 0 to 100."""

from __future__ import annotations

from typing import Any

from maintenance_investigator.constants import CURRENT, FLOW, TEMP_DE, VIB_DE


def _band(value: float, critical: float, warning: float, *, low_is_bad: bool) -> str:
    if low_is_bad:
        if value <= critical:
            return "critical"
        if value <= warning:
            return "warning"
        return "normal"
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "normal"


def compute_health_score(
    minimums: dict[str, float],
    maximums: dict[str, float],
    *,
    config: dict[str, Any],
    severity: str,
) -> float:
    """Apply the documented penalty table and severity cap.

    The score starts at 100. Each signal contributes its warning deduction or its
    critical deduction, never both. Three or more signals add the breadth penalty.
    Critical windows are then capped, and the result is clamped to 0–100.
    This is a rule penalty, not a probability of failure.
    """
    deductions = config["health_deductions"]
    thresholds = config["health_thresholds"]
    caps = config["health_caps"]
    score = 100.0
    signals = 0
    checks = (
        (maximums.get(VIB_DE), "vibration", False),
        (maximums.get(TEMP_DE), "temperature", False),
        (minimums.get(FLOW), "flow", True),
        (maximums.get(CURRENT), "current", False),
    )
    for value, name, low_is_bad in checks:
        if value is None:
            continue
        band = _band(
            float(value),
            float(thresholds[f"{name}_critical"]),
            float(thresholds[f"{name}_warning"]),
            low_is_bad=low_is_bad,
        )
        if band == "normal":
            continue
        signals += 1
        score -= float(deductions[f"{name}_{band}"])
    if signals >= 3:
        score -= float(deductions["multi_signal"])
    if severity in caps:
        score = min(score, float(caps[severity]))
    return float(max(0.0, min(100.0, round(score, 1))))


def severity_for_window(
    minimums: dict[str, float], maximums: dict[str, float], config: dict[str, Any]
) -> str:
    """Classify a window with the same bands used by the health score."""
    thresholds = config["health_thresholds"]
    bands = [
        _band(
            maximums[VIB_DE],
            thresholds["vibration_critical"],
            thresholds["vibration_warning"],
            low_is_bad=False,
        )
        if VIB_DE in maximums
        else "normal",
        _band(
            maximums[TEMP_DE],
            thresholds["temperature_critical"],
            thresholds["temperature_warning"],
            low_is_bad=False,
        )
        if TEMP_DE in maximums
        else "normal",
        _band(
            minimums[FLOW], thresholds["flow_critical"], thresholds["flow_warning"], low_is_bad=True
        )
        if FLOW in minimums
        else "normal",
        _band(
            maximums[CURRENT],
            thresholds["current_critical"],
            thresholds["current_warning"],
            low_is_bad=False,
        )
        if CURRENT in maximums
        else "normal",
    ]
    if "critical" in bands:
        return "critical"
    if "warning" in bands:
        return "warning"
    return "normal"
