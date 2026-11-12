"""Identifier generation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from maintenance_investigator.utils.identifiers import (
    evidence_id,
    incident_external_id,
    investigation_external_id,
)

pytestmark = pytest.mark.unit


def test_incident_external_id() -> None:
    start = datetime(2026, 11, 11, 20, 0, tzinfo=UTC)
    assert incident_external_id("PUMP-P101", start) == "INC-P101-20261111-2000"


def test_investigation_and_evidence_ids() -> None:
    assert investigation_external_id("INC-P101-20261111-2000") == "INV-INC-P101-20261111-2000"
    assert evidence_id("DOC", "SEC-VIBRATION-001", 3) == "EV-DOC-SEC-VIBRATION-001-03"
