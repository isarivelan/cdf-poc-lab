"""Configuration validation."""

from __future__ import annotations

import pytest

from maintenance_investigator.exceptions import ConfigurationError
from maintenance_investigator.settings import assert_development_target, load_settings

pytestmark = pytest.mark.unit


def test_local_mode_does_not_require_credentials(repo_root) -> None:
    settings = load_settings(
        environ={"APP_MODE": "local", "AI_PROVIDER": "mock"}, repo_root=repo_root
    )
    assert settings.app_mode.value == "local"
    assert settings.ai_provider.value == "mock"
    assert settings.public_summary()["cdf_client_secret"] == "empty"


def test_invalid_mode(repo_root) -> None:
    with pytest.raises(ConfigurationError) as caught:
        load_settings(environ={"APP_MODE": "production-cloud"}, repo_root=repo_root)
    assert "APP_MODE" in str(caught.value)
    assert "local" in caught.value.action


def test_cdf_mode_names_missing_key_without_secret(repo_root) -> None:
    secret = "super-secret-value-should-not-leak"
    with pytest.raises(ConfigurationError) as caught:
        load_settings(
            environ={
                "APP_MODE": "cdf",
                "CDF_CLIENT_SECRET": secret,
                "CDF_CLIENT_ID": "client",
                "CDF_TOKEN_URL": "https://login.example/token",
                "CDF_SCOPES": "https://example/.default",
            },
            repo_root=repo_root,
        )
    message = str(caught.value)
    assert secret not in message
    assert "CDF_PROJECT" in message


def test_openai_without_key_falls_back_in_local_mode(repo_root) -> None:
    settings = load_settings(
        environ={"APP_MODE": "local", "AI_PROVIDER": "openai_compatible"},
        repo_root=repo_root,
    )
    assert settings.ai_provider.value == "mock"
    assert "mock" in settings.ai_fallback_reason


def test_production_target_is_refused(repo_root) -> None:
    settings = load_settings(
        environ={"APP_MODE": "local", "CDF_PROJECT": "plant-prod", "CDF_ENVIRONMENT": "prod"},
        repo_root=repo_root,
    )
    with pytest.raises(ConfigurationError) as caught:
        assert_development_target(settings)
    assert "production" in str(caught.value).lower()
