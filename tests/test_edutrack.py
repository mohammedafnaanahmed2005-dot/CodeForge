"""Tests for EduTrack AI domain application."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from codeforge_core.ai_engine import AIEngine
from codeforge_core.config_loader import ConfigLoader
from codeforge_core.errors import AIEngineError, ValidationError, SafetyError
from codeforge_core.conversation_manager import ConversationManager
from codeforge_core.validator import ValidationService
from codeforge_core.safety_service import SafetyService
from codeforge_core.prompt_manager import PromptManager


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cfg():
    return ConfigLoader()


def _mock_engine(cfg, reply="EduTrack response"):
    engine = AIEngine(config_loader=cfg, api_key="sk-test-fake")
    msg = MagicMock(); msg.content = reply
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = resp
    engine.set_client_for_testing(client)
    return engine


@pytest.fixture
def edu_engine(cfg):
    return _mock_engine(cfg)


# ── Validation ────────────────────────────────────────────────────────────────

def test_empty_input_raises():
    v = ValidationService()
    with pytest.raises(ValidationError):
        v.validate("")


def test_too_long_input_raises():
    v = ValidationService(max_length=200)
    with pytest.raises(ValidationError):
        v.validate("x" * 201)


def test_valid_input_passes():
    v = ValidationService()
    assert v.validate("  Explain gravity  ") == "Explain gravity"


# ── Prompt building ───────────────────────────────────────────────────────────

def test_edu_prompt_includes_context():
    pm = PromptManager()
    pm.register("edutrack", "Base prompt.")
    prompt = pm.build_system_prompt(
        "edutrack",
        {"subject": "Physics", "academic_level": "High School"},
    )
    assert "Physics" in prompt
    assert "High School" in prompt


def test_edu_prompt_ignores_empty_context_values():
    pm = PromptManager()
    pm.register("edutrack", "Base.")
    prompt = pm.build_system_prompt("edutrack", {"subject": "", "level": "X"})
    assert "Subject:" not in prompt


# ── Conversation management ───────────────────────────────────────────────────

def test_conversation_accumulates_turns():
    convo = ConversationManager()
    convo.add_user_message("Q1")
    convo.add_assistant_message("A1")
    assert convo.turn_count() == 2


def test_conversation_reset():
    convo = ConversationManager()
    convo.add_user_message("Q1")
    convo.reset()
    assert convo.is_empty()


def test_edu_sessions_isolated():
    c1 = ConversationManager()
    c2 = ConversationManager()
    c1.add_user_message("Calculus question")
    c2.add_user_message("History question")
    assert c1.get_messages()[0]["content"] == "Calculus question"
    assert c2.get_messages()[0]["content"] == "History question"


# ── Safety ────────────────────────────────────────────────────────────────────

def test_edu_normal_question_passes(cfg):
    safety = SafetyService(cfg.get_app_config("edutrack"))
    safety.check_input("Explain the Pythagorean theorem")


def test_edu_emergency_keyword_blocked(cfg):
    safety = SafetyService(cfg.get_app_config("edutrack"))
    with pytest.raises(SafetyError):
        safety.check_input("I want to kill myself")


# ── AI engine integration ─────────────────────────────────────────────────────

def test_ai_engine_generates_response(cfg, edu_engine):
    pm = PromptManager()
    pm.register("edutrack", "You are EduTrack AI.")
    sys_prompt = pm.build_system_prompt("edutrack")
    convo = ConversationManager()
    convo.add_user_message("What is gravity?")
    reply = edu_engine.generate_response(
        system_prompt=sys_prompt,
        messages=convo.get_messages(),
        app_id="edutrack",
    )
    assert "EduTrack response" in reply


def test_ai_engine_error_propagates(cfg):
    engine = AIEngine(config_loader=cfg, api_key="sk-test-fake")
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("fail")
    engine.set_client_for_testing(client)
    with pytest.raises(AIEngineError):
        engine.generate_response("sys", [{"role": "user", "content": "q"}])


# ── Config ────────────────────────────────────────────────────────────────────

def test_edu_config_loads(cfg):
    data = cfg.get_app_config("edutrack")
    assert data["app"]["id"] == "edutrack"
    assert "subjects" in data


def test_edu_config_has_example_questions(cfg):
    data = cfg.get_app_config("edutrack")
    assert len(data.get("example_questions", [])) > 0
