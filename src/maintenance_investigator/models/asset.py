"""Asset hierarchy records."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """A site, functional location, or equipment node."""

    external_id: str
    name: str
    entity_type: str
    description: str = ""
    parent_external_id: str = ""
    equipment_type: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    installation_date: str = ""
    criticality: str = ""
    status: str = "active"
    functional_location: str = ""


class AssetContext(BaseModel):
    """Equipment plus its location and nearby assets."""

    equipment: Asset
    functional_location: Asset | None = None
    site: Asset | None = None
    related_equipment: list[Asset] = Field(default_factory=list)
