"""Tests for ValidationService."""

import pytest
from core.validation_service import ValidationService
from core.errors import ValidationError


@pytest.fixture
def validator():
    return ValidationService(max_length=200, min_length=1)


def test_valid_message_passes(validator):
    result = validator.validate("What is photosynthesis?")
    assert result == "What is photosynthesis?"


def test_whitespace_stripped(validator):
    result = validator.validate("  hello  ")
    assert result == "hello"


def test_empty_string_raises(validator):
    with pytest.raises(ValidationError, match="empty"):
        validator.validate("")


def test_whitespace_only_raises(validator):
    with pytest.raises(ValidationError, match="empty"):
        validator.validate("   ")


def test_too_long_raises(validator):
    with pytest.raises(ValidationError, match="too long"):
        validator.validate("x" * 201)


def test_exact_max_length_passes(validator):
    result = validator.validate("a" * 200)
    assert len(result) == 200


def test_non_string_raises(validator):
    with pytest.raises(ValidationError):
        validator.validate(None)  # type: ignore


def test_validate_app_config_passes():
    svc = ValidationService()
    svc.validate_app_config({"app": {}, "openai": {}})


def test_validate_app_config_missing_key_raises():
    svc = ValidationService()
    with pytest.raises(ValidationError, match="missing required keys"):
        svc.validate_app_config({"app": {}})
