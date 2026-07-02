"""slowapi rate limiter singleton."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import get_settings


def _key_func(request: object) -> str:
    """Rate-limit key: client IP address."""
    return get_remote_address(request)  # type: ignore[arg-type]


settings = get_settings()

limiter = Limiter(
    key_func=_key_func,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
)
