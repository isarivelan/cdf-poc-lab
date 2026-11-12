"""Historical work orders."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WorkOrder(BaseModel):
    """A completed or open maintenance work order."""

    external_id: str
    title: str
    description: str
    work_type: str
    priority: str
    status: str
    opened_time: str
    completed_time: str = ""
    equipment: str
    failure_mode: str = ""
    cause: str = ""
    corrective_action: str = ""
    related_incident: str = ""


class RankedWorkOrder(BaseModel):
    """A work order plus the structured relevance score used for ranking."""

    work_order: WorkOrder
    score: float
    reasons: list[str] = Field(default_factory=list)
