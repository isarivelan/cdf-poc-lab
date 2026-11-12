"""Rolling features that describe change without using labels."""

from __future__ import annotations

import numpy as np
import pandas as pd

from maintenance_investigator.detection.rules import RuleSet


def rate_of_change(frame: pd.DataFrame, rules: RuleSet) -> pd.DataFrame:
    """Return per-minute change over the configured window."""
    features = pd.DataFrame(index=frame.index)
    for sensor in rules.rate_sensors:
        if sensor not in frame.columns:
            continue
        features[f"{sensor}_roc"] = frame[sensor].diff(rules.rate_window_minutes)
    return features


def modified_zscore_mask(
    series: pd.Series,
    *,
    window: int,
    min_periods: int,
    threshold: float,
) -> pd.Series:
    """Flag points with a robust modified z-score above ``threshold``.

    The statistic is ``0.6745 * (x - rolling median) / rolling MAD``.
    It is reported separately from the rule detector.
    """
    median = series.rolling(window, min_periods=min_periods).median()
    mad = (series - median).abs().rolling(window, min_periods=min_periods).median()
    scale = mad.where(mad > 1e-9)
    score = 0.6745 * (series - median) / scale
    return score.abs() > threshold


def statistical_masks(
    frame: pd.DataFrame, rules: RuleSet, operating: pd.Series
) -> dict[str, pd.Series]:
    """Return statistical masks for configured sensors. These do not open incidents."""
    if not rules.statistical_enabled:
        return {}
    masks: dict[str, pd.Series] = {}
    for sensor in rules.statistical_sensors:
        if sensor not in frame.columns:
            continue
        flagged = modified_zscore_mask(
            frame[sensor],
            window=rules.statistical_window,
            min_periods=rules.statistical_min_periods,
            threshold=rules.statistical_z,
        )
        masks[sensor] = flagged.fillna(False) & operating.reindex(frame.index).fillna(False)
    return masks


def correlation_snapshot(frame: pd.DataFrame, columns: list[str]) -> dict[str, float]:
    """Pairwise Pearson correlations for finite overlapping samples."""
    present = [column for column in columns if column in frame.columns]
    if len(present) < 2:
        return {}
    subset = frame[present].dropna()
    if len(subset) < 5:
        return {}
    matrix = subset.corr(numeric_only=True)
    pairs: dict[str, float] = {}
    for left_index, left in enumerate(present):
        for right in present[left_index + 1 :]:
            value = matrix.loc[left, right]
            if pd.notna(value):
                pairs[f"{left}|{right}"] = round(float(value), 3)
    return pairs


def trend_label(values: np.ndarray, *, higher_is_worse: bool) -> str:
    """Compare the early and late parts of a window."""
    finite = values[np.isfinite(values)]
    if finite.size < 4:
        return "insufficient"
    split = max(1, finite.size // 5)
    early = float(np.mean(finite[:split]))
    late = float(np.mean(finite[-split:]))
    delta = late - early
    if abs(delta) < max(0.02, 0.01 * abs(early)):
        return "flat"
    worsening = delta > 0 if higher_is_worse else delta < 0
    return "worsening" if worsening else "improving"
