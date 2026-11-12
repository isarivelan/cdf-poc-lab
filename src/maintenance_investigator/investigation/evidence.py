"""Evidence identifiers and citation checks."""

from __future__ import annotations

from maintenance_investigator.exceptions import CitationError
from maintenance_investigator.models.investigation import EvidenceItem, InvestigationResponse


def known_ids(evidence: list[EvidenceItem]) -> tuple[set[str], set[str]]:
    """Return source ids and evidence ids that a response is allowed to cite."""
    return {item.source_id for item in evidence}, {item.evidence_id for item in evidence}


def assert_citations(response: InvestigationResponse, evidence: list[EvidenceItem]) -> None:
    """Reject source or evidence ids that were not supplied in the context."""
    sources, evidence_ids = known_ids(evidence)
    unknown_sources = {fact.source_id for fact in response.observed_facts} - sources
    referenced: set[str] = set()
    for hypothesis in response.hypotheses:
        referenced.update(hypothesis.supporting_evidence_ids)
        referenced.update(hypothesis.contradicting_evidence_ids)
    for action in response.recommended_actions:
        referenced.update(action.evidence_ids)
    unknown_evidence = referenced - evidence_ids
    if unknown_sources or unknown_evidence:
        raise CitationError(
            "The investigation cited evidence that was not in the supplied context.",
            likely_cause="A source id or evidence id was invented.",
            action="Retry with the supplied identifiers or use the safe fallback investigation.",
        )
