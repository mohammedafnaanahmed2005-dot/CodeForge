"""Tests for ConversationManager and conversation isolation."""

import pytest
from core.conversation_manager import ConversationManager


def test_new_manager_is_empty():
    cm = ConversationManager()
    assert cm.is_empty()
    assert cm.turn_count() == 0


def test_add_user_message():
    cm = ConversationManager()
    cm.add_user_message("Hello")
    assert cm.turn_count() == 1
    msgs = cm.get_messages()
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello"


def test_add_assistant_message():
    cm = ConversationManager()
    cm.add_assistant_message("Hi there!")
    msgs = cm.get_messages()
    assert msgs[0]["role"] == "assistant"


def test_reset_clears_history():
    cm = ConversationManager()
    cm.add_user_message("Hello")
    cm.add_assistant_message("Hi")
    cm.reset()
    assert cm.is_empty()


def test_domain_isolation():
    """Conversations in different managers never share history."""
    edu_cm = ConversationManager()
    health_cm = ConversationManager()

    edu_cm.add_user_message("Explain calculus")
    health_cm.add_user_message("Explain hypertension")

    assert edu_cm.turn_count() == 1
    assert health_cm.turn_count() == 1
    assert edu_cm.get_messages()[0]["content"] == "Explain calculus"
    assert health_cm.get_messages()[0]["content"] == "Explain hypertension"


def test_max_turns_trimming():
    cm = ConversationManager()
    cm._max_turns = 4
    for i in range(6):
        cm.add_user_message(f"msg {i}")
    # Should be trimmed to last 4
    assert cm.turn_count() == 4
    assert cm.get_messages()[0]["content"] == "msg 2"


def test_messages_format():
    cm = ConversationManager()
    cm.add_user_message("Q")
    cm.add_assistant_message("A")
    msgs = cm.get_messages()
    assert all("role" in m and "content" in m for m in msgs)
