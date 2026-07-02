"""Logging configuration helpers.

``print()`` is banned in application code (enforced by ruff). Use the stdlib
logger obtained via :func:`get_logger`.
"""

from __future__ import annotations

import logging
import sys

from src.config import get_settings

_configured = False


def configure_logging() -> None:
    """Configure root logging once, using the level from settings."""
    global _configured
    if _configured:
        return
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        ),
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
