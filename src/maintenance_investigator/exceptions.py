"""Domain errors. Messages name the failure, a likely cause, and a safe action."""

from __future__ import annotations


class MaintenanceInvestigatorError(Exception):
    """Base error for the maintenance investigator."""

    def __init__(self, message: str, *, likely_cause: str = "", action: str = "") -> None:
        self.message = message
        self.likely_cause = likely_cause
        self.action = action
        parts = [message]
        if likely_cause:
            parts.append(f"Likely cause: {likely_cause}")
        if action:
            parts.append(f"Action: {action}")
        super().__init__(" ".join(parts))


class ConfigurationError(MaintenanceInvestigatorError):
    """The process cannot start with the current configuration."""


class DataQualityError(MaintenanceInvestigatorError):
    """Sample or operational data failed a quality check."""


class DetectionError(MaintenanceInvestigatorError):
    """Anomaly detection could not be completed."""


class IngestionError(MaintenanceInvestigatorError):
    """A write to the local store or CDF did not complete."""


class AiProviderError(MaintenanceInvestigatorError):
    """The investigation model did not return a usable response."""


class CitationError(MaintenanceInvestigatorError):
    """A model response cited evidence that was not supplied."""


class OperationalSafetyError(MaintenanceInvestigatorError):
    """A requested action would control equipment or bypass approval."""


class CdfAuthenticationError(MaintenanceInvestigatorError):
    """CDF rejected or could not start authentication."""


class ResourceNotFoundError(MaintenanceInvestigatorError):
    """A requested asset, series, document, or incident is not in the repository."""
