"""Cognite Function entry point for incident investigation."""

from __future__ import annotations

from typing import Any


def handle(data: dict[str, Any], client: Any) -> dict[str, Any]:
    """Build an investigation when the package is installed in the function bundle."""
    del client
    if data.get("ping"):
        return {"status": "ok"}
    try:
        from maintenance_investigator.functions_api import investigate_for_function
    except ImportError:
        return {
            "status": "failed",
            "message": "maintenance_investigator is not installed in the function bundle.",
            "action": "Vendor the package before deploying the function.",
        }
    return investigate_for_function(data)
