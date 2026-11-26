"""
ConfigManager – loads YAML configuration files for the framework and
individual domain applications.  All callers share a single instance
so YAML files are only read from disk once per session.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from core.errors import ConfigError


class ConfigManager:
    """
    Load and expose configuration for the framework and each domain app.

    Usage::

        cfg = ConfigManager()
        fw  = cfg.get_framework_config()
        edu = cfg.get_app_config("edutrack")
    """

    # Relative to the project root (parent of core/)
    _CONFIG_DIR = Path(__file__).parent.parent / "config"

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_framework_config(self) -> dict[str, Any]:
        """Return the framework-level configuration."""
        return self._load("framework")

    def get_app_config(self, app_id: str) -> dict[str, Any]:
        """Return the configuration for *app_id* (e.g. ``"edutrack"``)."""
        return self._load(app_id)

    def get_available_apps(self) -> list[dict[str, str]]:
        """Return the list of registered applications from framework config."""
        fw = self.get_framework_config()
        return fw.get("applications", [])

    def get_openai_settings(self, app_id: str | None = None) -> dict[str, Any]:
        """
        Return OpenAI settings.  App-level settings override framework
        defaults when *app_id* is provided.
        """
        fw = self.get_framework_config().get("openai", {})
        if app_id is None:
            return fw
        app_openai = self.get_app_config(app_id).get("openai", {})
        return {**fw, **app_openai}

    def reload(self) -> None:
        """Clear the in-memory cache so files are re-read on next access."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, name: str) -> dict[str, Any]:
        if name in self._cache:
            return self._cache[name]

        path = self._CONFIG_DIR / f"{name}.yaml"
        if not path.exists():
            raise ConfigError(
                f"Configuration file not found: {path}. "
                "Ensure the config/ directory contains the required YAML files."
            )
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse {path}: {exc}") from exc

        self._cache[name] = data
        return data
