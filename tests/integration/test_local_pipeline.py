"""Local end-to-end investigation."""

from __future__ import annotations

import pytest

from maintenance_investigator.investigation.evidence import assert_citations
from maintenance_investigator.pipeline import run_local_pipeline

pytestmark = pytest.mark.integration


def test_sample_story(pipeline_result) -> None:
    severities = [item.severity for item in pipeline_result.incidents]
    assert "warning" in severities
    assert "critical" in severities
    critical = next(item for item in pipeline_result.incidents if item.severity == "critical")
    assert critical.equipment == "PUMP-P101"
    assert critical.health_score == 38.0
    assert critical.external_id == "INC-P101-20261111-2000"
    assert pipeline_result.health_score == 38.0
    record = next(
        item for item in pipeline_result.investigations if item.incident == critical.external_id
    )
    context = next(
        item
        for item in pipeline_result.contexts
        if item.incident.external_id == critical.external_id
    )
    assert_citations(record.response, context.evidence)
    orders = {item.work_order.external_id for item in context.work_orders}
    assert "WO-2025-001" in orders
    assert "WO-2025-002" in orders
    sections = {item.section_id for item in context.passages}
    assert "SEC-VIBRATION-001" in sections
    assert "SEC-BEARING-001" in sections
    assert record.response.recommended_actions
    assert all(action.requires_human_approval for action in record.response.recommended_actions)
    assert pipeline_result.notification is not None
    assert pipeline_result.notification["incident_external_id"] == critical.external_id
    assert "decision_support" in pipeline_result.notification


def test_pipeline_is_idempotent(repo_root, pipeline_result) -> None:
    second = run_local_pipeline(repo_root)
    assert [item.external_id for item in second.incidents] == [
        item.external_id for item in pipeline_result.incidents
    ]
    assert len(second.investigations) == len(pipeline_result.investigations)
