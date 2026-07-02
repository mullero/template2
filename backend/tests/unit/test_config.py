"""Unit tests for configuration."""

from __future__ import annotations

import pytest

from src.config import Environment, Settings, get_settings, reset_settings_cache, validate_config


def test_settings_parses_csv_cors() -> None:
    settings = Settings(CORS_ORIGINS="http://a.test,http://b.test")
    assert settings.CORS_ORIGINS == ["http://a.test", "http://b.test"]


def test_environment_helpers() -> None:
    settings = Settings(DEPLOYMENT_ENVIRONMENT=Environment.TESTING)
    assert settings.is_test is True
    assert settings.is_testing is True
    assert settings.is_production is False
    assert settings.dev_or_test is True


def test_get_settings_is_cached() -> None:
    reset_settings_cache()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_validate_config_rejects_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_settings_cache()
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "development")
    reset_settings_cache()
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_config()
    reset_settings_cache()


def test_validate_config_hard_fails_on_placeholder_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "CHANGE_ME")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.test")
    reset_settings_cache()
    with pytest.raises(RuntimeError, match="placeholder"):
        validate_config()
    reset_settings_cache()
