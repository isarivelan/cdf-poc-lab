"""Work-order ranking and manual sections."""

from __future__ import annotations

import pytest

from maintenance_investigator.contextualization.document_linking import parse_manual, rank_sections
from maintenance_investigator.contextualization.work_order_linking import rank_work_orders
from maintenance_investigator.models.incident import MaintenanceIncident
from maintenance_investigator.synthetic.catalog import work_orders

pytestmark = pytest.mark.unit


def _incident() -> MaintenanceIncident:
    return MaintenanceIncident(
        external_id="INC-P101-20261111-2000",
        title="High vibration and temperature detected on Pump P-101",
        start_time="2026-11-11T20:00:00Z",
        end_time="2026-11-11T23:59:00Z",
        severity="critical",
        status="open",
        equipment="PUMP-P101",
        detection_rules=[
            "DE_VIB_CRITICAL",
            "DE_TEMP_CRITICAL",
            "FLOW_CRITICAL",
            "CURRENT_WARNING",
            "COMBINED_VIB_TEMP",
        ],
        health_score=38,
        summary="Test incident",
    )


def test_bearing_and_alignment_history_rank_first() -> None:
    ranked = rank_work_orders(
        work_orders(),
        _incident(),
        related_equipment={"MOTOR-M101", "VALVE-V101", "BEARING-P101-DE", "BEARING-P101-NDE"},
        limit=5,
    )
    assert ranked[0].work_order.external_id == "WO-2025-001"
    top = {item.work_order.external_id for item in ranked[:3]}
    assert "WO-2025-002" in top
    assert ranked[0].score > ranked[-1].score


def test_manual_sections_are_linked(repo_root) -> None:
    text = (repo_root / "data" / "source" / "maintenance_manual_p101.md").read_text(
        encoding="utf-8"
    )
    document = parse_manual(text)
    assert "SYNTHETIC DEMONSTRATION CONTENT" in text
    passages = rank_sections(document, _incident(), limit=6, passage_chars=400)
    section_ids = {item.section_id for item in passages}
    assert "SEC-VIBRATION-001" in section_ids
    assert "SEC-BEARING-001" in section_ids
    assert all(item.passage for item in passages)
