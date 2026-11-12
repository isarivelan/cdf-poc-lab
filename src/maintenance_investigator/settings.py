"""Environment-backed settings. Secret values are never included in errors."""

from __future__ import annotations

import os
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from maintenance_investigator.exceptions import ConfigurationError
from maintenance_investigator.paths import find_repo_root

_SECRET_KEYS = ("CDF_CLIENT_SECRET", "AI_API_KEY", "CDF_CLIENT_ID", "CDF_TENANT_ID")


class AppMode(StrEnum):
    """Where operational data is read and written."""

    LOCAL = "local"
    CDF = "cdf"
    HYBRID = "hybrid"


class AiProviderName(StrEnum):
    """Investigation model provider."""

    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"


class Settings(BaseModel):
    """Validated process configuration."""

    app_mode: AppMode = AppMode.LOCAL
    ai_provider: AiProviderName = AiProviderName.MOCK
    ai_model: str = ""
    ai_endpoint: str = ""
    ai_api_key: str = ""
    ai_fallback_reason: str = ""
    log_level: str = "INFO"
    cdf_project: str = ""
    cdf_cluster: str = ""
    cdf_base_url: str = ""
    cdf_tenant_id: str = ""
    cdf_client_id: str = ""
    cdf_client_secret: str = ""
    cdf_token_url: str = ""
    cdf_scopes: str = ""
    cdf_data_set_external_id: str = "cdf-maintenance-investigator-demo"
    cdf_space: str = "cdf_maintenance_demo"
    cdf_instance_space: str = "cdf_maintenance_demo_instances"
    cdf_environment: str = "dev"
    login_flow: str = "client_credentials"
    write_classic_events: bool = False
    confirm_cleanup: bool = False
    repo_root: Path = Field(default_factory=find_repo_root)

    def cdf_required(self) -> bool:
        """Return whether this mode reads or writes CDF."""
        return self.app_mode in {AppMode.CDF, AppMode.HYBRID}

    def base_url(self) -> str:
        """Return the CDF API base URL."""
        if self.cdf_base_url.strip():
            return self.cdf_base_url.strip().rstrip("/")
        if self.cdf_cluster.strip():
            return f"https://{self.cdf_cluster.strip()}.cognitedata.com"
        raise ConfigurationError(
            "CDF cluster or base URL is missing.",
            likely_cause="Both CDF_CLUSTER and CDF_BASE_URL are blank.",
            action="Set CDF_CLUSTER to the tenant cluster or set CDF_BASE_URL.",
        )

    def scopes(self) -> list[str]:
        """Return OAuth scopes split on whitespace."""
        return [item for item in self.cdf_scopes.split() if item.strip()]

    def public_summary(self) -> dict[str, str]:
        """Return a log-safe view of the configuration."""
        summary = {
            "app_mode": self.app_mode.value,
            "ai_provider": self.ai_provider.value,
            "cdf_environment": self.cdf_environment,
            "cdf_project": self.cdf_project or "empty",
            "cdf_cluster": self.cdf_cluster or "empty",
            "login_flow": self.login_flow,
            "ai_fallback_reason": self.ai_fallback_reason,
        }
        for key in _SECRET_KEYS:
            field = key.lower()
            summary[field] = "set" if str(getattr(self, field, "")).strip() else "empty"
        return summary


def _raw(source: Mapping[str, str], key: str) -> str:
    return str(source.get(key, "")).strip()


def _require(source: Mapping[str, str], key: str, purpose: str) -> str:
    value = _raw(source, key)
    if not value:
        raise ConfigurationError(
            f"{key} is required for {purpose}.",
            likely_cause=f"{key} is missing or blank.",
            action=f"Set {key} in the process environment. Do not commit the value.",
        )
    return value


