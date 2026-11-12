"""Cognite Function entry points shared with the Toolkit bundles."""

from maintenance_investigator.functions_api import detect_for_function, investigate_for_function

__all__ = ["detect_for_function", "investigate_for_function"]


def handle(data: dict, client: object) -> dict:
    """Compatibility entry point. The data payload selects the operation."""
    del client
    if data.get("operation") == "investigate":
        return investigate_for_function(data)
    return detect_for_function(data)
