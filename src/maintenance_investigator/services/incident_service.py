"""Create and update maintenance incidents from detection intervals."""

from __future__ import annotations

from typing import Any

import pandas as pd

from maintenance_investigator.constants import (
    CURRENT,
    FLOW,
    PRIMARY_EQUIPMENT,
    SENSOR_UNITS,
    TEMP_DE,
    TEMP_NDE,
    VIB_DE,
    VIB_NDE,
)
from maintenance_investigator.detection.detector import AnomalyInterval, detect
from maintenance_investigator.detection.feature_engineering import trend_label
from maintenance_investigator.detection.rules import RuleSet
from maintenance_investigator.detection.severity import compute_health_score
from maintenance_investigator.ingestion.time_series import to_wide
from maintenance_investigator.models.incident import MaintenanceIncident, SensorExtreme
from maintenance_investigator.utils.dates import to_iso
from maintenance_investigator.utils.identifiers import incident_external_id

_HIGHER_IS_WORSE = {VIB_DE, VIB_NDE, TEMP_DE, CURRENT}
_LOWER_IS_WORSE = {FLOW}


def classic_event_payload(incident: MaintenanceIncident) -> dict[str, object]:
    """Build a classic CDF event body. The caller decides whether to write it."""
    from maintenance_investigator.utils.dates import to_millis

    return {
        "externalId": incident.external_id,
        "type": "maintenance-incident",
        "subtype": incident.severity,
        "description": incident.summary[:500],
        "startTime": to_millis(incident.start_time),
        "endTime": to_millis(incident.end_time),
        "metadata": {
            "equipment": incident.equipment,
            "healthScore": str(incident.health_score),
            "detector": incident.detector,
        },
    }


def _baseline(
    wide: pd.DataFrame,
    sensor: str,
    start: pd.Timestamp,
    *,
    speed_sensor: str,
    minimum_speed: float,
    lookback_hours: int,
) -> float | None:
    cutoff = start - pd.Timedelta(hours=lookback_hours)
    history = wide.loc[wide.index < cutoff]
    if history.empty or sensor not in history.columns:
        return None
    operating = history[speed_sensor] >= minimum_speed
    values = history.loc[operating, sensor].dropna()
    if values.empty:
        return None
    return float(values.median())


def _title(rule_ids: list[str], severity: str) -> str:
    if "DE_VIB_CRITICAL" in rule_ids and "DE_TEMP_CRITICAL" in rule_ids:
        return "High vibration and temperature detected on Pump P-101"
    if severity == "warning" and "DE_VIB_WARNING" in rule_ids:
        return "Sustained drive-end vibration on Pump P-101"
    return f"{severity.title()} equipment condition detected on Pump P-101"


def _summary(
    incident_rules: list[str], duration: int, health: float, extremes: list[SensorExtreme]
) -> str:
    highlights = []
    for item in extremes:
        if item.sensor_external_id in {VIB_DE, TEMP_DE, FLOW, CURRENT}:
            highlights.append(f"{item.sensor_external_id} max {item.maximum:.2f} {item.unit}")
    detail = "; ".join(highlights)
    return (
        f"Rule detector reported {', '.join(incident_rules)} for {duration} minutes. "
        f"Health score {health:.0f}. Observed {detail}. "
        "This is an equipment-condition incident, not a confirmed failure diagnosis."
    )


