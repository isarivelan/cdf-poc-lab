"""Build the compact context package for one incident."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from maintenance_investigator.constants import CURRENT, FLOW, TEMP_DE, VALVE, VIB_DE, VIB_NDE
from maintenance_investigator.contextualization.asset_context import build_asset_context
from maintenance_investigator.contextualization.document_linking import rank_sections
from maintenance_investigator.contextualization.work_order_linking import rank_work_orders
from maintenance_investigator.detection.feature_engineering import correlation_snapshot
from maintenance_investigator.models.asset import Asset, AssetContext
from maintenance_investigator.models.document import DocumentPassage, TechnicalDocument
from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.models.investigation import EvidenceItem, ObservedFact
from maintenance_investigator.models.work_order import RankedWorkOrder, WorkOrder
from maintenance_investigator.utils.dates import to_utc
from maintenance_investigator.utils.identifiers import evidence_id


class ContextPackage(BaseModel):
    """Deterministic context passed to an investigator."""

    incident: MaintenanceIncident
    asset: AssetContext
    work_orders: list[RankedWorkOrder]
    passages: list[DocumentPassage]
    evidence: list[EvidenceItem]
    observed_facts: list[ObservedFact]
    correlations: dict[str, float] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


def _extreme(incident: MaintenanceIncident, sensor: str) -> Any:
    for item in incident.extremes:
        if item.sensor_external_id == sensor:
            return item
    return None


def build_context(
    incident: MaintenanceIncident,
    *,
    assets: list[Asset],
    work_orders: list[WorkOrder],
    document: TechnicalDocument,
    wide: pd.DataFrame,
    app_config: dict[str, Any],
    related_ids: list[str],
) -> ContextPackage:
    """Collect asset, sensor, work-order, and manual evidence within configured limits."""
    limits = app_config["context_limits"]
    asset = build_asset_context(assets, incident.equipment, related_ids)
    ranked = rank_work_orders(
        work_orders,
        incident,
        related_equipment=set(related_ids),
        limit=int(limits["max_work_orders"]),
    )
    passages = rank_sections(
        document,
        incident,
        limit=int(limits["max_document_passages"]),
        passage_chars=int(limits["max_passage_chars"]),
    )
    evidence: list[EvidenceItem] = []
    facts: list[ObservedFact] = []
    sequence = 1
    asset_evidence = evidence_id("ASSET", incident.equipment, sequence)
    evidence.append(
        EvidenceItem(
            evidence_id=asset_evidence,
            source_type="asset",
            source_id=incident.equipment,
            timestamp_or_section="",
            text=(
                f"{asset.equipment.name} ({asset.equipment.manufacturer} {asset.equipment.model}), "
                f"criticality {asset.equipment.criticality}."
            ),
            category="observed_fact",
        )
    )
    facts.append(
        ObservedFact(
            fact=evidence[-1].text,
            source_type="asset",
            source_id=incident.equipment,
            timestamp_or_section=incident.start_time,
        )
    )
    sequence += 1
    incident_evidence = evidence_id("INC", incident.external_id, sequence)
    evidence.append(
        EvidenceItem(
            evidence_id=incident_evidence,
            source_type="incident",
            source_id=incident.external_id,
            timestamp_or_section=incident.start_time,
            text=(
                f"{incident.severity} incident {incident.external_id}. "
                f"Health score {incident.health_score:.0f}."
            ),
            category="observed_fact",
        )
    )
    for sensor in (VIB_DE, VIB_NDE, TEMP_DE, FLOW, CURRENT, VALVE):
        extreme = _extreme(incident, sensor)
        if extreme is None:
            continue
        sequence += 1
        item_id = evidence_id("TS", sensor, sequence)
        text = (
            f"{sensor} ranged from {extreme.minimum:.2f} to {extreme.maximum:.2f} {extreme.unit}"
            + (
                f" against a baseline of {extreme.baseline:.2f}."
                if extreme.baseline is not None
                else "."
            )
            + f" Trend: {extreme.trend}."
        )
        evidence.append(
            EvidenceItem(
                evidence_id=item_id,
                source_type="time_series",
                source_id=sensor,
                timestamp_or_section=incident.start_time,
                text=text,
                category="observed_fact",
            )
        )
        facts.append(
            ObservedFact(
                fact=text,
                source_type="time_series",
                source_id=sensor,
                timestamp_or_section=incident.start_time,
            )
        )
    for ranked_order in ranked:
        sequence += 1
        work_order = ranked_order.work_order
        failure_mode = work_order.failure_mode or "not recorded"
        cause = work_order.cause or "not recorded"
        action = work_order.corrective_action or "not recorded"
        text = (
            f"{work_order.external_id} {work_order.title}. Failure mode: {failure_mode}. "
            f"Cause: {cause}. Action: {action}."
        )
        evidence.append(
            EvidenceItem(
                evidence_id=evidence_id("WO", work_order.external_id, sequence),
                source_type="work_order",
                source_id=work_order.external_id,
                timestamp_or_section=work_order.completed_time,
                text=text,
                category="historical_evidence",
            )
        )
    for passage in passages:
        sequence += 1
        evidence.append(
            EvidenceItem(
                evidence_id=evidence_id("DOC", passage.section_id, sequence),
                source_type="document",
                source_id=passage.section_id,
                timestamp_or_section=passage.section_id,
                text=passage.passage,
                category="manual_guidance",
            )
        )
    fact_limit = int(limits["max_observed_facts"])
    start = to_utc(incident.start_time)
    end = to_utc(incident.end_time)
    window = wide.loc[(wide.index >= start) & (wide.index <= end)]
    correlations = correlation_snapshot(window, [VIB_DE, TEMP_DE, FLOW, CURRENT])
    return ContextPackage(
        incident=incident,
        asset=asset,
        work_orders=ranked,
        passages=passages,
        evidence=evidence,
        observed_facts=facts[:fact_limit],
        correlations=correlations,
        limits={key: int(value) for key, value in limits.items()},
    )
