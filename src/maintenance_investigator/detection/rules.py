"""Load externalized anomaly rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from maintenance_investigator.exceptions import DetectionError
from maintenance_investigator.paths import load_yaml


@dataclass(frozen=True)
class Condition:
    """One sensor comparison."""

    sensor: str
    comparison: str
    threshold: float


@dataclass(frozen=True)
class Rule:
    """A sustained warning or critical condition."""

    id: str
    severity: str
    duration_minutes: int
    description: str
    kind: str
    conditions: tuple[Condition, ...] = ()
    minimum_count: int = 1


@dataclass(frozen=True)
class RuleSet:
    """Rules plus merge and statistical settings."""

    merge_gap_minutes: int
    rules: tuple[Rule, ...]
    statistical_enabled: bool
    statistical_window: int
    statistical_min_periods: int
    statistical_z: float
    statistical_sensors: tuple[str, ...]
    rate_window_minutes: int
    rate_sensors: tuple[str, ...]


def _condition(raw: dict[str, object]) -> Condition:
    comparison = str(raw["comparison"])
    if comparison not in {">", "<"}:
        raise DetectionError(
            f"Comparison '{comparison}' is not supported.",
            likely_cause="A rule uses a comparison other than > or <.",
            action="Update config/anomaly_rules.yaml.",
        )
    return Condition(
        sensor=str(raw["sensor"]), comparison=comparison, threshold=float(raw["threshold"])
    )


def load_rules(path: Path) -> RuleSet:
    """Load config/anomaly_rules.yaml."""
    raw = load_yaml(path)
    rules: list[Rule] = []
    for item in raw.get("rules", []):
        if not isinstance(item, dict):
            raise DetectionError(
                "A rule entry is not a mapping.",
                likely_cause="config/anomaly_rules.yaml is malformed.",
                action="Restore the rules file.",
            )
        kind = str(item.get("kind", "threshold"))
        if kind == "threshold":
            conditions = (_condition(item),)
        else:
            conditions = tuple(_condition(condition) for condition in item.get("conditions", []))
        rules.append(
            Rule(
                id=str(item["id"]),
                severity=str(item["severity"]),
                duration_minutes=int(item["duration_minutes"]),
                description=str(item.get("description", item["id"])),
                kind=kind,
                conditions=conditions,
                minimum_count=int(item.get("minimum_count", 1)),
            )
        )
    statistical = raw.get("statistical", {})
    rate = raw.get("rate_of_change", {})
    return RuleSet(
        merge_gap_minutes=int(raw.get("merge_gap_minutes", 15)),
        rules=tuple(rules),
        statistical_enabled=bool(statistical.get("enabled", False)),
        statistical_window=int(statistical.get("window_minutes", 180)),
        statistical_min_periods=int(statistical.get("min_periods", 60)),
        statistical_z=float(statistical.get("modified_z", 3.5)),
        statistical_sensors=tuple(statistical.get("sensors", [])),
        rate_window_minutes=int(rate.get("window_minutes", 30)),
        rate_sensors=tuple(rate.get("sensors", [])),
    )
