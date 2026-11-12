"""Rule-based anomaly intervals for operating equipment."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from maintenance_investigator.detection.feature_engineering import rate_of_change, statistical_masks
from maintenance_investigator.detection.rules import Condition, Rule, RuleSet
from maintenance_investigator.exceptions import DetectionError

_LABEL_COLUMNS = {"ground_truth", "label"}  # exclude labels; they are not consumed


@dataclass
class AnomalyInterval:
    """A sustained, possibly merged, anomalous window."""

    start: pd.Timestamp
    end: pd.Timestamp
    severity: str
    rule_ids: list[str]
    active_minutes: int
    detector: str = "rules"

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start) / pd.Timedelta(minutes=1)) + 1


@dataclass
class DetectionResult:
    """Rule incidents and separate statistical signals."""

    intervals: list[AnomalyInterval] = field(default_factory=list)
    statistical_intervals: list[AnomalyInterval] = field(default_factory=list)
    features: pd.DataFrame | None = None


def boolean_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Return inclusive start and end indexes of consecutive true values."""
    if mask.size == 0:
        return []
    padded = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    starts = np.flatnonzero(padded == 1)
    ends = np.flatnonzero(padded == -1) - 1
    return list(zip(starts.tolist(), ends.tolist(), strict=True))


def sustained_mask(mask: np.ndarray, duration_minutes: int) -> np.ndarray:
    """Keep only runs that last at least ``duration_minutes``."""
    kept = np.zeros(mask.shape, dtype=bool)
    for start, end in boolean_runs(mask):
        if end - start + 1 >= duration_minutes:
            kept[start : end + 1] = True
    return kept


def _comparison(values: np.ndarray, condition: Condition) -> np.ndarray:
    finite = np.isfinite(values)
    if condition.comparison == ">":
        return finite & (values > condition.threshold)
    return finite & (values < condition.threshold)


def _rule_mask(
    frame: pd.DataFrame, rule: Rule, operating: np.ndarray, warning_masks: list[np.ndarray]
) -> np.ndarray:
    if rule.kind == "count_of_warning_rules":
        if not warning_masks:
            raw = np.zeros(len(frame), dtype=bool)
        else:
            count = np.sum(np.vstack(warning_masks), axis=0)
            raw = count >= rule.minimum_count
        return sustained_mask(raw & operating, rule.duration_minutes)
    if rule.kind == "all_of":
        masks = [
            _comparison(frame[condition.sensor].to_numpy(dtype=float), condition)
            for condition in rule.conditions
        ]
        raw = np.logical_and.reduce(masks) if masks else np.zeros(len(frame), dtype=bool)
        return sustained_mask(raw & operating, rule.duration_minutes)
    condition = rule.conditions[0]
    if condition.sensor not in frame.columns:
        raise DetectionError(
            f"Rule {rule.id} references missing sensor {condition.sensor}.",
            likely_cause="The time-series frame does not contain a configured sensor.",
            action="Load the full Pump P-101 sensor set before detection.",
        )
    raw = _comparison(frame[condition.sensor].to_numpy(dtype=float), condition)
    return sustained_mask(raw & operating, rule.duration_minutes)


def _constant_runs(codes: np.ndarray) -> list[tuple[int, int, int]]:
    """Return inclusive runs of a constant non-zero code."""
    intervals: list[tuple[int, int, int]] = []
    if codes.size == 0:
        return intervals
    start = 0
    for position in range(1, len(codes) + 1):
        if position == len(codes) or codes[position] != codes[start]:
            if int(codes[start]) != 0:
                intervals.append((start, position - 1, int(codes[start])))
            start = position
    return intervals


def _intervals_from_severity(
    index: pd.DatetimeIndex,
    severity_code: np.ndarray,
    rule_ids_by_index: list[list[str]],
    detector: str,
    *,
    low_severity: str = "warning",
) -> list[AnomalyInterval]:
    intervals: list[AnomalyInterval] = []
    for start, end, code in _constant_runs(severity_code):
        collected: list[str] = []
        for position in range(start, end + 1):
            collected.extend(rule_ids_by_index[position])
        intervals.append(
            AnomalyInterval(
                start=index[start],
                end=index[end],
                severity="critical" if code == 2 else low_severity,
                rule_ids=sorted(set(collected)),
                active_minutes=end - start + 1,
                detector=detector,
            )
        )
    return intervals


