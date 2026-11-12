"""Parse and rank sections of the synthetic maintenance manual."""

from __future__ import annotations

import re

from maintenance_investigator.contextualization.work_order_linking import incident_components
from maintenance_investigator.models.document import (
    DocumentPassage,
    DocumentSection,
    TechnicalDocument,
)
from maintenance_investigator.models.incident import MaintenanceIncident

_HEADING = re.compile(r"^##\s+(SEC-[A-Z]+-\d+)\s+[—-]\s+(.+?)\s*$", re.MULTILINE)

_SECTION_COMPONENTS: dict[str, set[str]] = {
    "SEC-VIBRATION-001": {"bearing", "alignment"},
    "SEC-TEMPERATURE-001": {"bearing"},
    "SEC-FLOW-001": {"flow"},
    "SEC-ALIGNMENT-001": {"alignment"},
    "SEC-BEARING-001": {"bearing"},
    "SEC-SAFETY-001": {"safety"},
    "SEC-SHUTDOWN-001": {"safety"},
    "SEC-PROCEDURE-001": set(),
    "SEC-REVISION-001": set(),
}


def parse_manual(
    text: str, *, external_id: str = "DOC-P101-MANUAL", equipment: str = "PUMP-P101"
) -> TechnicalDocument:
    """Split the manual on stable section ids."""
    matches = list(_HEADING.finditer(text))
    sections: list[DocumentSection] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(
            DocumentSection(
                section_id=match.group(1),
                title=match.group(2).strip(),
                text=text[start:end].strip(),
            )
        )
    return TechnicalDocument(
        external_id=external_id,
        title="Cooling Water Pump P-101 Maintenance Manual",
        document_type="maintenance_manual",
        revision="Demo-A",
        effective_date="2025-01-15",
        equipment=equipment,
        path="data/source/maintenance_manual_p101.md",
        sections=sections,
    )


def _trim(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    clipped = compact[:limit].rsplit(" ", 1)[0]
    return clipped + "..."


def rank_sections(
    document: TechnicalDocument,
    incident: MaintenanceIncident,
    *,
    limit: int,
    passage_chars: int,
) -> list[DocumentPassage]:
    """Select manual sections from component overlap, not from a free-text search alone."""
    components = incident_components(incident.detection_rules)
    ranked: list[DocumentPassage] = []
    for section in document.sections:
        section_parts = _SECTION_COMPONENTS.get(section.section_id, set())
        overlap = components & section_parts
        score = 10.0 * len(overlap)
        reason = ""
        if overlap:
            reason = "section covers " + ", ".join(sorted(overlap))
        if section.section_id == "SEC-SAFETY-001":
            score += 4
            reason = reason or "safety guidance applies to every recommendation"
        if section.section_id == "SEC-SHUTDOWN-001" and incident.severity == "critical":
            score += 6
            reason = reason or "critical limits are referenced by the shutdown section"
        if score <= 0:
            continue
        ranked.append(
            DocumentPassage(
                document_external_id=document.external_id,
                section_id=section.section_id,
                title=section.title,
                passage=_trim(section.text, passage_chars),
                relevance_reason=reason,
                score=score,
            )
        )
    ranked.sort(key=lambda item: (-item.score, item.section_id))
    return ranked[:limit]
