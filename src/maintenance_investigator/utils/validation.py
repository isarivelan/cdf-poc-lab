"""Data-quality checks for generated and ingested sensor tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from maintenance_investigator.constants import ALL_SENSORS, SENSOR_UNITS
from maintenance_investigator.exceptions import DataQualityError
from maintenance_investigator.paths import config_dir, load_yaml

REQUIRED_COLUMNS = ("timestamp", "sensor_external_id", "value", "unit", "ground_truth")
LABELS = {"normal", "warning", "critical", "shutdown", "data_quality_issue"}
PRODUCTION_MODULES = (
    "detection/rules.py",
    "detection/detector.py",
    "detection/feature_engineering.py",
    "detection/severity.py",
    "services/incident_service.py",
)


def validate_sensor_frame(
    frame: pd.DataFrame, *, ranges: dict[str, list[float]] | None = None
) -> dict[str, Any]:
    """Validate a long sensor table and return quality metrics."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise DataQualityError(
            f"Sensor table is missing columns: {', '.join(missing_columns)}.",
            likely_cause="The generator or extract did not write the expected schema.",
            action="Regenerate sample data with scripts/01_generate_sample_data.py.",
        )
    if frame.empty:
        raise DataQualityError(
            "Sensor table is empty.",
            likely_cause="No datapoints were generated or loaded.",
            action="Generate sample data before running detection.",
        )
    timestamps = pd.to_datetime(frame["timestamp"], utc=True)
    ordered = timestamps.is_monotonic_increasing or timestamps.sort_values().is_monotonic_increasing
    if not bool(ordered):
        raise DataQualityError(
            "Sensor timestamps could not be ordered.",
            likely_cause="Timestamp values are invalid.",
            action="Regenerate sample data.",
        )
    duplicates = int(frame.duplicated(["timestamp", "sensor_external_id"]).sum())
    if duplicates:
        raise DataQualityError(
            f"Found {duplicates} duplicate timestamp and sensor combinations.",
            likely_cause="The same minute was written more than once for a sensor.",
            action="Regenerate sample data. Ingestion upserts by external id and timestamp.",
        )
    unknown = sorted(set(frame["sensor_external_id"]) - set(ALL_SENSORS))
    if unknown:
        raise DataQualityError(
            f"Unknown sensors: {', '.join(unknown)}.",
            likely_cause="A sensor external id is not part of the Pump P-101 model.",
            action="Use the sensor ids declared in the generator.",
        )
    unit_mismatch = frame.loc[
        frame.apply(lambda row: SENSOR_UNITS.get(row["sensor_external_id"]) != row["unit"], axis=1)
    ]
    if not unit_mismatch.empty:
        raise DataQualityError(
            "One or more sensors use an unexpected engineering unit.",
            likely_cause="Unit labels drifted from the sensor catalog.",
            action="Regenerate sample data.",
        )
    range_map = ranges or {}
    out_of_range = 0
    for sensor, bounds in range_map.items():
        subset = frame.loc[frame["sensor_external_id"] == sensor, "value"]
        if subset.empty:
            continue
        low, high = float(bounds[0]), float(bounds[1])
        out_of_range += int(((subset < low) | (subset > high)).sum())
    if out_of_range:
        raise DataQualityError(
            f"Found {out_of_range} values outside the configured engineering ranges.",
            likely_cause="The generator produced a physically implausible value.",
            action="Regenerate sample data and inspect config/app.yaml quality_ranges.",
        )
    labels = set(frame["ground_truth"].unique())
    if not LABELS <= labels:
        raise DataQualityError(
            f"Ground-truth labels are incomplete: {sorted(labels)}.",
            likely_cause="A scenario window was not generated.",
            action="Regenerate sample data with the fixed random seed.",
        )
    expected = len(frame["timestamp"].drop_duplicates()) * len(ALL_SENSORS)
    present = len(frame)
    missing_percent = 100.0 * (expected - present) / expected if expected else 0.0
    return {
        "rows": present,
        "expected_rows": expected,
        "missing_percent": round(missing_percent, 3),
        "duplicate_count": duplicates,
        "out_of_range_count": out_of_range,
        "labels": sorted(labels),
        "sensors": sorted(frame["sensor_external_id"].unique()),
    }


def assert_missing_percent(metrics: dict[str, Any], bounds: dict[str, float]) -> None:
    """Fail when the missing-data rate is outside the demo band."""
    missing = float(metrics["missing_percent"])
    low = float(bounds["minimum"])
    high = float(bounds["maximum"])
    if missing < low or missing > high:
        raise DataQualityError(
            f"Missing-data percentage is {missing}, outside {low}-{high}.",
            likely_cause="The generator dropped too many or too few points.",
            action="Regenerate sample data without changing the seed.",
        )


def assert_detection_ignores_labels(root: Path) -> None:
    """Fail if production detection modules mention ground-truth labels."""
    package = root / "src" / "maintenance_investigator"
    offenders: list[str] = []
    for relative in PRODUCTION_MODULES:
        lines = (package / relative).read_text(encoding="utf-8").splitlines()
        for line in lines:
            lowered = line.lower()
            if "ground_truth" not in lowered and "ground truth" not in lowered:
                continue
            if any(
                token in lowered for token in ("drop", "exclude", "label_columns", "not consumed")
            ):
                continue
            offenders.append(f"{relative}: {line.strip()}")
    if offenders:
        raise DataQualityError(
            "Production detection code references ground-truth labels.",
            likely_cause=f"Found references in {', '.join(offenders)}.",
            action="Remove label columns before detection and keep them in validation only.",
        )


def quality_report(frame: pd.DataFrame, root: Path | None = None) -> dict[str, Any]:
    """Validate a frame against config/app.yaml and the detection-source rule."""
    from maintenance_investigator.paths import find_repo_root

    project = root or find_repo_root()
    app_config = load_yaml(config_dir(project) / "app.yaml")
    metrics = validate_sensor_frame(frame, ranges=app_config["quality_ranges"])
    assert_missing_percent(metrics, app_config["expected_missing_percent"])
    assert_detection_ignores_labels(project)
    metrics["detection_reads_labels"] = False
    return metrics
