"""AI provider service (Gemini / Vertex AI).

Kept intentionally small and gated on ``AI_ENABLED`` so a no-AI build stays lean.
The heavy provider SDKs are imported lazily inside the call path.
"""

from __future__ import annotations

import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class AIDisabledError(RuntimeError):
    """Raised when AI features are used while ``AI_ENABLED`` is false."""


async def generate_text(prompt: str) -> str:
    """Generate text from the configured provider.

    Raises :class:`AIDisabledError` when AI is disabled.
    """
    settings = get_settings()
    if not settings.AI_ENABLED:
        raise AIDisabledError("AI features are disabled (AI_ENABLED=false)")

    logger.info(
        "ai.generate_text start provider=%s model=%s",
        settings.AI_PROVIDER,
        settings.AI_MODEL,
    )

    if settings.AI_PROVIDER == "gemini":
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.AI_MODEL)
        response = await model.generate_content_async(prompt)
        text = response.text
    else:  # vertex
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.VERTEX_LOCATION)
        model = GenerativeModel(settings.AI_MODEL)
        response = await model.generate_content_async(prompt)
        text = response.text

    logger.info("ai.generate_text success chars=%d", len(text))
    return str(text)
