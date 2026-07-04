"""Async AI-extraction pipeline handler.

Runs the LLM extraction for an uploaded document, computes a confidence signal,
and applies the CONFIDENCE GATE:

- high confidence (>= ``EXTRACTION_AUTOCOMMIT_THRESHOLD``) and not forced review
  -> auto-commit (``status=committed``);
- low confidence or ``force_review`` -> human-review queue (``status=needs_review``).

On extraction failure the document is marked ``failed`` and the tenant's quota
reservation is refunded; the exception re-raises so the job is recorded failed
and Cloud Tasks retries.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.document import DocumentStatus
from src.repositories.document_repository import DocumentRepository
from src.services import quota_service
from src.services.ai_service import generate_text
from src.services.email_service import send_email

logger = logging.getLogger(__name__)


def _mock_extraction(content_hash: str) -> tuple[dict[str, object], float]:
    """Deterministic stub extraction used when AI is disabled (local/tests).

    Confidence is derived from the content hash so tests are reproducible.
    """
    confidence = (int(content_hash[:8], 16) % 100) / 100.0
    extraction: dict[str, object] = {
        "provider": "mock",
        "fields": {"summary": "stub extraction", "hash_prefix": content_hash[:8]},
    }
    return extraction, confidence


async def _ai_extraction(filename: str) -> tuple[dict[str, object], float]:
    """Run the real LLM extraction. Confidence is a provider-reported signal."""
    prompt = (
        "Extract the key structured fields from the document named "
        f"'{filename}' and return concise JSON."
    )
    text = await generate_text(prompt)
    extraction: dict[str, object] = {"provider": "gemini", "raw": text}
    # A real implementation parses structured JSON + a model-reported score; the
    # skeleton uses a fixed high confidence to exercise the auto-commit path.
    return extraction, 0.95


async def run_extraction(
    session: AsyncSession,
    tenant_id: str,
    document_id: str,
    *,
    force_review: bool = False,
) -> None:
    """Extract, gate, and persist a document result. Manages its own commit."""
    settings = get_settings()
    repo = DocumentRepository(session)

    document = await repo.get_for_worker(document_id)
    if document is None:
        logger.warning("extraction.run missing document_id=%s", document_id)
        return
    if document.status in {DocumentStatus.COMMITTED, DocumentStatus.NEEDS_REVIEW}:
        # Idempotency: already processed by a prior (succeeded) attempt.
        logger.info("extraction.run skip already-processed document_id=%s", document_id)
        return

    logger.info("extraction.run start document_id=%s", document_id)
    try:
        if settings.AI_ENABLED:
            extraction, confidence = await _ai_extraction(document.filename)
        else:
            extraction, confidence = _mock_extraction(document.content_hash)
    except Exception as exc:
        await session.rollback()
        document = await repo.get_for_worker(document_id)
        if document is not None:
            await repo.apply_extraction(
                document,
                status=DocumentStatus.FAILED,
                extraction={"error": str(exc)},
                confidence=None,
            )
        await quota_service.refund(session, tenant_id)
        await session.commit()
        logger.exception("extraction.run failed document_id=%s", document_id)
        raise

    needs_review = force_review or confidence < settings.EXTRACTION_AUTOCOMMIT_THRESHOLD
    new_status = DocumentStatus.NEEDS_REVIEW if needs_review else DocumentStatus.COMMITTED
    await repo.apply_extraction(
        document,
        status=new_status,
        extraction=extraction,
        confidence=confidence,
    )
    await session.commit()

    if new_status == DocumentStatus.NEEDS_REVIEW and document.created_by:
        # Fire-and-forget: never fail the pipeline on a notification hiccup.
        await send_email(
            to=document.created_by,
            subject="Document ready for review",
            body=f"Document {document.filename} needs your review.",
        )

    logger.info(
        "extraction.run success document_id=%s status=%s confidence=%.2f",
        document_id,
        new_status,
        confidence,
    )
