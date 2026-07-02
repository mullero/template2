"""Authentication service — Firebase ID token verification + tenant resolution.

Isolates all ``firebase-admin`` interaction so routes/guards depend on a small,
typed surface. When ``AUTH_ENABLED`` is false (local dev only) a stub superadmin
is returned with a sentinel tenant so queries never touch real tenant data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)

# Sentinel tenant used when auth is disabled locally.
DEV_TENANT_ID = "dev-tenant"
DEV_USER_ID = "dev-superadmin"
DEV_USER_EMAIL = "dev@localhost"


class Role(StrEnum):
    """User roles, ordered least→most privileged."""

    VIEWER = "viewer"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """The identity resolved from a verified token (or the dev stub)."""

    uid: str
    email: str | None
    role: Role
    tenant_id: str | None

    @property
    def is_admin(self) -> bool:
        return self.role in {Role.ADMIN, Role.SUPERADMIN}

    @property
    def is_superadmin(self) -> bool:
        return self.role is Role.SUPERADMIN


class AuthError(Exception):
    """Raised when a token cannot be verified."""


@lru_cache(maxsize=1)
def _firebase_app() -> Any:
    """Initialize (once) and return the firebase-admin app.

    Honors ``FIREBASE_AUTH_EMULATOR_HOST`` for emulator mode (no real creds);
    otherwise uses ``GOOGLE_APPLICATION_CREDENTIALS`` / ADC.
    """
    import firebase_admin
    from firebase_admin import credentials

    settings = get_settings()
    options = {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None

    if settings.FIREBASE_AUTH_EMULATOR_HOST:
        logger.info("Initializing firebase-admin against the Auth emulator")
        return firebase_admin.initialize_app(options=options)

    cred = credentials.ApplicationDefault()
    return firebase_admin.initialize_app(cred, options=options)


def _role_from_claims(claims: dict[str, Any]) -> Role:
    raw = str(claims.get("role", Role.VIEWER))
    try:
        return Role(raw)
    except ValueError:
        return Role.VIEWER


def _tenant_from_claims(claims: dict[str, Any]) -> str | None:
    """Resolve tenant id from Identity Platform tenancy or a custom claim."""
    firebase_section = claims.get("firebase", {})
    if isinstance(firebase_section, dict):
        tenant = firebase_section.get("tenant")
        if tenant:
            return str(tenant)
    tenant_claim = claims.get("tenant_id")
    return str(tenant_claim) if tenant_claim else None


def dev_stub_user() -> AuthenticatedUser:
    """Return the stub superadmin used when auth is disabled locally."""
    return AuthenticatedUser(
        uid=DEV_USER_ID,
        email=DEV_USER_EMAIL,
        role=Role.SUPERADMIN,
        tenant_id=DEV_TENANT_ID,
    )


def verify_token(token: str) -> AuthenticatedUser:
    """Verify a Firebase ID token and resolve the authenticated user.

    Raises :class:`AuthError` on any verification failure.
    """
    from firebase_admin import auth as firebase_auth

    try:
        claims = firebase_auth.verify_id_token(token, app=_firebase_app())
    except Exception as exc:  # firebase raises several concrete types
        raise AuthError("Invalid or expired authentication token") from exc

    return AuthenticatedUser(
        uid=str(claims["uid"]),
        email=claims.get("email"),
        role=_role_from_claims(claims),
        tenant_id=_tenant_from_claims(claims),
    )


def set_user_claims(uid: str, *, role: Role, tenant_id: str) -> None:
    """Set custom claims (role + tenant) on a Firebase user.

    Used by the bootstrap flow to promote the first superadmin.
    """
    from firebase_admin import auth as firebase_auth

    firebase_auth.set_custom_user_claims(
        uid,
        {"role": str(role), "tenant_id": tenant_id},
        app=_firebase_app(),
    )
    logger.info("Set custom claims for uid=%s role=%s", uid, role)
