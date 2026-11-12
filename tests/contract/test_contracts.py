"""Repository and provider contracts."""

from __future__ import annotations

import os

import pytest

from maintenance_investigator.clients.ai_client import InvestigationProvider, MockInvestigator
from maintenance_investigator.clients.local_repository import LocalRepository
from maintenance_investigator.models.investigation import InvestigationResponse

pytestmark = pytest.mark.unit


def _cdf_ready() -> bool:
    return bool(
        os.getenv("CDF_PROJECT") and os.getenv("CDF_CLIENT_ID") and os.getenv("CDF_CLIENT_SECRET")
    )


def test_local_repository_matches_master_data_contract(repo_root) -> None:
    repository = LocalRepository(repo_root)
    assets = repository.list_assets()
    sensors = repository.list_sensors()
    orders = repository.list_work_orders()
    assert any(item.external_id == "PUMP-P101" for item in assets)
    assert len(sensors) == 10
    assert {item.external_id for item in orders} >= {f"WO-2025-00{index}" for index in range(1, 6)}


def test_mock_provider_satisfies_protocol() -> None:
    provider: InvestigationProvider = MockInvestigator()
    assert provider.name == "mock"


def test_response_schema_round_trip() -> None:
    payload = {
        "investigation_summary": "Review required.",
        "observed_facts": [],
        "hypotheses": [],
        "recommended_actions": [],
        "safety_notes": ["POC decision-support output."],
        "limitations": ["Synthetic."],
    }
    assert (
        InvestigationResponse.model_validate(payload).model_dump()["investigation_summary"]
        == "Review required."
    )


@pytest.mark.cdf
@pytest.mark.skipif(not _cdf_ready(), reason="CDF credentials are not configured")
def test_cdf_credentials_are_optional() -> None:
    """Placeholder kept skipped until a development project is configured."""
    assert _cdf_ready()
