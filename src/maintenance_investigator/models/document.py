"""Technical document sections."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    """One stable section of a technical document."""

    section_id: str
    title: str
    text: str


class TechnicalDocument(BaseModel):
    """Document metadata and parsed sections."""

    external_id: str
    title: str
    document_type: str
    revision: str
    effective_date: str
    equipment: str
    path: str = ""
    sections: list[DocumentSection] = Field(default_factory=list)


class DocumentPassage(BaseModel):
    """A short passage selected as evidence."""

    document_external_id: str
    section_id: str
    title: str
    passage: str
    relevance_reason: str
    score: float
