"""Tests for ConfigManager."""

import pytest
from core.config_manager import ConfigManager
from core.errors import ConfigError


@pytest.fixture
def cfg():
    return ConfigManager()


def test_framework_config_loads(cfg):
    data = cfg.get_framework_config()
    assert "framework" in data
    assert data["framework"]["name"] == "CodeForge AI"


def test_edutrack_config_loads(cfg):
    data = cfg.get_app_config("edutrack")
    assert data["app"]["id"] == "edutrack"
    assert "subjects" in data


def test_healthmate_config_loads(cfg):
    data = cfg.get_app_config("healthmate")
    assert data["app"]["id"] == "healthmate"
    assert "topic_categories" in data


def test_missing_config_raises(cfg):
    with pytest.raises(ConfigError):
        cfg.get_app_config("nonexistent_domain")


def test_openai_settings_fallback(cfg):
    settings = cfg.get_openai_settings()
    assert "model" in settings or "default_model" in settings


def test_openai_settings_app_override(cfg):
    settings = cfg.get_openai_settings("edutrack")
    assert "model" in settings


def test_cache_returns_same_object(cfg):
    a = cfg.get_framework_config()
    b = cfg.get_framework_config()
    assert a is b


def test_reload_clears_cache(cfg):
    _ = cfg.get_framework_config()
    cfg.reload()
    assert cfg._cache == {}


def test_available_apps_returns_list(cfg):
    apps = cfg.get_available_apps()
    assert isinstance(apps, list)
    assert len(apps) >= 2
    ids = [a["id"] for a in apps]
    assert "edutrack" in ids
    assert "healthmate" in ids
