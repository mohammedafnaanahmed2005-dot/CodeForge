"""
ConversationManager – session-scoped, isolated conversation history.

Each domain app owns its own instance so conversations never leak
across domains.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Turn:
    role: str
    content: str


class ConversationManager:
    """Maintains an isolated message history for one domain app."""

    def __init__(self, max_turns: int = 20) -> None:
        self._history: list[Turn] = []
        self._max_turns = max_turns

    def add_user_message(self, content: str) -> None:
        self._history.append(Turn("user", content))
        self._trim()

    def add_assistant_message(self, content: str) -> None:
        self._history.append(Turn("assistant", content))
        self._trim()

    def get_messages(self) -> list[dict[str, str]]:
        return [{"role": t.role, "content": t.content} for t in self._history]

    def reset(self) -> None:
        self._history.clear()

    def is_empty(self) -> bool:
        return not self._history

    def turn_count(self) -> int:
        return len(self._history)

    def _trim(self) -> None:
        if len(self._history) > self._max_turns:
            self._history = self._history[-self._max_turns:]
