"""Application configuration — a cached Pydantic BaseSettings singleton.

All configuration flows from environment variables (which the generated
``backend/.env`` supplies in local development). This module is the single point
of truth for typed settings; nothing else should read ``os.environ`` directly.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

logger = logging.getLogger(__name__)

_PLACEHOLDER = "CHANGE_ME"


class Environment(StrEnum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


def _split_csv(value: str | list[str]) -> list[str]:
    """Parse a comma-separated string into a trimmed, non-empty list."""
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Typed application settings. Env vars override values from ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Environment ---------------------------------------------------------
    DEPLOYMENT_ENVIRONMENT: Environment = Environment.DEVELOPMENT
    PROJECT_NAME: str = "machote"
    PRODUCT_NAME: str = "machote"
    LOG_LEVEL: str = "INFO"

    # --- Database ------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://machote:CHANGE_ME@localhost:5432/machote"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True

    # --- Cloud / storage -----------------------------------------------------
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GCS_BUCKET: str = ""

    # --- AI provider ---------------------------------------------------------
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "vertex"
    GEMINI_API_KEY: str = ""
    VERTEX_LOCATION: str = "us-central1"
    AI_MODEL: str = "gemini-1.5-flash"

    # --- Graph database (Neo4j) ---------------------------------------------
    GRAPH_ENABLED: bool = False
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "CHANGE_ME"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_POOL_SIZE: int = 50

    # --- Auth / Firebase -----------------------------------------------------
    AUTH_ENABLED: bool = True
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_AUTH_EMULATOR_HOST: str = ""

    # --- API + security ------------------------------------------------------
    API_HOST: str = "0.0.0.0"  # noqa: S104 — container binds all interfaces by design
    API_PORT: int = 8000
    API_VERSION: str = "0.1.0"
    SECRET_KEY: str = "CHANGE_ME"
    ENABLE_SWAGGER: bool = True
    ENABLE_DETAILED_ERRORS: bool = True
    ENABLE_DEV_ROUTES: bool = True

    # --- CORS ----------------------------------------------------------------
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"],
    )
    CORS_ALLOW_METHODS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    CORS_ALLOW_HEADERS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["Authorization", "Content-Type"],
    )

    # --- Feature flags -------------------------------------------------------
    FEATURE_PROJECTS: bool = True
    FEATURE_TASKS: bool = True

    # --- Resource limits -----------------------------------------------------
    MAX_REQUEST_BODY_BYTES: int = 10_485_760
    REQUEST_TIMEOUT_SECONDS: int = 30

    # --- Rate limiting -------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # --- Bootstrap admin -----------------------------------------------------
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@example.com"
    BOOTSTRAP_ADMIN_PASSWORD: str = "CHANGE_ME"
    BOOTSTRAP_TENANT_ID: str = "dev-tenant"

    # --- Sentry --------------------------------------------------------------
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # --- OpenTelemetry -------------------------------------------------------
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "machote-backend"

    # --- Startup safety ------------------------------------------------------
    DRIFT_CHECK_ENABLED: bool = True
    RESET_DB_ON_STARTUP: bool = False

    @field_validator("CORS_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def _parse_csv(cls, value: str | list[str]) -> list[str]:
        return _split_csv(value)

    # --- Environment helpers -------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.DEPLOYMENT_ENVIRONMENT is Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.DEPLOYMENT_ENVIRONMENT is Environment.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        return self.DEPLOYMENT_ENVIRONMENT is Environment.TESTING

    @property
    def is_testing(self) -> bool:
        return self.is_test

    @property
    def dev_or_test(self) -> bool:
        return self.is_development or self.is_test


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings (used by tests to reload env)."""
    get_settings.cache_clear()


def validate_config() -> None:
    """Validate configuration at startup.

    Hard-fails in non-development environments when required secrets still hold
    the ``CHANGE_ME`` placeholder. In development, only warns.
    """
    settings = get_settings()

    required_secrets: dict[str, str] = {
        "SECRET_KEY": settings.SECRET_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
    }
    if settings.AI_ENABLED and settings.AI_PROVIDER == "gemini":
        required_secrets["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    if settings.GRAPH_ENABLED:
        required_secrets["NEO4J_PASSWORD"] = settings.NEO4J_PASSWORD

    placeholders = [name for name, value in required_secrets.items() if _PLACEHOLDER in value]

    if placeholders:
        message = (
            f"Configuration contains placeholder secrets: {', '.join(sorted(placeholders))}"
        )
        if settings.is_development:
            logger.warning("%s (allowed in development)", message)
        else:
            raise RuntimeError(message)

    # CORS must never combine credentials with a wildcard.
    if "*" in settings.CORS_ORIGINS:
        raise RuntimeError("CORS_ORIGINS must enumerate explicit origins, never '*'.")

    logger.info(
        "Configuration validated: env=%s auth=%s graph=%s ai=%s",
        settings.DEPLOYMENT_ENVIRONMENT,
        settings.AUTH_ENABLED,
        settings.GRAPH_ENABLED,
        settings.AI_ENABLED,
    )
