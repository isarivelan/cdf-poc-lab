"""Investigation response schema. Hypotheses are not physical diagnoses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SourceType = Literal["time_series", "incident", "asset", "work_order", "document"]
Priority = Literal["immediate", "high", "medium", "low"]

_FORBIDDEN_PHRASES = (
    "bypass safety",
    "disable interlock",
    "skip lockout",
    "ignore the procedure",
    "ignore site procedure",
)


class ObservedFact(BaseModel):
    """A claim tied to a supplied source."""

    fact: str
    source_type: SourceType
    source_id: str
    timestamp_or_section: str


class Hypothesis(BaseModel):
    """An unverified explanation. It is not a confirmed diagnosis."""

    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    verification_steps: list[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    """A decision-support action that still requires a person."""

    action: str
    priority: Priority
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)
    requires_human_approval: bool
    source: str = ""

    @field_validator("requires_human_approval")
    @classmethod
    def _approval(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Operational actions require human approval.")
        return value

    @field_validator("action")
    @classmethod
    def _no_bypass(cls, value: str) -> str:
        lowered = value.lower()
        if any(phrase in lowered for phrase in _FORBIDDEN_PHRASES):
            raise ValueError("The action asks to bypass a safety procedure.")
        return value


class InvestigationResponse(BaseModel):
    """Strict investigator payload."""

    investigation_summary: str
    observed_facts: list[ObservedFact]
    hypotheses: list[Hypothesis]
    recommended_actions: list[RecommendedAction]
    safety_notes: list[str]
    limitations: list[str]


class EvidenceItem(BaseModel):
    """One retrievable piece of evidence."""

    evidence_id: str
    source_type: SourceType
    source_id: str
    timestamp_or_section: str
    text: str
    category: str


class InvestigationRecord(BaseModel):
    """Persisted investigation metadata plus the validated response."""

    external_id: str
    incident: str
    equipment: str
    generated_time: str
    confidence: float
    model_information: str
    response: InvestigationResponse
    notification: dict[str, object] = Field(default_factory=dict)
