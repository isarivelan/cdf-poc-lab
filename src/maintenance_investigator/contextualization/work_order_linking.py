"""Rank historical work orders from structured fields."""

from __future__ import annotations

import math
import re

from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.models.work_order import RankedWorkOrder, WorkOrder
from maintenance_investigator.utils.dates import to_utc

_COMPONENTS: dict[str, set[str]] = {
    "bearing": {"bearing", "lubrication", "overheating"},
    "alignment": {"alignment", "misalignment", "coupling", "vibration"},
    "flow": {"flow", "valve", "restriction", "cavitation"},
    "motor": {"motor", "current"},
}

_RULE_COMPONENTS: dict[str, set[str]] = {
    "DE_VIB_WARNING": {"bearing", "alignment"},
    "DE_VIB_CRITICAL": {"bearing", "alignment"},
    "DE_TEMP_WARNING": {"bearing"},
    "DE_TEMP_CRITICAL": {"bearing"},
    "FLOW_WARNING": {"flow"},
    "FLOW_CRITICAL": {"flow"},
    "CURRENT_WARNING": {"bearing", "motor"},
    "COMBINED_VIB_TEMP": {"bearing"},
    "MULTI_WARNING": set(),
}

_EMPTY = {"", "none", "n/a", "na"}


def incident_components(rule_ids: list[str]) -> set[str]:
    """Map detection rules to component families."""
    found: set[str] = set()
    for rule_id in rule_ids:
        found.update(_RULE_COMPONENTS.get(rule_id, set()))
    return found


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _components(text: str) -> set[str]:
    tokens = _tokens(text)
    return {name for name, words in _COMPONENTS.items() if tokens & words}


def _present(value: str) -> bool:
    return value.strip().lower() not in _EMPTY


def score_work_order(
    work_order: WorkOrder,
    incident: MaintenanceIncident,
    *,
    related_equipment: set[str],
) -> RankedWorkOrder:
    """Score one work order. Structured fields dominate; title text is not used."""
    reasons: list[str] = []
    score = 0.0
    if work_order.equipment == incident.equipment:
        score += 40
        reasons.append("same asset")
    elif work_order.equipment in related_equipment:
        score += 12
        reasons.append("related equipment")
    incident_parts = incident_components(incident.detection_rules)
    failure_parts = _components(work_order.failure_mode)
    cause_parts = _components(work_order.cause)
    overlap = incident_parts & (failure_parts | cause_parts)
    if overlap:
        score += 20
        reasons.append("shared component " + ", ".join(sorted(overlap)))
    if failure_parts & incident_parts:
        score += 15
        reasons.append("similar failure mode")
    if cause_parts & incident_parts:
        score += 8
        reasons.append("similar recorded cause")
    if "bearing" in overlap and "DE_TEMP_CRITICAL" in incident.detection_rules:
        score += 12
        reasons.append("temperature and bearing history align")
    if work_order.completed_time:
        age_days = max(
            0.0,
            (to_utc(incident.start_time) - to_utc(work_order.completed_time)).total_seconds()
            / 86400,
        )
        recency = 15.0 * max(0.0, 1.0 - age_days / 730.0)
        score += recency
        reasons.append(f"recency {recency:.1f}")
    completeness = 0
    if _present(work_order.failure_mode):
        completeness += 4
    if _present(work_order.cause):
        completeness += 3
    if _present(work_order.corrective_action):
        completeness += 3
    if completeness:
        score += completeness
        reasons.append("work order records the outcome")
    return RankedWorkOrder(work_order=work_order, score=round(score, 2), reasons=reasons)


def rank_work_orders(
    work_orders: list[WorkOrder],
    incident: MaintenanceIncident,
    *,
    related_equipment: set[str],
    limit: int,
) -> list[RankedWorkOrder]:
    """Return the highest-scoring work orders for an incident."""
    ranked = [
        score_work_order(item, incident, related_equipment=related_equipment)
        for item in work_orders
    ]
    ranked.sort(key=lambda item: (-item.score, item.work_order.external_id))
    return ranked[:limit]


def age_penalty_reference(age_days: float) -> float:
    """Expose the recency curve for tests."""
    return 15.0 * max(0.0, 1.0 - age_days / 730.0) if not math.isnan(age_days) else 0.0
