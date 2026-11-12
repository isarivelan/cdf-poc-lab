"""Deterministic Pump P-101 sensor history."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from maintenance_investigator.constants import (
    ALL_SENSORS,
    CURRENT,
    DISCHARGE_P,
    FLOW,
    RANDOM_SEED,
    SENSOR_UNITS,
    SPEED,
    SUCTION_P,
    TEMP_DE,
    TEMP_NDE,
    VALVE,
    VIB_DE,
    VIB_NDE,
)
from maintenance_investigator.synthetic.catalog import (
    assets_frame,
    failure_events,
    sensors_frame,
    work_orders_frame,
)

START = pd.Timestamp("2026-10-29T00:00:00Z")
PERIODS = 14 * 24 * 60
SHUTDOWN_START = pd.Timestamp("2026-11-04T02:00:00Z")
SHUTDOWN_END = pd.Timestamp("2026-11-04T06:00:00Z")
STARTUP_END = pd.Timestamp("2026-11-04T06:20:00Z")
SPIKE_AT = pd.Timestamp("2026-11-01T12:00:00Z")
BUMP_START = pd.Timestamp("2026-11-08T10:00:00Z")
BUMP_END = pd.Timestamp("2026-11-08T10:25:00Z")
DEGRADE_START = pd.Timestamp("2026-11-10T00:00:00Z")
CRITICAL_START = pd.Timestamp("2026-11-11T20:00:00Z")


def timeline(periods: int = PERIODS) -> pd.DatetimeIndex:
    """Return the one-minute UTC timeline."""
    return pd.date_range(START, periods=periods, freq="min", tz="UTC")


def _clip_noise(base: np.ndarray, noise: np.ndarray, low: float, high: float) -> np.ndarray:
    return np.clip(base + noise, low, high)


def generate_wide(
    seed: int = RANDOM_SEED, periods: int | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate wide sensor values and a ground-truth label per timestamp.

    The full demo uses 14 days. Tests may pass a shorter ``periods`` value only
    when they do not depend on the scripted calendar windows.
    """
    if periods is not None and periods != PERIODS:
        index = pd.date_range(START, periods=periods, freq="min", tz="UTC")
    else:
        index = timeline()
    count = len(index)
    rng = np.random.default_rng(seed)
    hour = index.hour.to_numpy() + index.minute.to_numpy() / 60.0
    daily = np.sin(2.0 * np.pi * hour / 24.0)
    shutdown = (index >= SHUTDOWN_START) & (index < SHUTDOWN_END)
    startup = (index >= SHUTDOWN_END) & (index < STARTUP_END)
    spike = index == SPIKE_AT
    bump = (index >= BUMP_START) & (index <= BUMP_END)
    degrade = (index >= DEGRADE_START) & (index < CRITICAL_START)
    critical = index >= CRITICAL_START
    labels = np.full(count, "normal", dtype=object)
    labels[shutdown] = "shutdown"
    labels[bump] = "warning"
    labels[critical] = "critical"
    labels[spike] = "data_quality_issue"

    vib_de = _clip_noise(2.6 + 0.22 * daily, rng.normal(0, 0.08, count), 2.0, 3.4)
    vib_nde = _clip_noise(2.3 + 0.18 * daily, rng.normal(0, 0.07, count), 1.8, 3.1)
    temp_de = _clip_noise(58 + 2.0 * daily, rng.normal(0, 0.4, count), 52, 66)
    temp_nde = _clip_noise(55 + 1.5 * daily, rng.normal(0, 0.35, count), 50, 64)
    discharge = _clip_noise(6.15 + 0.04 * daily, rng.normal(0, 0.03, count), 5.9, 6.4)
    suction = _clip_noise(1.15, rng.normal(0, 0.015, count), 1.0, 1.3)
    flow = _clip_noise(100 + 2.5 * daily, rng.normal(0, 0.6, count), 92, 108)
    current = _clip_noise(39.2 + 0.4 * daily, rng.normal(0, 0.15, count), 37, 42)
    speed = _clip_noise(1490, rng.normal(0, 1.5, count), 1482, 1498)
    valve = _clip_noise(80 + daily, rng.normal(0, 0.4, count), 74, 86)

    vib_de[shutdown] = 0.3
    vib_nde[shutdown] = 0.25
    temp_de[shutdown] = 36
    temp_nde[shutdown] = 35
    discharge[shutdown] = 0.4
    suction[shutdown] = 0.3
    flow[shutdown] = 0.0
    current[shutdown] = 1.5
    speed[shutdown] = 0.0
    valve[shutdown] = 0.0

    startup_index = np.flatnonzero(startup)
    if len(startup_index):
        ramp = np.linspace(0, 1, len(startup_index))
        speed[startup_index] = 200 + ramp * 1280
        flow[startup_index] = ramp * 95
        current[startup_index] = 8 + ramp * 30
        valve[startup_index] = 20 + ramp * 60
        vib_de[startup_index] = 2.2 + ramp * 0.8
        temp_de[startup_index] = 40 + ramp * 16

    vib_de[spike] = 9.2
    vib_de[bump] = 5.2

    degrade_index = np.flatnonzero(degrade)
    if len(degrade_index):
        progress = np.linspace(0, 1, len(degrade_index))
        vib_de[degrade_index] = 3.6 + progress * 2.8
        vib_nde[degrade_index] = 2.6 + progress * 0.8
        temp_de[degrade_index] = 68 + progress * 10
        temp_nde[degrade_index] = 60 + progress * 5
        flow[degrade_index] = 98 - progress * 4
        current[degrade_index] = 40.5 + progress * 1.5
        discharge[degrade_index] = 6.1 + rng.normal(0, 0.04, len(degrade_index))
        labels[degrade_index[vib_de[degrade_index] > 4.5]] = "warning"

    critical_index = np.flatnonzero(critical)
    if len(critical_index):
        progress = np.linspace(0, 1, len(critical_index))
        vib_de[critical_index] = np.clip(
            8.0 + 0.6 * progress + rng.normal(0, 0.05, len(critical_index)), 7.45, 9.3
        )
        vib_nde[critical_index] = np.clip(3.6 + 0.3 * progress, 3.4, 4.2)
        temp_de[critical_index] = np.clip(
            84 + 4 * progress + rng.normal(0, 0.15, len(critical_index)), 83, 90
        )
        temp_nde[critical_index] = 70 + progress * 2
        flow[critical_index] = np.clip(
            80 - 2 * progress + rng.normal(0, 0.15, len(critical_index)), 76, 81
        )
        current[critical_index] = np.clip(
            47.5 + progress + rng.normal(0, 0.08, len(critical_index)), 47.1, 50
        )
        discharge[critical_index] = np.clip(
            6.0 + rng.normal(0, 0.28, len(critical_index)), 5.2, 7.2
        )
        speed[critical_index] = 1492
        valve[critical_index] = 80
        labels[critical_index] = "critical"

    # Early degradation stays below the warning band and keeps the normal label.
    labels[degrade & (vib_de <= 4.5) & (labels != "critical")] = "normal"

    frame = pd.DataFrame(
        {
            VIB_DE: vib_de,
            VIB_NDE: vib_nde,
            TEMP_DE: temp_de,
            TEMP_NDE: temp_nde,
            DISCHARGE_P: discharge,
            SUCTION_P: suction,
            FLOW: flow,
            CURRENT: current,
            SPEED: speed,
            VALVE: valve,
        },
        index=index,
    )
    frame.index.name = "timestamp"
    return frame, pd.Series(labels, index=index, name="ground_truth")


