"""Deterministic investigator and optional OpenAI-compatible adapter."""

from __future__ import annotations

import json
import logging
from typing import Protocol
from urllib import error, request

from maintenance_investigator.constants import DECISION_SUPPORT_NOTICE, FLOW, TEMP_DE, VALVE, VIB_DE
from maintenance_investigator.exceptions import AiProviderError
from maintenance_investigator.investigation.context_builder import ContextPackage
from maintenance_investigator.models.investigation import Hypothesis, InvestigationResponse

logger = logging.getLogger(__name__)


class InvestigationProvider(Protocol):
    """Provider-independent investigation interface."""

    name: str

    def complete(self, prompt: dict[str, str], correction: str) -> dict[str, object] | str:
        """Return a JSON object or a JSON string matching the investigation schema."""


def _evidence_id(context: ContextPackage, source_id: str) -> str | None:
    for item in context.evidence:
        if item.source_id == source_id:
            return item.evidence_id
    return None


def _extreme(context: ContextPackage, sensor: str) -> object:
    for item in context.incident.extremes:
        if item.sensor_external_id == sensor:
            return item
    return None


class MockInvestigator:
    """Build a schema-valid investigation from supplied evidence only."""

    name = "mock"

    def complete(self, prompt: dict[str, str], correction: str) -> dict[str, object]:
        """Ignore model text and use the context already validated by the caller.

        The prompt is accepted so the provider interface matches the remote adapter.
        This implementation does not read instructions out of document passages.
        """
        del prompt, correction
        raise AiProviderError(
            "MockInvestigator.complete requires complete_from_context.",
            likely_cause="The mock provider was called without the context package.",
            action="Call complete_from_context or use Investigator.run.",
        )

    def complete_from_context(self, context: ContextPackage) -> dict[str, object]:
        """Return the deterministic investigation body."""
        rules = set(context.incident.detection_rules)
        vib = _evidence_id(context, VIB_DE)
        temp = _evidence_id(context, TEMP_DE)
        flow = _evidence_id(context, FLOW)
        valve = _evidence_id(context, VALVE)
        bearing_order = _evidence_id(context, "WO-2025-001")
        alignment_order = _evidence_id(context, "WO-2025-002")
        supporting = [item for item in (vib, temp, bearing_order) if item]
        confidence = 0.42
        if "DE_VIB_CRITICAL" in rules:
            confidence += 0.16
        if "DE_TEMP_CRITICAL" in rules:
            confidence += 0.12
        if bearing_order:
            confidence += 0.08
        confidence = round(min(0.8, confidence), 2)
        valve_extreme = _extreme(context, VALVE)
        valve_normal = False
        if valve_extreme is not None:
            valve_normal = valve_extreme.minimum >= 70 and valve_extreme.maximum <= 90
        hypotheses: list[dict[str, object]] = [
            {
                "hypothesis": (
                    "Hypothesis: drive-end bearing degradation or misalignment. "
                    "This is not a confirmed physical diagnosis."
                ),
                "confidence": confidence,
                "supporting_evidence_ids": supporting,
                "contradicting_evidence_ids": [],
                "verification_steps": [
                    "Compare drive-end and non-drive-end vibration after a planned stop.",
                    "Inspect lubrication condition and drive-end bearing mounting.",
                    "Check coupling alignment with the approved method.",
                ],
            }
        ]
        if alignment_order:
            hypotheses.append(
                {
                    "hypothesis": (
                        "Hypothesis: coupling misalignment is contributing. "
                        "Historical alignment work exists, and this remains unverified."
                    ),
                    "confidence": 0.46,
                    "supporting_evidence_ids": [item for item in (vib, alignment_order) if item],
                    "contradicting_evidence_ids": [],
                    "verification_steps": [
                        "Measure coupling alignment only after isolation and lockout."
                    ],
                }
            )
        if "FLOW_CRITICAL" in rules or "FLOW_WARNING" in rules:
            hypotheses.append(
                {
                    "hypothesis": (
                        "Hypothesis: a flow restriction is contributing. "
                        "Confirm valve position and suction conditions before accepting it."
                    ),
                    "confidence": 0.28,
                    "supporting_evidence_ids": [flow] if flow else [],
                    "contradicting_evidence_ids": [valve] if valve and valve_normal else [],
                    "verification_steps": [
                        "Confirm the discharge valve command and the local position indication."
                    ],
                }
            )
        facts = [fact.model_dump() for fact in context.observed_facts]
        limitations = [
            "Hypotheses are not a confirmed diagnosis and do not replace inspection.",
            "The health score is a transparent penalty model, not a probability of failure.",
            "The statistical detector is reported separately and is not used as a diagnosis.",
        ]
        if context.incident.data_quality_warnings:
            limitations.append("The incident window contains data-quality warnings.")
        return {
            "investigation_summary": (
                f"{context.incident.title} Health score {context.incident.health_score:.0f}. "
                "The most likely hypothesis is drive-end bearing degradation or misalignment, "
                "pending physical verification."
            ),
            "observed_facts": facts,
            "hypotheses": hypotheses,
            "recommended_actions": [],
            "safety_notes": [
                DECISION_SUPPORT_NOTICE,
                "Isolate and lock out the equipment before removing guards "
                "or inspecting the coupling.",
            ],
            "limitations": limitations,
        }


