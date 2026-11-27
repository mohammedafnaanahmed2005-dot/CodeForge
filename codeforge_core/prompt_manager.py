"""
PromptManager – registry and assembler for domain-specific system prompts.
"""

from __future__ import annotations


class PromptManager:
    """Registry and assembler for domain-specific system prompts."""

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}

    def register(self, app_id: str, template: str) -> None:
        self._templates[app_id] = template

    def has(self, app_id: str) -> bool:
        return app_id in self._templates

    def build_system_prompt(
        self,
        app_id: str,
        context: dict[str, str] | None = None,
    ) -> str:
        """Return the full system prompt for *app_id*, with optional context lines."""
        if app_id not in self._templates:
            raise KeyError(
                f"No system prompt registered for application '{app_id}'. "
                "Call register() first."
            )

        prompt = self._templates[app_id]

        if context:
            lines = [
                f"- {key.replace('_', ' ').title()}: {value}"
                for key, value in context.items()
                if value
            ]
            if lines:
                prompt += "\n\nUser context:\n" + "\n".join(lines)

        return prompt
