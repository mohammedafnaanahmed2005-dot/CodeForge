"""
ErrorHandler – translates low-level API / network exceptions into
user-friendly AIEngineError instances.
"""

from __future__ import annotations

import logging

from codeforge_core.errors import AIEngineError, MissingAPIKeyError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralised exception translator for the AI engine."""

    @staticmethod
    def handle(exc: Exception) -> None:
        logger.error("AI engine error: %s", exc, exc_info=True)

        message = str(exc).lower()

        try:
            import openai  # noqa: PLC0415

            if isinstance(exc, openai.AuthenticationError):
                raise MissingAPIKeyError(
                    "Invalid or missing API key. "
                    "Set NVIDIA_API_KEY or OPENAI_API_KEY in your .env file."
                ) from exc

            if isinstance(exc, openai.RateLimitError):
                raise AIEngineError(
                    "Rate limit reached. Please wait a moment and try again."
                ) from exc

            if isinstance(exc, openai.APIConnectionError):
                raise AIEngineError(
                    "Could not connect to the AI provider. "
                    "Check your internet connection and try again."
                ) from exc

            if isinstance(exc, openai.APITimeoutError):
                raise AIEngineError("The request timed out. Please try again.") from exc

            if isinstance(exc, openai.BadRequestError):
                raise AIEngineError(
                    "The request was rejected. Try rephrasing your message."
                ) from exc

            if isinstance(exc, openai.APIStatusError):
                raise AIEngineError(
                    f"API returned an error (HTTP {exc.status_code}): {exc.message}"
                ) from exc

        except ImportError:
            pass

        if "api key" in message or "authentication" in message:
            raise MissingAPIKeyError(
                "API key problem detected. Verify your key configuration."
            ) from exc

        raise AIEngineError(
            f"An unexpected error occurred ({type(exc).__name__}): {exc}. "
            "Please try again."
        ) from exc
