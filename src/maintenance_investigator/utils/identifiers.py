"""Readable external identifiers."""

from __future__ import annotations

import re
from datetime import datetime

from maintenance_investigator.utils.dates import to_utc


def equipment_token(equipment_external_id: str) -> str:
    """Return the short equipment token used in incident ids."""
    parts = [part for part in equipment_external_id.split("-") if part]
    return parts[-1] if parts else equipment_external_id


def incident_external_id(equipment_external_id: str, start: datetime) -> str:
    """Build INC-<token>-YYYYMMDD-HHMM from the incident start."""
    token = equipment_token(equipment_external_id)
    stamp = to_utc(start).strftime("%Y%m%d-%H%M")
    return f"INC-{token}-{stamp}"


def investigation_external_id(incident_external_id_value: str) -> str:
    """Build the investigation id for an incident."""
    return f"INV-{incident_external_id_value}"


def evidence_id(kind: str, source: str, sequence: int) -> str:
    """Build a stable evidence id from a source identifier."""
    safe = re.sub(r"[^A-Za-z0-9]+", "-", source).strip("-")
    return f"EV-{kind}-{safe}-{sequence:02d}"
