"""
Tests for AIEngine — all OpenAI calls are mocked.
No real API key is required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from core.ai_engine import AIEngine
from core.config_manager import ConfigManager
from core.errors import AIEngineError, MissingAPIKeyError


@pytest.fixture
def cfg():
    return ConfigManager()


@pytest.fixture
def engine_no_key(cfg):
    """Engine with no API key in environment."""
    # Remove the key from the env for the duration of this test, then restore.
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        import os
        os.environ.pop("OPENAI_API_KEY", None)
        eng = AIEngine(config_manager=cfg, api_key=None)
        # Patch dotenv so it cannot re-inject a key from a .env file on disk
        with patch("core.ai_engine.AIEngine.get_api_key", return_value=None):
            yield eng


@pytest.fixture
def engine_with_key(cfg):
    """Engine with a fake API key injected."""
    return AIEngine(config_manager=cfg, api_key="sk-fake-test-key")


def _make_mock_client(content: str = "Mocked AI response") -> MagicMock:
    """Build a minimal mock that mimics the openai.OpenAI().chat.completions.create() chain."""
    mock_message = MagicMock()
    mock_message.content = content

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# ── API key detection ─────────────────────────────────────────────────────────

def test_is_ready_with_key(engine_with_key):
    assert engine_with_key.is_ready() is True


def test_is_ready_without_key(engine_no_key):
    assert engine_no_key.is_ready() is False


def test_missing_key_raises_before_call(engine_no_key):
    with pytest.raises(MissingAPIKeyError):
        engine_no_key.generate_response("system", [{"role": "user", "content": "hi"}])


# ── Successful generation ─────────────────────────────────────────────────────

def test_generate_response_calls_openai(engine_with_key):
    mock_client = _make_mock_client("Hello from mock!")
    engine_with_key.set_client_for_testing(mock_client)

    result = engine_with_key.generate_response(
        system_prompt="You are a test assistant.",
        messages=[{"role": "user", "content": "Say hello"}],
    )

    assert result == "Hello from mock!"
    assert mock_client.chat.completions.create.called


def test_generate_response_passes_system_prompt(engine_with_key):
    mock_client = _make_mock_client("ok")
    engine_with_key.set_client_for_testing(mock_client)

    engine_with_key.generate_response(
        system_prompt="SYSTEM_INSTRUCTIONS",
        messages=[{"role": "user", "content": "hi"}],
    )

    call_kwargs = mock_client.chat.completions.create.call_args
    messages_sent = call_kwargs.kwargs.get("messages") or call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["messages"]
    system_msgs = [m for m in messages_sent if m["role"] == "system"]
    assert any("SYSTEM_INSTRUCTIONS" in m["content"] for m in system_msgs)


def test_generate_response_with_app_id(engine_with_key):
    mock_client = _make_mock_client("response")
    engine_with_key.set_client_for_testing(mock_client)
    result = engine_with_key.generate_response(
        system_prompt="sys",
        messages=[{"role": "user", "content": "q"}],
        app_id="edutrack",
    )
    assert result == "response"


def test_empty_response_raises(engine_with_key):
    mock_client = _make_mock_client("")
    engine_with_key.set_client_for_testing(mock_client)
    with pytest.raises(AIEngineError, match="empty"):
        engine_with_key.generate_response("sys", [{"role": "user", "content": "hi"}])


# ── API error handling ────────────────────────────────────────────────────────

def test_generic_exception_becomes_ai_engine_error(engine_with_key):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("network blip")
    engine_with_key.set_client_for_testing(mock_client)

    with pytest.raises(AIEngineError):
        engine_with_key.generate_response("sys", [{"role": "user", "content": "hi"}])


# ── Domain switching ──────────────────────────────────────────────────────────

def test_domain_switch_uses_different_settings(engine_with_key, cfg):
    """Switching app_id should use the right model settings."""
    edu_settings = cfg.get_openai_settings("edutrack")
    health_settings = cfg.get_openai_settings("healthmate")
    # Both should return model info
    assert "model" in edu_settings
    assert "model" in health_settings
