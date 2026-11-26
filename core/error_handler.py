"""
ErrorHandler – translates low-level OpenAI / network exceptions into
user-friendly messages and framework-level AIEngineError exceptions.
"""

from __future__ import annotations

import logging

from core.errors import AIEngineError, MissingAPIKeyError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralised exception translator for the AI engine."""

    @staticmethod
    def handle(exc: Exception) -> None:
        """
        Log the original exception, then raise :class:`AIEngineError`
        (or a more specific subclass) with a human-readable message.
        """
        logger.error("AI engine error: %s", exc, exc_info=True)

        exc_type = type(exc).__name__
        message = str(exc).lower()

        # --- OpenAI SDK specific errors (lazy import so tests don't need openai) ---
        try:
            import openai  # noqa: PLC0415

            if isinstance(exc, openai.AuthenticationError):
                raise MissingAPIKeyError(
                    "Invalid or missing OpenAI API key. "
                    "Set OPENAI_API_KEY in your .env file or Streamlit secrets."
                ) from exc

            if isinstance(exc, openai.RateLimitError):
                raise AIEngineError(
                    "OpenAI rate limit reached. Please wait a moment and try again."
                ) from exc

            if isinstance(exc, openai.APIConnectionError):
                raise AIEngineError(
                    "Could not connect to the OpenAI API. "
                    "Check your internet connection and try again."
                ) from exc

            if isinstance(exc, openai.APITimeoutError):
                raise AIEngineError(
                    "The request to OpenAI timed out. Please try again."
                ) from exc

            if isinstance(exc, openai.BadRequestError):
                raise AIEngineError(
                    "The request was rejected by OpenAI (bad request). "
                    "Try rephrasing your message."
                ) from exc

            if isinstance(exc, openai.APIStatusError):
                raise AIEngineError(
                    f"OpenAI API returned an error (HTTP {exc.status_code}): "
                    f"{exc.message}"
                ) from exc

        except ImportError:
            pass  # openai not installed in test environment

        # --- Generic fallback ---
        if "api key" in message or "authentication" in message:
            raise MissingAPIKeyError(
                "API key problem detected. "
                "Please verify your OPENAI_API_KEY configuration."
            ) from exc

        raise AIEngineError(
            f"An unexpected error occurred ({exc_type}): {exc}. "
            "Please try again or contact support."
        ) from exc
