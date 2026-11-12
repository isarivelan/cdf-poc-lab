"""Callable entry points for Cognite Functions."""

from __future__ import annotations

from typing import Any

from maintenance_investigator.paths import find_repo_root
from maintenance_investigator.pipeline import run_local_pipeline


def detect_for_function(data: dict[str, Any]) -> dict[str, Any]:
    """Run the local detection pipeline and return incident ids."""
    del data
    result = run_local_pipeline(find_repo_root())
    return {
        "status": "ok",
        "incidents": [item.external_id for item in result.incidents],
        "health_score": result.health_score,
    }


def investigate_for_function(data: dict[str, Any]) -> dict[str, Any]:
    """Return the latest investigation summary."""
    result = run_local_pipeline(find_repo_root())
    wanted = str(data.get("incident_external_id", ""))
    records = result.investigations
    if wanted:
        records = [item for item in records if item.incident == wanted] or records
    if not records:
        return {"status": "empty", "message": "No incidents were detected."}
    record = records[-1]
    return {
        "status": "ok",
        "incident_external_id": record.incident,
        "summary": record.response.investigation_summary,
        "requires_human_approval": True,
    }
