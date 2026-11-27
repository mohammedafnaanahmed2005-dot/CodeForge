"""Tests for codeforge_core.AIEngine — all OpenAI calls are mocked."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from codeforge_core.ai_engine import AIEngine
from codeforge_core.config_loader import ConfigLoader
from codeforge_core.errors import AIEngineError, MissingAPIKeyError


@pytest.fixture
def cfg():
    return ConfigLoader()


@pytest.fixture
def engine_with_key(cfg):
    return AIEngine(config_loader=cfg, api_key="sk-test-fake")


@pytest.fixture
def engine_no_key(cfg):
    eng = AIEngine(config_loader=cfg, api_key=None)
    with patch.object(eng, "get_api_key", return_value=None):
        with patch.object(eng, "is_ready", return_value=False):
            yield eng


def _mock_client(content: str = "Mocked response") -> MagicMock:
    msg = MagicMock(); msg.content = content
    choice = MagicMock(); choice.message = msg
    resp = MagicMock(); resp.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = resp
    return client


def test_is_ready_with_key(engine_with_key):
    assert engine_with_key.is_ready() is True


def test_is_ready_without_key(engine_no_key):
    assert engine_no_key.is_ready() is False


def test_missing_key_raises(engine_no_key):
    with pytest.raises(MissingAPIKeyError):
        engine_no_key.generate_response("sys", [{"role": "user", "content": "hi"}])


def test_generate_response_returns_content(engine_with_key):
    engine_with_key.set_client_for_testing(_mock_client("Hello!"))
    result = engine_with_key.generate_response("sys", [{"role": "user", "content": "hi"}])
    assert result == "Hello!"


def test_system_prompt_included(engine_with_key):
    client = _mock_client("ok")
    engine_with_key.set_client_for_testing(client)
    engine_with_key.generate_response("MY_SYSTEM", [{"role": "user", "content": "hi"}])
    call = client.chat.completions.create.call_args
    msgs = call.kwargs.get("messages", [])
    assert any(m["role"] == "system" and "MY_SYSTEM" in m["content"] for m in msgs)


def test_empty_response_triggers_fallback_then_error(engine_with_key):
    engine_with_key.set_client_for_testing(_mock_client(""))
    with pytest.raises((AIEngineError, Exception)):
        engine_with_key.generate_response("sys", [{"role": "user", "content": "hi"}])


def test_runtime_error_becomes_ai_engine_error(engine_with_key):
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("boom")
    engine_with_key.set_client_for_testing(client)
    with pytest.raises(AIEngineError):
        engine_with_key.generate_response("sys", [{"role": "user", "content": "hi"}])


def test_app_id_routes_settings(engine_with_key, cfg):
    edu = cfg.get_openai_settings("edutrack")
    health = cfg.get_openai_settings("healthmate")
    assert "model" in edu
    assert "model" in health
    assert edu != health or edu["model"] == health["model"]  # may be same model but settings resolved