def to_long(wide: pd.DataFrame, labels: pd.Series, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Stack sensors and drop a reproducible slice of normal and shutdown rows."""
    rng = np.random.default_rng(seed + 7)
    frames: list[pd.DataFrame] = []
    candidate = labels.isin(["normal", "shutdown"]).to_numpy()
    for sensor in ALL_SENSORS:
        drop = candidate & (rng.random(len(wide)) < 0.018)
        kept = wide.loc[~drop, [sensor]].copy()
        kept = kept.rename(columns={sensor: "value"})
        kept["sensor_external_id"] = sensor
        kept["unit"] = SENSOR_UNITS[sensor]
        kept["ground_truth"] = labels.loc[kept.index].to_numpy()
        frames.append(kept.reset_index())
    long_frame = pd.concat(frames, ignore_index=True)
    long_frame["timestamp"] = pd.to_datetime(long_frame["timestamp"], utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    long_frame = long_frame[["timestamp", "sensor_external_id", "value", "unit", "ground_truth"]]
    long_frame = long_frame.sort_values(["timestamp", "sensor_external_id"]).reset_index(drop=True)
    long_frame["value"] = long_frame["value"].astype(float).round(4)
    return long_frame


def write_source_files(root: Path) -> None:
    """Write catalog CSV files and leave the manual in place."""
    source = root / "data" / "source"
    source.mkdir(parents=True, exist_ok=True)
    assets_frame().to_csv(source / "assets.csv", index=False)
    sensors_frame().to_csv(source / "sensors.csv", index=False)
    work_orders_frame().to_csv(source / "work_orders.csv", index=False)
    failure_events().to_csv(source / "failure_events.csv", index=False)


def write_generated(root: Path, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Write the long sensor extract and return it."""
    wide, labels = generate_wide(seed=seed)
    long_frame = to_long(wide, labels, seed=seed)
    target = root / "data" / "generated"
    target.mkdir(parents=True, exist_ok=True)
    long_frame.to_csv(target / "pump_sensor_data.csv", index=False)
    return long_frame
