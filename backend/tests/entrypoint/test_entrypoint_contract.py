"""Entrypoint contract tests.

These assert the entrypoint script's non-destructive contract via static checks,
so they run without Docker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).resolve().parents[2] / "entrypoint.sh"

pytestmark = pytest.mark.entrypoint


def _script() -> str:
    return ENTRYPOINT.read_text(encoding="utf-8")


def test_entrypoint_exists_and_strict() -> None:
    text = _script()
    assert "set -euo pipefail" in text
    assert "inherit_errexit" in text


def test_entrypoint_refuses_destructive_reset() -> None:
    text = _script()
    assert "RESET_DB_ON_STARTUP" in text
    assert "never drops data" in text


def test_entrypoint_runs_migrations_and_drift_check() -> None:
    text = _script()
    assert "alembic upgrade head" in text
    assert "alembic check" in text
    assert "DRIFT_CHECK_ENABLED" in text


def test_entrypoint_stamps_when_version_missing() -> None:
    text = _script()
    assert "alembic stamp head" in text
