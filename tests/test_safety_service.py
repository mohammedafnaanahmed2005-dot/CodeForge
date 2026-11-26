"""Tests for SafetyService (mostly healthcare safety)."""

import pytest
from core.safety_service import SafetyService
from core.errors import SafetyError
from core.config_manager import ConfigManager


@pytest.fixture
def health_safety():
    cfg = ConfigManager()
    return SafetyService(cfg.get_app_config("healthmate"))


@pytest.fixture
def edu_safety():
    cfg = ConfigManager()
    return SafetyService(cfg.get_app_config("edutrack"))


# ── Healthcare safety ─────────────────────────────────────────────────────────

def test_diagnosis_request_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Can you diagnose my chest pain?")


def test_prescribe_request_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Please prescribe me antibiotics for my infection")


def test_do_i_have_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Do I have diabetes based on my symptoms?")


def test_is_this_cancer_blocked(health_safety):
    with pytest.raises(SafetyError):
        health_safety.check_input("Is this cancer on my skin?")


def test_suicide_triggers_emergency(health_safety):
    with pytest.raises(SafetyError, match="Emergency"):
        health_safety.check_input("I want to commit suicide")


def test_self_harm_triggers_emergency(health_safety):
    with pytest.raises(SafetyError, match="Emergency"):
        health_safety.check_input("I am thinking about self.harm")


def test_safe_health_question_passes(health_safety):
    # Should not raise
    health_safety.check_input("What does hypertension mean?")
    health_safety.check_input("How much water should I drink daily?")


def test_medical_disclaimer_appended(health_safety):
    result = health_safety.build_response_with_disclaimer("Drink 8 glasses a day.")
    assert "Drink 8 glasses" in result
    assert "HealthMate AI provides general health education" in result
    assert result.startswith("Drink 8 glasses")


def test_disclaimer_on_every_response(health_safety):
    for r in ["Answer 1", "Answer 2", "Answer 3"]:
        out = health_safety.build_response_with_disclaimer(r)
        assert "not a substitute for professional medical advice" in out


# ── Education safety ──────────────────────────────────────────────────────────

def test_edu_suicide_also_triggers_emergency(edu_safety):
    with pytest.raises(SafetyError, match="Emergency"):
        edu_safety.check_input("kill myself thoughts")


def test_edu_normal_question_passes(edu_safety):
    edu_safety.check_input("Explain the Pythagorean theorem")


def test_edu_disclaimer_appended(edu_safety):
    out = edu_safety.build_response_with_disclaimer("The answer is 42.")
    assert "educational guidance" in out
