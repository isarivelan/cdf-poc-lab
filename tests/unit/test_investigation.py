"""AI schema, citation checks, and recommendation approval."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from maintenance_investigator.clients.ai_client import MockInvestigator
from maintenance_investigator.exceptions import CitationError, OperationalSafetyError
from maintenance_investigator.investigation.context_builder import ContextPackage
from maintenance_investigator.investigation.evidence import assert_citations
from maintenance_investigator.investigation.investigator import Investigator
from maintenance_investigator.investigation.recommendations import select_recommendations
from maintenance_investigator.models.asset import Asset, AssetContext
from maintenance_investigator.models.incident import MaintenanceIncident, SensorExtreme
from maintenance_investigator.models.investigation import (
    EvidenceItem,
    InvestigationResponse,
    ObservedFact,
    RecommendedAction,
)
from maintenance_investigator.paths import config_dir, load_yaml
from maintenance_investigator.pipeline import DisabledWorkOrderGateway

pytestmark = pytest.mark.unit


def _context() -> ContextPackage:
    incident = MaintenanceIncident(
        external_id="INC-P101-20261111-2000",
        title="High vibration and temperature detected on Pump P-101",
        start_time="2026-11-11T20:00:00Z",
        end_time="2026-11-11T23:59:00Z",
        severity="critical",
        status="open",
        equipment="PUMP-P101",
        detection_rules=["DE_VIB_CRITICAL", "DE_TEMP_CRITICAL", "COMBINED_VIB_TEMP"],
        health_score=38,
        summary="Synthetic incident",
        extremes=[
            SensorExtreme(
                sensor_external_id="P101_VIBRATION_DE_MM_S",
                unit="mm/s",
                minimum=7.5,
                maximum=8.4,
                baseline=2.6,
                deviation=5.8,
                trend="worsening",
            )
        ],
    )
    evidence = [
        EvidenceItem(
            evidence_id="EV-TS-P101-VIBRATION-DE-MM-S-02",
            source_type="time_series",
            source_id="P101_VIBRATION_DE_MM_S",
            timestamp_or_section=incident.start_time,
            text="Drive-end vibration rose above 7.1 mm/s.",
            category="observed_fact",
        ),
        EvidenceItem(
            evidence_id="EV-DOC-SEC-VIBRATION-001-03",
            source_type="document",
            source_id="SEC-VIBRATION-001",
            timestamp_or_section="SEC-VIBRATION-001",
            text="Investigate sustained vibration above 4.5 mm/s.",
            category="manual_guidance",
        ),
    ]
    return ContextPackage(
        incident=incident,
        asset=AssetContext(
            equipment=Asset(
                external_id="PUMP-P101",
                name="Cooling Water Pump 101",
                entity_type="equipment",
                criticality="high",
            )
        ),
        work_orders=[],
        passages=[],
        evidence=evidence,
        observed_facts=[
            ObservedFact(
                fact="Drive-end vibration rose above 7.1 mm/s.",
                source_type="time_series",
                source_id="P101_VIBRATION_DE_MM_S",
                timestamp_or_section=incident.start_time,
            )
        ],
    )


def test_mock_response_validates_and_cites_only_known_ids() -> None:
    context = _context()
    body = MockInvestigator().complete_from_context(context)
    parsed = InvestigationResponse.model_validate(body)
    assert_citations(parsed, context.evidence)
    assert parsed.hypotheses[0].confidence <= 0.8
    assert "hypothesis" in parsed.hypotheses[0].hypothesis.lower()


def test_unknown_citation_is_rejected() -> None:
    context = _context()
    body = MockInvestigator().complete_from_context(context)
    body["hypotheses"][0]["supporting_evidence_ids"] = ["EV-DOES-NOT-EXIST"]
    parsed = InvestigationResponse.model_validate(body)
    with pytest.raises(CitationError):
        assert_citations(parsed, context.evidence)


def test_invalid_response_falls_back_after_one_retry(repo_root) -> None:
    class Scripted:
        name = "scripted"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, prompt: dict[str, str], correction: str) -> dict[str, object]:
            del prompt, correction
            self.calls += 1
            if self.calls == 1:
                return {"investigation_summary": "incomplete"}
            return {
                "investigation_summary": "bad citation",
                "observed_facts": [
                    {
                        "fact": "Invented",
                        "source_type": "time_series",
                        "source_id": "NOT-A-SENSOR",
                        "timestamp_or_section": "",
                    }
                ],
                "hypotheses": [],
                "recommended_actions": [],
                "safety_notes": [],
                "limitations": [],
            }

    provider = Scripted()
    config = load_yaml(config_dir(repo_root) / "recommendations.yaml")
    result = Investigator(provider, config).run(_context())
    assert provider.calls == 2
    assert any("validation failed" in item for item in result.limitations)
    assert all(action.requires_human_approval for action in result.recommended_actions)


def test_action_without_approval_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendedAction(
            action="Inspect the coupling.",
            priority="high",
            reason="Test",
            evidence_ids=[],
            requires_human_approval=False,
        )


def test_safety_bypass_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendedAction(
            action="Bypass safety and keep the pump running.",
            priority="high",
            reason="Test",
            evidence_ids=[],
            requires_human_approval=True,
        )


def test_templates_require_approval(repo_root) -> None:
    config = load_yaml(config_dir(repo_root) / "recommendations.yaml")
    actions = select_recommendations(_context(), config)
    assert actions
    assert all(item.requires_human_approval for item in actions)
    assert any(
        "bearing" in item.action.lower() or "vibration" in item.action.lower() for item in actions
    )


def test_work_order_gateway_does_not_create_orders() -> None:
    with pytest.raises(OperationalSafetyError):
        DisabledWorkOrderGateway().submit({"title": "Replace bearing"})
