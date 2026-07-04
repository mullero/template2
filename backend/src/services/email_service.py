"""Email/notification service.

Provider-agnostic wrapper (SendGrid by default) behind a tiny typed surface.
Sending is gated on ``EMAIL_ENABLED`` and is best-effort/fire-and-forget: a
notification failure must NEVER fail a user write. The heavy provider SDK is
imported lazily.
"""

from __future__ import annotations

import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(*, to: str, subject: str, body: str) -> bool:
    """Send an email through the configured provider.

    Returns ``True`` on success, ``False`` on any failure (never raises). No-op
    (returns ``True``) when ``EMAIL_ENABLED`` is false.
    """
    settings = get_settings()
    if not settings.EMAIL_ENABLED:
        logger.info("email.send skipped (EMAIL_ENABLED=false) subject=%s", subject)
        return True

    try:
        if settings.EMAIL_PROVIDER == "sendgrid":
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=to,
                subject=subject,
                plain_text_content=body,
            )
            client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            client.send(message)
        else:  # pragma: no cover - alternate providers not implemented in skeleton
            logger.warning("email.send unknown provider=%s", settings.EMAIL_PROVIDER)
            return False
    except Exception:
        logger.exception("email.send failed subject=%s (continuing)", subject)
        return False

    logger.info("email.send success subject=%s", subject)
    return True
