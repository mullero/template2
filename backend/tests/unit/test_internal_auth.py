"""Unit tests for the internal Cloud Tasks OIDC guard (mocking verification)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.config import reset_settings_cache
from src.dependencies import internal_auth


def _creds(token: str = "tok") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_missing_credentials_rejected() -> None:
    with pytest.raises(HTTPException) as exc:
        await internal_auth.verify_cloud_tasks_oidc(None)
    assert exc.value.status_code == 401


async def test_wrong_service_account_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ["TASKS_SERVICE_ACCOUNT"] = "queue@project.iam.gserviceaccount.com"
    reset_settings_cache()
    monkeypatch.setattr(
        internal_auth,
        "_verify_oidc",
        lambda _token, _aud: {"email": "attacker@evil.example"},
    )
    try:
        with pytest.raises(HTTPException) as exc:
            await internal_auth.verify_cloud_tasks_oidc(_creds())
        assert exc.value.status_code == 403
    finally:
        os.environ.pop("TASKS_SERVICE_ACCOUNT", None)
        reset_settings_cache()


async def test_valid_token_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    os.environ["TASKS_SERVICE_ACCOUNT"] = "queue@project.iam.gserviceaccount.com"
    reset_settings_cache()

    def _ok(_token: str, _aud: str) -> dict[str, Any]:
        return {"email": "queue@project.iam.gserviceaccount.com"}

    monkeypatch.setattr(internal_auth, "_verify_oidc", _ok)
    try:
        assert await internal_auth.verify_cloud_tasks_oidc(_creds()) is None
    finally:
        os.environ.pop("TASKS_SERVICE_ACCOUNT", None)
        reset_settings_cache()
