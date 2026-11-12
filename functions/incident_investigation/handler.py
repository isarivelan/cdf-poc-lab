"""Cognite Function entry point for investigation. See the Toolkit bundle for deployment."""

from maintenance_investigator.functions_api import investigate_for_function


def handle(data: dict, client: object) -> dict:
    """Run the investigation entry point."""
    del client
    return investigate_for_function(data)