def build_incidents(
    wide: pd.DataFrame,
    intervals: list[AnomalyInterval],
    *,
    app_config: dict[str, Any],
    speed_sensor: str,
    minimum_speed: float,
) -> list[MaintenanceIncident]:
    """Convert rule intervals into idempotent incident records for Pump P-101."""
    if wide.empty:
        return []
    latest = wide.index.max()
    incidents: list[MaintenanceIncident] = []
    for interval in intervals:
        if interval.detector != "rules":
            continue
        window = wide.loc[interval.start : interval.end]
        operating = window[speed_sensor] >= minimum_speed
        observed = window.loc[operating]
        if observed.empty:
            observed = window
        minimums = {
            column: float(observed[column].min())
            for column in observed.columns
            if observed[column].notna().any()
        }
        maximums = {
            column: float(observed[column].max())
            for column in observed.columns
            if observed[column].notna().any()
        }
        health = compute_health_score(
            minimums, maximums, config=app_config, severity=interval.severity
        )
        extremes: list[SensorExtreme] = []
        affected: list[str] = []
        for sensor in observed.columns:
            if sensor == speed_sensor or sensor not in minimums:
                continue
            baseline = _baseline(
                wide,
                sensor,
                interval.start,
                speed_sensor=speed_sensor,
                minimum_speed=minimum_speed,
                lookback_hours=int(app_config["baseline_lookback_hours"]),
            )
            peak = maximums[sensor]
            trough = minimums[sensor]
            if sensor in _LOWER_IS_WORSE:
                deviation = None if baseline is None else baseline - trough
            else:
                deviation = None if baseline is None else peak - baseline
            trend = trend_label(
                observed[sensor].to_numpy(dtype=float),
                higher_is_worse=sensor not in _LOWER_IS_WORSE,
            )
            if _affected(sensor, trough, peak, app_config["health_thresholds"]):
                affected.append(sensor)
            extremes.append(
                SensorExtreme(
                    sensor_external_id=sensor,
                    unit=SENSOR_UNITS.get(sensor, ""),
                    minimum=round(trough, 3),
                    maximum=round(peak, 3),
                    baseline=None if baseline is None else round(baseline, 3),
                    deviation=None if deviation is None else round(deviation, 3),
                    trend=trend,
                )
            )
        expected = interval.duration_minutes * max(1, len(wide.columns))
        missing = int(window.isna().sum().sum())
        warnings: list[str] = []
        if expected and missing / expected > 0.02:
            warnings.append(f"Missing datapoints in the incident window: {missing}.")
        open_status = interval.end >= latest - pd.Timedelta(minutes=1)
        external_id = incident_external_id(PRIMARY_EQUIPMENT, interval.start.to_pydatetime())
        incidents.append(
            MaintenanceIncident(
                external_id=external_id,
                title=_title(interval.rule_ids, interval.severity),
                start_time=to_iso(interval.start),
                end_time=to_iso(interval.end),
                severity=interval.severity,
                status="open" if open_status else "closed",
                equipment=PRIMARY_EQUIPMENT,
                detection_rules=interval.rule_ids,
                health_score=health,
                summary=_summary(interval.rule_ids, interval.duration_minutes, health, extremes),
                affected_sensors=affected or [VIB_DE],
                extremes=extremes,
                active_minutes=interval.active_minutes,
                duration_minutes=interval.duration_minutes,
                data_quality_warnings=warnings,
                investigation_status="pending",
                detector="rules",
            )
        )
    return incidents


def _affected(sensor: str, minimum: float, maximum: float, thresholds: dict[str, Any]) -> bool:
    if sensor == VIB_DE:
        return maximum >= float(thresholds["vibration_warning"])
    if sensor == TEMP_DE:
        return maximum >= float(thresholds["temperature_warning"])
    if sensor == FLOW:
        return minimum <= float(thresholds["flow_warning"])
    if sensor == CURRENT:
        return maximum >= float(thresholds["current_warning"])
    if sensor in {VIB_NDE, TEMP_NDE}:
        return maximum >= float(
            thresholds["vibration_warning" if sensor == VIB_NDE else "temperature_warning"]
        )
    return False


def detect_incidents(
    frame: pd.DataFrame, *, app_config: dict[str, Any], rules: RuleSet
) -> tuple[pd.DataFrame, list[MaintenanceIncident], list[AnomalyInterval]]:
    """Pivot, detect, and build incidents. Label columns are not used."""
    wide = to_wide(frame) if "sensor_external_id" in frame.columns else frame
    operating = app_config["operating"]
    result = detect(
        wide,
        rules,
        speed_sensor=str(operating["sensor"]),
        minimum_speed=float(operating["minimum"]),
    )
    incidents = build_incidents(
        wide,
        result.intervals,
        app_config=app_config,
        speed_sensor=str(operating["sensor"]),
        minimum_speed=float(operating["minimum"]),
    )
    return wide, incidents, result.statistical_intervals