def merge_intervals(intervals: list[AnomalyInterval], gap_minutes: int) -> list[AnomalyInterval]:
    """Merge same-severity intervals when the idle gap is within ``gap_minutes``."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: (item.start, item.end))
    merged: list[AnomalyInterval] = [ordered[0]]
    for item in ordered[1:]:
        current = merged[-1]
        gap = int((item.start - current.end) / pd.Timedelta(minutes=1)) - 1
        if (
            item.severity == current.severity
            and item.detector == current.detector
            and gap <= gap_minutes
        ):
            current.end = max(current.end, item.end)
            current.rule_ids = sorted(set(current.rule_ids) | set(item.rule_ids))
            current.active_minutes += item.active_minutes
        else:
            merged.append(item)
    return merged


def detect(
    frame: pd.DataFrame, rules: RuleSet, *, speed_sensor: str, minimum_speed: float
) -> DetectionResult:
    """Detect sustained warning and critical intervals.

    Label columns are dropped and are not read. Planned shutdowns and other
    non-operating minutes cannot open an equipment-failure interval. Isolated
    spikes fail the duration test.
    """
    columns = [column for column in frame.columns if column.lower() not in _LABEL_COLUMNS]
    working = frame.loc[:, columns].copy()
    if speed_sensor not in working.columns:
        raise DetectionError(
            f"Operating sensor {speed_sensor} is missing.",
            likely_cause="Motor speed was not included in the frame.",
            action="Include M101_MOTOR_SPEED_RPM so shutdowns can be excluded.",
        )
    if not isinstance(working.index, pd.DatetimeIndex):
        raise DetectionError(
            "The sensor frame index is not a datetime index.",
            likely_cause="Timestamps were not set as the index.",
            action="Pivot the long table onto a UTC timestamp index before detection.",
        )
    speed = working[speed_sensor].to_numpy(dtype=float)
    operating = np.isfinite(speed) & (speed >= minimum_speed)
    warning_atoms = [
        rule for rule in rules.rules if rule.kind == "threshold" and rule.severity == "warning"
    ]
    other_rules = [rule for rule in rules.rules if rule not in warning_atoms]
    masks: dict[str, np.ndarray] = {}
    warning_masks: list[np.ndarray] = []
    for rule in warning_atoms:
        mask = _rule_mask(working, rule, operating, [])
        masks[rule.id] = mask
        warning_masks.append(mask)
    for rule in other_rules:
        masks[rule.id] = _rule_mask(working, rule, operating, warning_masks)

    severity_code = np.zeros(len(working), dtype=np.int8)
    ids_at: list[list[str]] = [[] for _ in range(len(working))]
    for rule in rules.rules:
        hits = np.flatnonzero(masks[rule.id])
        level = 2 if rule.severity == "critical" else 1
        for position in hits:
            severity_code[position] = max(severity_code[position], level)
            ids_at[position].append(rule.id)
    intervals = _intervals_from_severity(working.index, severity_code, ids_at, "rules")
    intervals = merge_intervals(intervals, rules.merge_gap_minutes)
    minimum_duration = {rule.id: rule.duration_minutes for rule in rules.rules}
    intervals = [
        item
        for item in intervals
        if item.rule_ids
        and item.active_minutes >= min(minimum_duration[rule_id] for rule_id in item.rule_ids)
    ]

    statistical = statistical_masks(working, rules, pd.Series(operating, index=working.index))
    statistical_code = np.zeros(len(working), dtype=np.int8)
    statistical_ids: list[list[str]] = [[] for _ in range(len(working))]
    for sensor, mask in statistical.items():
        for position in np.flatnonzero(mask.to_numpy(dtype=bool)):
            statistical_code[position] = 1
            statistical_ids[position].append(f"STAT:{sensor}")
    statistical_intervals = merge_intervals(
        _intervals_from_severity(
            working.index,
            statistical_code,
            statistical_ids,
            "statistical",
            low_severity="statistical",
        ),
        rules.merge_gap_minutes,
    )
    return DetectionResult(
        intervals=intervals,
        statistical_intervals=statistical_intervals,
        features=rate_of_change(working, rules),
    )
