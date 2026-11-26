"""
SafetyService – domain-aware safety checks applied before every AI call.

Each domain can define a list of prohibited request patterns and an
emergency message in its YAML config.  The service prepends a mandatory
disclaimer to every response so the UI always shows it.
"""

from __future__ import annotations

import re
from typing import Any

from core.errors import SafetyError


class SafetyService:
    """Apply domain-specific safety rules to user messages and responses."""

    # Patterns that should always trigger emergency guidance regardless of domain
    _UNIVERSAL_EMERGENCY_PATTERNS: list[str] = [
        r"\bsuicide\b",
        r"\bkill myself\b",
        r"\bend my life\b",
        r"\bself.harm\b",
        r"\boverdose\b",
    ]

    def __init__(self, app_config: dict[str, Any]) -> None:
        safety_cfg = app_config.get("safety", {})
        self._disclaimer: str = (
            safety_cfg.get("medical_disclaimer", "")
            or safety_cfg.get("disclaimer", "")
        )
        self._emergency_message: str = safety_cfg.get("emergency_message", "")
        raw_prohibited: list[str] = safety_cfg.get("prohibited_requests", [])
        self._prohibited_patterns: list[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in raw_prohibited
        ]
        self._app_id: str = app_config.get("app", {}).get("id", "unknown")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_input(self, user_message: str) -> None:
        """
        Raise :class:`SafetyError` if *user_message* triggers a blocked
        pattern for this domain.
        """
        # Universal emergency patterns
        for raw in self._UNIVERSAL_EMERGENCY_PATTERNS:
            if re.search(raw, user_message, re.IGNORECASE):
                emergency = (
                    self._emergency_message
                    or "If this is an emergency please contact emergency services immediately."
                )
                raise SafetyError(
                    f"⚠️ **Emergency Notice**\n\n{emergency}\n\n"
                    "If you need to talk to someone, please reach out to a crisis helpline."
                )

        # Domain-specific prohibited patterns (healthmate: no diagnosis/prescription)
        for pattern in self._prohibited_patterns:
            if pattern.search(user_message):
                raise SafetyError(
                    f"I'm sorry, but I'm not able to {pattern.pattern.strip('()')} "
                    "as that falls outside what I can safely provide.\n\n"
                    + self._get_redirect_message()
                )

    def build_response_with_disclaimer(self, response: str) -> str:
        """Append the domain disclaimer to the AI response when present."""
        if not self._disclaimer:
            return response
        separator = "\n\n---\n"
        return f"{response}{separator}*{self._disclaimer}*"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_redirect_message(self) -> str:
        if self._app_id == "healthmate":
            return (
                "Please consult a qualified healthcare professional for personal "
                "medical advice, diagnosis, or treatment."
            )
        return "Please rephrase your question so I can help you better."
