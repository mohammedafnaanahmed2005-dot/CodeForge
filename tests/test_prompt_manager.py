"""Tests for PromptManager and domain prompt selection."""

import pytest
from core.prompt_manager import PromptManager


@pytest.fixture
def pm():
    return PromptManager()


def test_register_and_build(pm):
    pm.register("edutrack", "You are EduTrack AI.")
    prompt = pm.build_system_prompt("edutrack")
    assert "EduTrack" in prompt


def test_build_with_context(pm):
    pm.register("edutrack", "Base prompt.")
    prompt = pm.build_system_prompt(
        "edutrack",
        {"subject": "Mathematics", "academic_level": "High School"},
    )
    assert "Base prompt." in prompt
    assert "Subject: Mathematics" in prompt
    assert "Academic Level: High School" in prompt


def test_context_with_empty_values_ignored(pm):
    pm.register("edutrack", "Base.")
    prompt = pm.build_system_prompt("edutrack", {"subject": "", "level": "X"})
    # Empty-value keys must not appear; non-empty ones must
    assert "Subject:" not in prompt
    assert "Level: X" in prompt


def test_unknown_app_raises(pm):
    with pytest.raises(KeyError, match="No system prompt"):
        pm.build_system_prompt("unknown_app")


def test_has(pm):
    pm.register("healthmate", "Health prompt.")
    assert pm.has("healthmate")
    assert not pm.has("edutrack")


def test_domain_prompts_are_distinct():
    """EduTrack and HealthMate prompts must be different."""
    from apps.edutrack.prompts import SYSTEM_PROMPT as EDU
    from apps.healthmate.prompts import SYSTEM_PROMPT as HEALTH

    assert EDU != HEALTH
    assert "EduTrack" in EDU
    assert "HealthMate" in HEALTH
    # Health prompt contains the mandatory safety rules
    assert "NEVER diagnose" in HEALTH
    assert "NEVER prescribe" in HEALTH
