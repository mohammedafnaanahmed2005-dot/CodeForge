"""
PromptManager – loads, customises and assembles domain system prompts.

Prompts live as Python constants per domain (in ``apps/<domain>/prompts.py``)
and are registered here.  The manager layers the prompt:
base persona → domain instructions → user context (subject, level, ...),
so callers never build raw prompt strings themselves.
"""

from __future__ import annotations


class PromptManager:
    """Registry and assembler for domain-specific system prompts."""

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, app_id: str, template: str) -> None:
        """Register a base system prompt template for *app_id*."""
        self._templates[app_id] = template

    def has(self, app_id: str) -> bool:
        """True if a prompt is registered for *app_id*."""
        return app_id in self._templates

    def build_system_prompt(
        self,
        app_id: str,
        context: dict[str, str] | None = None,
    ) -> str:
        """
        Return the full system prompt for *app_id*.

        Args:
            app_id: Domain identifier, e.g. ``"edutrack"``.
            context: Optional key/value user context (subject, level, ...)
                     appended as structured context lines.

        Raises:
            KeyError: No prompt registered for *app_id*.
        """
        if app_id not in self._templates:
            raise KeyError(
                f"No system prompt registered for application '{app_id}'. "
                "Call register() first or add the domain prompt module."
            )

        prompt = self._templates[app_id]

        if context:
            lines = [f"- {key.replace('_', ' ').title()}: {value}"
                     for key, value in context.items() if value]
            if lines:
                prompt += "\n\nUser context:\n" + "\n".join(lines)

        return prompt
