"""Internal worker authentication — Cloud Tasks OIDC verification.

The internal worker endpoints are authenticated by the OIDC token that Cloud
Tasks attaches (minted for the queue's service account), NOT the Firebase user
flow. This guard verifies the token signature + audience and asserts the caller
is the expected queue service account.

These routes are on the auth-coverage allow-list precisely because they use this
alternate machine-to-machine auth instead of :func:`require_tenant`.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def _verify_oidc(token: str, audience: str) -> dict[str, Any]:
    """Verify a Google-signed OIDC ID token. Raises on failure."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    request = google_requests.Request()
    claims: dict[str, Any] = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
        token,
        request,
        audience=audience,
    )
    return claims


async def verify_cloud_tasks_oidc(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    """FastAPI guard: accept only a valid Cloud Tasks OIDC token."""
    settings = get_settings()

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing worker credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = _verify_oidc(credentials.credentials, settings.tasks_oidc_audience)
    except Exception as exc:
        logger.info("internal.oidc verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid worker credentials",
        ) from exc

    expected_sa = settings.TASKS_SERVICE_ACCOUNT
    email = str(claims.get("email", ""))
    if expected_sa and email != expected_sa:
        logger.warning("internal.oidc rejected unexpected principal")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caller is not the queue service account",
        )


WorkerAuth = Depends(verify_cloud_tasks_oidc)
