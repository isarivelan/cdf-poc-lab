"""Map fired rules to safety-approved recommendation templates."""

from __future__ import annotations

from typing import Any

from maintenance_investigator.investigation.context_builder import ContextPackage
from maintenance_investigator.models.investigation import RecommendedAction
from maintenance_investigator.paths import load_yaml


def _evidence_for_source(context: ContextPackage, source: str) -> list[str]:
    matches = [item.evidence_id for item in context.evidence if item.source_id == source]
    if matches:
        return matches[:2]
    incident_ids = [item.evidence_id for item in context.evidence if item.source_type == "incident"]
    return incident_ids[:1]


def select_recommendations(
    context: ContextPackage, config: dict[str, Any]
) -> list[RecommendedAction]:
    """Return template actions for the incident. Every action requires approval."""
    fired = set(context.incident.detection_rules)
    trigger_rules: dict[str, list[str]] = config.get("trigger_rules", {})
    selected: list[RecommendedAction] = []
    alignment_history = any(
        "alignment" in " ".join(item.reasons) or "misalignment" in item.work_order.cause.lower()
        for item in context.work_orders
    )
    for template in config.get("templates", []):
        trigger = str(template["trigger"])
        rules = set(trigger_rules.get(trigger, []))
        if trigger == "high_vibration_and_temperature":
            matched = {
                "DE_VIB_CRITICAL",
                "DE_TEMP_CRITICAL",
            } <= fired or "COMBINED_VIB_TEMP" in fired
        elif trigger == "alignment_history":
            matched = alignment_history
        else:
            matched = bool(rules & fired)
        if not matched:
            continue
        evidence_ids = _evidence_for_source(context, str(template["source"]))
        for action in template["actions"]:
            selected.append(
                RecommendedAction(
                    action=action,
                    priority=template["priority"],
                    reason=f"Template {template['id']} matched trigger {trigger}.",
                    evidence_ids=evidence_ids,
                    requires_human_approval=True,
                    source=str(template["source"]),
                )
            )
    return selected


def load_recommendation_config(path: Any) -> dict[str, Any]:
    """Load config/recommendations.yaml."""
    return load_yaml(path)
