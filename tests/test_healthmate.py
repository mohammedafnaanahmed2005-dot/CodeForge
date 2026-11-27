"""Tests for HealthMate AI domain application."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from codeforge_core.ai_engine import AIEngine
from codeforge_core.config_loader import ConfigLoader
from codeforge_core.errors import AIEngineError, ValidationError, SafetyError, MissingAPIKeyError
from codeforge_core.conversation_manager import ConversationManager
from codeforge_core.validator import ValidationService
from codeforge_core.safety_service import SafetyService
from codeforge_core.prompt_manager import PromptManager


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def cfg():
    return ConfigLoader()


def _mock_engine(cfg, reply="HealthMate response"):
    engine = AIEngine(config_loader=cfg, api_key="sk-test-fake")
    msg = MagicMock(); msg.content = reply
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = resp
    engine.set_client_for_testing(client)
    return engine


@pytest.fixture
def health_engine(cfg):
    return _mock_engine(cfg)


@pytest.fixture
def health_safety(cfg):
    return SafetyService(cfg.get_app_config("healthmate"))


# ── Safety – blocked requests ─────────────────────────────────────────────────

def test_diagnosis_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Can you diagnose my chest pain?")


def test_prescribe_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Please prescribe me antibiotics")


def test_do_i_have_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Do I have diabetes?")


def test_is_this_cancer_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Is this cancer?")


def test_emergency_keyword_blocked(health_safety):
    with pytest.raises(SafetyError, match="Emergency"):
        health_safety.check_input("I want to end my life")


def test_safe_question_passes(health_safety):
    health_safety.check_input("What does hypertension mean?")
    health_safety.check_input("How much water should I drink?")


# ── Safety – disclaimer ───────────────────────────────────────────────────────

def test_disclaimer_appended(health_safety):
    result = health_safety.build_response_with_disclaimer("Here is some info.")
    assert "Here is some info." in result
    assert "not a substitute for professional medical advice" in result


def test_disclaimer_on_every_response(health_safety):
    for text in ["Answer A", "Answer B", "Answer C"]:
        out = health_safety.build_response_with_disclaimer(text)
        assert "not a substitute" in out


# ── Validation ────────────────────────────────────────────────────────────────

def test_empty_message_raises():
    v = ValidationService()
    with pytest.raises(ValidationError):
        v.validate("")


def test_too_long_message_raises():
    v = ValidationService(max_length=100)
    with pytest.raises(ValidationError):
        v.validate("x" * 101)


# ── Conversation isolation ────────────────────────────────────────────────────

def test_health_edu_conversations_isolated():
    edu_convo    = ConversationManager()
    health_convo = ConversationManager()
    edu_convo.add_user_message("Explain calculus")
    health_convo.add_user_message("Explain hypertension")
    assert edu_convo.get_messages()[0]["content"] == "Explain calculus"
    assert health_convo.get_messages()[0]["content"] == "Explain hypertension"


def test_clear_conversation(health_engine):
    convo = ConversationManager()
    convo.add_user_message("Hello")
    convo.reset()
    assert convo.is_empty()


# ── Prompt ────────────────────────────────────────────────────────────────────

def test_health_prompt_registered():
    pm = PromptManager()
    pm.register("healthmate", "You are HealthMate AI.")
    assert pm.has("healthmate")


def test_health_prompt_includes_topic_context():
    pm = PromptManager()
    pm.register("healthmate", "Base.")
    prompt = pm.build_system_prompt("healthmate", {"topic_category": "Nutrition & Diet"})
    assert "Nutrition" in prompt


# ── AI engine integration ─────────────────────────────────────────────────────

def test_health_engine_generates_response(cfg, health_engine):
    pm = PromptManager()
    pm.register("healthmate", "You are HealthMate AI.")
    convo = ConversationManager()
    convo.add_user_message("What is a virus?")
    reply = health_engine.generate_response(
        system_prompt=pm.build_system_prompt("healthmate"),
        messages=convo.get_messages(),
        app_id="healthmate",
    )
    assert "HealthMate response" in reply


def test_missing_key_raises(cfg):
    engine = AIEngine(config_loader=cfg, api_key=None)
    with patch.object(engine, "get_api_key", return_value=None), \
         patch.object(engine, "is_ready", return_value=False):
        with pytest.raises(MissingAPIKeyError):
            engine.generate_response("sys", [{"role": "user", "content": "hi"}])


# ── Config ────────────────────────────────────────────────────────────────────

def test_health_config_loads(cfg):
    data = cfg.get_app_config("healthmate")
    assert data["app"]["id"] == "healthmate"
    assert "topic_categories" in data


def test_health_config_has_safety_rules(cfg):
    data = cfg.get_app_config("healthmate")
    assert "safety" in data
    assert "prohibited_requests" in data["safety"]
    assert len(data["safety"]["prohibited_requests"]) > 0


def test_health_config_has_emergency_message(cfg):
    data = cfg.get_app_config("healthmate")
    assert data["safety"].get("emergency_message", "") != ""
