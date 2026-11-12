"""Rule duration, shutdown exclusion, spikes, and merging."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from maintenance_investigator.constants import (
    ALL_SENSORS,
    CURRENT,
    FLOW,
    SPEED,
    TEMP_DE,
    VIB_DE,
)
from maintenance_investigator.detection.detector import detect
from maintenance_investigator.detection.rules import load_rules
from maintenance_investigator.detection.severity import compute_health_score
from maintenance_investigator.paths import config_dir, load_yaml

pytestmark = pytest.mark.unit

_NORMAL = {
    "P101_VIBRATION_DE_MM_S": 2.6,
    "P101_VIBRATION_NDE_MM_S": 2.3,
    "P101_BEARING_TEMP_DE_C": 58,
    "P101_BEARING_TEMP_NDE_C": 55,
    "P101_DISCHARGE_PRESSURE_BAR": 6.15,
    "P101_SUCTION_PRESSURE_BAR": 1.15,
    "P101_FLOW_M3_H": 100,
    "M101_MOTOR_CURRENT_A": 39,
    "M101_MOTOR_SPEED_RPM": 1490,
    "V101_VALVE_POSITION_PCT": 80,
}


@pytest.fixture(scope="module")
def rules(repo_root):
    return load_rules(config_dir(repo_root) / "anomaly_rules.yaml")


@pytest.fixture(scope="module")
def app_config(repo_root):
    return load_yaml(config_dir(repo_root) / "app.yaml")


def frame(minutes: int, **overrides: object) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=minutes, freq="min", tz="UTC")
    data = {sensor: np.full(minutes, _NORMAL[sensor], dtype=float) for sensor in ALL_SENSORS}
    for key, value in overrides.items():
        data[key] = np.asarray(value, dtype=float)
    return pd.DataFrame(data, index=index)


def rule_intervals(result):
    return [item for item in result.intervals if item.detector == "rules"]


def test_short_warning_does_not_open_incident(rules) -> None:
    values = np.full(30, 2.6)
    values[5:14] = 5.2
    result = detect(frame(30, **{VIB_DE: values}), rules, speed_sensor=SPEED, minimum_speed=1400)
    assert rule_intervals(result) == []


def test_sustained_warning_opens_one_incident(rules) -> None:
    values = np.full(30, 2.6)
    values[5:15] = 5.2
    result = detect(frame(30, **{VIB_DE: values}), rules, speed_sensor=SPEED, minimum_speed=1400)
    intervals = rule_intervals(result)
    assert len(intervals) == 1
    assert intervals[0].severity == "warning"
    assert intervals[0].active_minutes == 10


def test_spike_does_not_create_critical_incident(rules) -> None:
    values = np.full(40, 2.6)
    values[12] = 9.5
    result = detect(frame(40, **{VIB_DE: values}), rules, speed_sensor=SPEED, minimum_speed=1400)
    assert rule_intervals(result) == []


def test_shutdown_excludes_failure_incident(rules) -> None:
    result = detect(
        frame(40, **{VIB_DE: np.full(40, 9.0), TEMP_DE: np.full(40, 90.0), SPEED: np.zeros(40)}),
        rules,
        speed_sensor=SPEED,
        minimum_speed=1400,
    )
    assert rule_intervals(result) == []


def test_same_severity_intervals_merge(rules) -> None:
    values = np.full(50, 2.6)
    values[0:12] = 5.2
    values[22:34] = 5.2
    result = detect(frame(50, **{VIB_DE: values}), rules, speed_sensor=SPEED, minimum_speed=1400)
    assert len(rule_intervals(result)) == 1


def test_large_gap_does_not_merge(rules) -> None:
    values = np.full(60, 2.6)
    values[0:12] = 5.2
    values[40:52] = 5.2
    result = detect(frame(60, **{VIB_DE: values}), rules, speed_sensor=SPEED, minimum_speed=1400)
    assert len(rule_intervals(result)) == 2


def test_severity_increase_opens_a_second_incident(rules) -> None:
    vibration = np.full(40, 2.6)
    vibration[0:15] = 5.2
    vibration[15:25] = 8.0
    result = detect(frame(40, **{VIB_DE: vibration}), rules, speed_sensor=SPEED, minimum_speed=1400)
    severities = [item.severity for item in rule_intervals(result)]
    assert severities == ["warning", "critical"]


def test_normal_operation_has_no_incident(rules) -> None:
    result = detect(frame(30), rules, speed_sensor=SPEED, minimum_speed=1400)
    assert rule_intervals(result) == []


def test_critical_health_score_matches_documented_example(app_config) -> None:
    score = compute_health_score(
        {FLOW: 79},
        {VIB_DE: 8.2, TEMP_DE: 86, CURRENT: 48, FLOW: 81},
        config=app_config,
        severity="critical",
    )
    assert score == 38.0


def test_critical_cap_limits_a_single_signal(app_config) -> None:
    score = compute_health_score(
        {FLOW: 100},
        {VIB_DE: 8.0, TEMP_DE: 60, CURRENT: 39, FLOW: 100},
        config=app_config,
        severity="critical",
    )
    assert score == 45.0
