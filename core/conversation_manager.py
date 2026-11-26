"""
ConversationManager – session-scoped conversation history.

Each domain app owns an independent instance, and every browser session
gets its own state (Streamlit session_state keyed by app id), so
conversations never leak across domains or users.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    """A single conversation turn."""
    role: str  # "user" or "assistant"
    content: str


class ConversationManager:
    """Maintains an isolated message history for one domain app."""

    def __init__(self) -> None:
        self._history: list[Turn] = field(default_factory=list) if False else []
        self._max_turns: int = 20  # keep context bounded for token limits

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_user_message(self, content: str) -> None:
        self._history.append(Turn("user", content))
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        self._history.append(Turn("assistant", content))
        self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        """Return history in OpenAI message format."""
        return [{"role": t.role, "content": t.content} for t in self._history]

    def reset(self) -> None:
        """Clear all history for this conversation."""
        self._history.clear()

    def is_empty(self) -> bool:
        return not self._history

    def turn_count(self) -> int:
        return len(self._history)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _trim(self) -> None:
        if len(self._history) > self._max_turns:
            self._history = self._history[-self._max_turns:]