def load_settings(
    *,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> Settings:
    """Load and validate settings.

    When ``environ`` is omitted, values come from the process environment after
    an optional ``.env`` file is loaded. Passed mappings are used as-is so tests
    do not read a developer environment file.
    """
    root = repo_root or find_repo_root()
    if environ is None:
        load_dotenv(root / ".env", override=False)
        source: Mapping[str, str] = os.environ
    else:
        source = environ
    mode_text = _raw(source, "APP_MODE") or "local"
    try:
        mode = AppMode(mode_text.lower())
    except ValueError as exc:
        raise ConfigurationError(
            f"APP_MODE '{mode_text}' is not supported.",
            likely_cause="APP_MODE must be local, cdf, or hybrid.",
            action="Set APP_MODE=local to run the demo without cloud credentials.",
        ) from exc
    provider_text = _raw(source, "AI_PROVIDER") or "mock"
    try:
        provider = AiProviderName(provider_text.lower())
    except ValueError as exc:
        raise ConfigurationError(
            f"AI_PROVIDER '{provider_text}' is not supported.",
            likely_cause="AI_PROVIDER must be mock or openai_compatible.",
            action="Set AI_PROVIDER=mock to use the deterministic investigator.",
        ) from exc
    log_level = (_raw(source, "LOG_LEVEL") or "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        raise ConfigurationError(
            f"LOG_LEVEL '{log_level}' is not supported.",
            likely_cause="LOG_LEVEL is not a standard level used by this application.",
            action="Set LOG_LEVEL to DEBUG, INFO, WARNING, or ERROR.",
        )
    login_flow = _raw(source, "LOGIN_FLOW") or "client_credentials"
    if login_flow != "client_credentials":
        raise ConfigurationError(
            f"LOGIN_FLOW '{login_flow}' is not implemented.",
            likely_cause="This POC authenticates with the client-credentials flow.",
            action="Set LOGIN_FLOW=client_credentials.",
        )
    fallback = ""
    if provider is AiProviderName.OPENAI_COMPATIBLE and (
        not _raw(source, "AI_ENDPOINT") or not _raw(source, "AI_API_KEY")
    ):
        if mode is AppMode.CDF:
            _require(source, "AI_ENDPOINT", "the external AI provider")
            _require(source, "AI_API_KEY", "the external AI provider")
        provider = AiProviderName.MOCK
        fallback = (
            "AI endpoint or API key is empty, so the deterministic mock investigator is used."
        )
    if mode in {AppMode.CDF, AppMode.HYBRID}:
        _require(source, "CDF_PROJECT", f"APP_MODE={mode.value}")
        if not _raw(source, "CDF_CLUSTER") and not _raw(source, "CDF_BASE_URL"):
            raise ConfigurationError(
                "CDF_CLUSTER or CDF_BASE_URL is required.",
                likely_cause="The CDF API host is not configured.",
                action="Set CDF_CLUSTER or CDF_BASE_URL, or use APP_MODE=local.",
            )
        for key in ("CDF_CLIENT_ID", "CDF_CLIENT_SECRET", "CDF_TOKEN_URL", "CDF_SCOPES"):
            _require(source, key, f"APP_MODE={mode.value}")
    return Settings(
        app_mode=mode,
        ai_provider=provider,
        ai_model=_raw(source, "AI_MODEL"),
        ai_endpoint=_raw(source, "AI_ENDPOINT"),
        ai_api_key=_raw(source, "AI_API_KEY"),
        ai_fallback_reason=fallback,
        log_level=log_level,
        cdf_project=_raw(source, "CDF_PROJECT"),
        cdf_cluster=_raw(source, "CDF_CLUSTER"),
        cdf_base_url=_raw(source, "CDF_BASE_URL"),
        cdf_tenant_id=_raw(source, "CDF_TENANT_ID"),
        cdf_client_id=_raw(source, "CDF_CLIENT_ID"),
        cdf_client_secret=_raw(source, "CDF_CLIENT_SECRET"),
        cdf_token_url=_raw(source, "CDF_TOKEN_URL"),
        cdf_scopes=_raw(source, "CDF_SCOPES"),
        cdf_data_set_external_id=_raw(source, "CDF_DATA_SET_EXTERNAL_ID")
        or "cdf-maintenance-investigator-demo",
        cdf_space=_raw(source, "CDF_SPACE") or "cdf_maintenance_demo",
        cdf_instance_space=_raw(source, "CDF_INSTANCE_SPACE") or "cdf_maintenance_demo_instances",
        cdf_environment=_raw(source, "CDF_ENVIRONMENT") or "dev",
        login_flow=login_flow,
        write_classic_events=_raw(source, "CDF_WRITE_CLASSIC_EVENTS").lower() == "true",
        confirm_cleanup=_raw(source, "CDF_CONFIRM_CLEANUP").lower() == "yes",
        repo_root=root,
    )


def assert_development_target(settings: Settings) -> None:
    """Refuse project names or environments that look like production."""
    project = settings.cdf_project.lower()
    environment = settings.cdf_environment.lower()
    if "prod" in project or environment in {"prod", "production"}:
        raise ConfigurationError(
            "Refusing a production CDF target.",
            likely_cause="CDF_PROJECT or CDF_ENVIRONMENT identifies production.",
            action="Use the development project and set CDF_ENVIRONMENT=dev.",
        )