class OpenAICompatibleProvider:
    """Optional chat-completions adapter. Unused when the endpoint or key is empty."""

    name = "openai_compatible"

    def __init__(self, *, endpoint: str, api_key: str, model: str) -> None:
        self.endpoint = endpoint.strip()
        self.api_key = api_key.strip()
        self.model = model.strip() or "gpt-4o-mini"

    def complete(self, prompt: dict[str, str], correction: str) -> str:
        """Call an OpenAI-compatible endpoint and return the message content."""
        if not self.endpoint or not self.api_key:
            raise AiProviderError(
                "The external AI provider is not configured.",
                likely_cause="AI_ENDPOINT or AI_API_KEY is empty.",
                action="Set AI_PROVIDER=mock or provide both AI_ENDPOINT and AI_API_KEY.",
            )
        messages = [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ]
        if correction:
            messages.append({"role": "user", "content": correction})
        body = json.dumps({"model": self.model, "temperature": 0, "messages": messages}).encode(
            "utf-8"
        )
        endpoint = self.endpoint.rstrip("/")
        url = endpoint if endpoint.endswith("/chat/completions") else f"{endpoint}/chat/completions"
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise AiProviderError(
                "The AI endpoint rejected the request.",
                likely_cause=f"HTTP {exc.code}.",
                action="Check the endpoint, model name, and key. The key was not logged.",
            ) from exc
        except error.URLError as exc:
            raise AiProviderError(
                "The AI endpoint could not be reached.",
                likely_cause="A network error occurred.",
                action="Use AI_PROVIDER=mock until the endpoint is reachable.",
            ) from exc
        try:
            return str(payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise AiProviderError(
                "The AI endpoint returned an unexpected payload.",
                likely_cause="The chat-completions body did not contain a message.",
                action="Use an OpenAI-compatible chat endpoint or switch to the mock provider.",
            ) from exc


def fallback_response(context: ContextPackage, reason: str) -> InvestigationResponse:
    """Return a safe investigation that cites only supplied evidence."""
    evidence_ids = [context.evidence[0].evidence_id] if context.evidence else []
    hypotheses: list[Hypothesis] = []
    if evidence_ids:
        hypotheses.append(
            Hypothesis(
                hypothesis="Available evidence is insufficient for an automated hypothesis.",
                confidence=0.2,
                supporting_evidence_ids=evidence_ids,
                contradicting_evidence_ids=[],
                verification_steps=[
                    "Review the incident with a maintenance engineer before any work."
                ],
            )
        )
    return InvestigationResponse(
        investigation_summary=(
            "The model response could not be validated. Use the observed facts and "
            "the deterministic recommendations."
        ),
        observed_facts=list(context.observed_facts[:8]),
        hypotheses=hypotheses,
        recommended_actions=[],
        safety_notes=[DECISION_SUPPORT_NOTICE],
        limitations=[f"Automatic narrative was replaced after validation failed ({reason})."],
    )


def parse_model_json(raw: dict[str, object] | str) -> dict[str, object]:
    """Parse a model payload, including a fenced JSON string."""
    if isinstance(raw, dict):
        return raw
    text = raw.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise json.JSONDecodeError("Expected a JSON object", text, 0)
    return loaded
