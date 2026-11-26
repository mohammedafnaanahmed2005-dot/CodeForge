"""
ValidationService – validates user input before it reaches the AI engine.

Rules are configurable through the framework YAML so they can be tightened
or relaxed without touching this module.
"""

from __future__ import annotations

from core.errors import ValidationError


class ValidationService:
    """Validate raw user input against configurable constraints."""

    DEFAULT_MAX_LENGTH = 2000
    DEFAULT_MIN_LENGTH = 1

    def __init__(
        self,
        max_length: int = DEFAULT_MAX_LENGTH,
        min_length: int = DEFAULT_MIN_LENGTH,
    ) -> None:
        self.max_length = max_length
        self.min_length = min_length

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, text: str) -> str:
        """
        Validate *text* and return the sanitised version.

        Raises :class:`ValidationError` if any constraint is violated.
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string.")

        cleaned = text.strip()

        if len(cleaned) < self.min_length:
            raise ValidationError("Message cannot be empty.")

        if len(cleaned) > self.max_length:
            raise ValidationError(
                f"Message is too long ({len(cleaned)} characters). "
                f"Please keep it under {self.max_length} characters."
            )

        return cleaned

    def validate_app_config(self, config: dict) -> None:
        """
        Raise :class:`ValidationError` if the minimum required config
        keys are absent.
        """
        required_keys = ["app", "openai"]
        missing = [k for k in required_keys if k not in config]
        if missing:
            raise ValidationError(
                f"Application configuration is missing required keys: {missing}"
            )
