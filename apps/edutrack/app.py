"""
EduTrackApp – Education domain application.

Wires together the core framework services with EduTrack-specific
configuration and prompt logic.  The AI engine is shared; everything
else is domain-specific.
"""

from __future__ import annotations

from typing import Any

from apps.edutrack.prompts import SYSTEM_PROMPT
from core.ai_engine import AIEngine
from core.config_manager import ConfigManager
from core.conversation_manager import ConversationManager
from core.errors import SafetyError, ValidationError
from core.prompt_manager import PromptManager
from core.safety_service import SafetyService
from core.validation_service import ValidationService

APP_ID = "edutrack"


class EduTrackApp:
    """
    EduTrack AI – personal academic assistant.

    Strategy: attach user context (subject, academic level, etc.) to the
    system prompt at runtime; the AI engine receives a fully-assembled
    prompt and needs no domain knowledge itself.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_engine: AIEngine,
    ) -> None:
        self._cfg = config_manager
        self._engine = ai_engine
        self._app_config = self._cfg.get_app_config(APP_ID)

        # Build reusable services
        self._validator = ValidationService(
            max_length=self._cfg.get_framework_config()
            .get("validation", {})
            .get("max_input_length", 2000)
        )
        self._safety = SafetyService(self._app_config)
        self._conversations: dict[str, ConversationManager] = {}

        # Register domain prompt
        self._prompts = PromptManager()
        self._prompts.register(APP_ID, SYSTEM_PROMPT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def app_config(self) -> dict[str, Any]:
        return self._app_config

    def get_conversation(self, session_id: str) -> ConversationManager:
        """Get (or lazily create) the conversation for *session_id*."""
        if session_id not in self._conversations:
            self._conversations[session_id] = ConversationManager()
        return self._conversations[session_id]

    def clear_conversation(self, session_id: str) -> None:
        """Reset the conversation for *session_id*."""
        self.get_conversation(session_id).reset()

    def chat(
        self,
        session_id: str,
        user_message: str,
        subject: str = "",
        academic_level: str = "",
        learning_difficulty: str = "",
        assistance_type: str = "",
    ) -> str:
        """
        Process a user message and return the assistant reply.

        Returns a plain string; Streamlit renders Markdown from it.
        """
        # 1 – Validate input
        clean_message = self._validator.validate(user_message)

        # 2 – Safety check
        self._safety.check_input(clean_message)

        # 3 – Build contextualised system prompt
        context = {
            "subject": subject,
            "academic_level": academic_level,
            "learning_difficulty": learning_difficulty,
            "assistance_type": assistance_type,
        }
        system_prompt = self._prompts.build_system_prompt(APP_ID, context)

        # 4 – Record turn, build message list
        convo = self.get_conversation(session_id)
        convo.add_user_message(clean_message)
        messages = convo.get_messages()

        # 5 – Call AI engine
        response = self._engine.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            app_id=APP_ID,
        )

        # 6 – Record assistant reply (with disclaimer appended)
        final_response = self._safety.build_response_with_disclaimer(response)
        convo.add_assistant_message(final_response)

        return final_response
