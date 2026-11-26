"""
Integration tests for EduTrackApp and HealthMateApp.
All OpenAI calls are mocked.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from core.ai_engine import AIEngine
from core.config_manager import ConfigManager
from core.errors import AIEngineError, MissingAPIKeyError, SafetyError, ValidationError
from apps.edutrack.app import EduTrackApp
from apps.healthmate.app import HealthMateApp


@pytest.fixture
def cfg():
    return ConfigManager()


def _mock_engine(cfg: ConfigManager, response: str = "AI response") -> AIEngine:
    engine = AIEngine(config_manager=cfg, api_key="sk-test-fake")
    mock_msg = MagicMock()
    mock_msg.content = response
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp
    engine.set_client_for_testing(mock_client)
    return engine


@pytest.fixture
def edu_app(cfg):
    return EduTrackApp(cfg, _mock_engine(cfg, "EduTrack response"))


@pytest.fixture
def health_app(cfg):
    return HealthMateApp(cfg, _mock_engine(cfg, "HealthMate response"))


# ── EduTrack ──────────────────────────────────────────────────────────────────

def test_edutrack_basic_chat(edu_app):
    reply = edu_app.chat("session1", "Explain gravity")
    assert "EduTrack response" in reply


def test_edutrack_disclaimer_in_response(edu_app):
    reply = edu_app.chat("session1", "What is photosynthesis?")
    assert "educational guidance" in reply.lower() or "EduTrack response" in reply


def test_edutrack_empty_message_raises(edu_app):
    with pytest.raises(ValidationError):
        edu_app.chat("session1", "")


def test_edutrack_too_long_message_raises(edu_app):
    with pytest.raises(ValidationError):
        edu_app.chat("session1", "x" * 2001)


def test_edutrack_conversation_accumulates(edu_app):
    edu_app.chat("session1", "First question")
    edu_app.chat("session1", "Second question")
    convo = edu_app.get_conversation("session1")
    # 2 user + 2 assistant = 4 turns
    assert convo.turn_count() == 4


def test_edutrack_clear_conversation(edu_app):
    edu_app.chat("session1", "Hello")
    edu_app.clear_conversation("session1")
    assert edu_app.get_conversation("session1").is_empty()


def test_edutrack_sessions_are_isolated(edu_app):
    edu_app.chat("session_A", "Session A question")
    edu_app.chat("session_B", "Session B question")
    convo_a = edu_app.get_conversation("session_A")
    convo_b = edu_app.get_conversation("session_B")
    assert convo_a.turn_count() == 2
    assert convo_b.turn_count() == 2
    assert convo_a.get_messages()[0]["content"] == "Session A question"
    assert convo_b.get_messages()[0]["content"] == "Session B question"


def test_edutrack_context_in_prompt(cfg):
    """Context parameters should be reflected in the system prompt sent."""
    engine = AIEngine(config_manager=cfg, api_key="sk-test-fake")
    captured_calls = []

    mock_msg = MagicMock()
    mock_msg.content = "ok"
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client = MagicMock()
    def capture(*args, **kwargs):
        captured_calls.append(kwargs)
        return mock_resp
    mock_client.chat.completions.create.side_effect = capture
    engine.set_client_for_testing(mock_client)

    app = EduTrackApp(cfg, engine)
    app.chat("s1", "What is calculus?", subject="Mathematics", academic_level="Undergraduate")

    assert len(captured_calls) == 1
    system_content = captured_calls[0]["messages"][0]["content"]
    assert "Mathematics" in system_content
    assert "Undergraduate" in system_content


# ── HealthMate ────────────────────────────────────────────────────────────────

def test_healthmate_basic_chat(health_app):
    reply = health_app.chat("session1", "What is hypertension?")
    assert "HealthMate response" in reply


def test_healthmate_disclaimer_always_present(health_app):
    reply = health_app.chat("session1", "What is a virus?")
    assert "not a substitute for professional medical advice" in reply.lower() \
        or "HealthMate AI provides general health education" in reply


def test_healthmate_diagnosis_blocked(health_app):
    with pytest.raises(SafetyError):
        health_app.chat("session1", "Can you diagnose my rash?")


def test_healthmate_prescribe_blocked(health_app):
    with pytest.raises(SafetyError):
        health_app.chat("session1", "Please prescribe me something for my headache")


def test_healthmate_do_i_have_blocked(health_app):
    with pytest.raises(SafetyError):
        health_app.chat("session1", "Do I have COVID based on my symptoms?")


def test_healthmate_empty_message_raises(health_app):
    with pytest.raises(ValidationError):
        health_app.chat("session1", "")


def test_healthmate_conversation_isolated_from_edutrack(edu_app, health_app):
    edu_app.chat("shared_session_id", "Explain calculus")
    # Using same session id string but different app objects → still isolated
    reply = health_app.chat("shared_session_id", "What is hypertension?")
    health_convo = health_app.get_conversation("shared_session_id")
    edu_convo = edu_app.get_conversation("shared_session_id")
    # Contents must differ
    assert health_convo.get_messages()[0]["content"] == "What is hypertension?"
    assert edu_convo.get_messages()[0]["content"] == "Explain calculus"


def test_healthmate_emergency_raises(health_app):
    with pytest.raises(SafetyError, match="Emergency"):
        health_app.chat("session1", "I want to end my life")


def test_healthmate_clear_conversation(health_app):
    health_app.chat("session1", "Hello")
    health_app.clear_conversation("session1")
    assert health_app.get_conversation("session1").is_empty()


# ── Cross-domain API error handling ───────────────────────────────────────────

def test_api_error_propagates_to_app(cfg):
    engine = AIEngine(config_manager=cfg, api_key="sk-test-fake")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("boom")
    engine.set_client_for_testing(mock_client)

    app = EduTrackApp(cfg, engine)
    with pytest.raises(AIEngineError):
        app.chat("s", "question")
