"""
HealthMateApp – Healthcare information domain application.

Shares the core AI engine with EduTrack but applies its own safety rules,
disclaimers, and system prompt.
"""

from __future__ import annotations

from typing import Any

from apps.healthmate.prompts import SYSTEM_PROMPT
from core.ai_engine import AIEngine
from core.config_manager import ConfigManager
from core.conversation_manager import ConversationManager
from core.errors import SafetyError, ValidationError
from core.prompt_manager import PromptManager
from core.safety_service import SafetyService
from core.validation_service import ValidationService

APP_ID = "healthmate"


class HealthMateApp:
    """HealthMate AI – general health information assistant."""

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_engine: AIEngine,
    ) -> None:
        self._cfg = config_manager
        self._engine = ai_engine
        self._app_config = self._cfg.get_app_config(APP_ID)

        self._validator = ValidationService(
            max_length=self._cfg.get_framework_config()
            .get("validation", {})
            .get("max_input_length", 2000)
        )
        self._safety = SafetyService(self._app_config)
        self._conversations: dict[str, ConversationManager] = {}

        self._prompts = PromptManager()
        self._prompts.register(APP_ID, SYSTEM_PROMPT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def app_config(self) -> dict[str, Any]:
        return self._app_config

    def get_conversation(self, session_id: str) -> ConversationManager:
        if session_id not in self._conversations:
            self._conversations[session_id] = ConversationManager()
        return self._conversations[session_id]

    def clear_conversation(self, session_id: str) -> None:
        self.get_conversation(session_id).reset()

    def chat(
        self,
        session_id: str,
        user_message: str,
        topic_category: str = "",
    ) -> str:
        """Process a user message and return the assistant reply."""
        # 1 – Validate
        clean_message = self._validator.validate(user_message)

        # 2 – Safety check (blocks diagnosis/prescription requests, emergencies)
        self._safety.check_input(clean_message)

        # 3 – Build system prompt with optional topic context
        context = {"topic_category": topic_category} if topic_category else None
        system_prompt = self._prompts.build_system_prompt(APP_ID, context)

        # 4 – Record turn
        convo = self.get_conversation(session_id)
        convo.add_user_message(clean_message)
        messages = convo.get_messages()

        # 5 – Call engine
        response = self._engine.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            app_id=APP_ID,
        )

        # 6 – Append medical disclaimer and record
        final_response = self._safety.build_response_with_disclaimer(response)
        convo.add_assistant_message(final_response)

        return final_response
