"""
ConfigLoader – loads and caches YAML configuration files.

Replaces the old ConfigManager.  Both names are supported for backward
compatibility; ``ConfigLoader`` is the canonical name going forward.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from codeforge_core.errors import ConfigError


class ConfigLoader:
    """
    Load and expose configuration for the framework and each domain app.

    Config files are resolved relative to a base directory supplied at
    construction time (defaults to the ``config/`` folder at the project
    root so both standalone runs and ``pytest`` work without extra setup).

    Usage::

        cfg = ConfigLoader()
        fw  = cfg.get_framework_config()
        edu = cfg.get_app_config("edutrack_ai")
    """

    _DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "config"

    def __init__(self, config_dir: Path | str | None = None) -> None:
        self._config_dir = Path(config_dir) if config_dir else self._DEFAULT_CONFIG_DIR
        self._cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_framework_config(self) -> dict[str, Any]:
        return self._load("framework")

    def get_app_config(self, app_id: str) -> dict[str, Any]:
        """Return config for *app_id*.  Accepts both ``edutrack`` and
        ``edutrack_ai`` as the key."""
        # normalise: strip trailing _ai so old yaml names still work
        normalised = app_id.replace("_ai", "")
        return self._load(normalised)

    def get_available_apps(self) -> list[dict[str, str]]:
        return self.get_framework_config().get("applications", [])

    def get_openai_settings(self, app_id: str | None = None) -> dict[str, Any]:
        fw = self.get_framework_config().get("openai", {})
        if app_id is None:
            return fw
        app_openai = self.get_app_config(app_id).get("openai", {})
        return {**fw, **app_openai}

    def reload(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, name: str) -> dict[str, Any]:
        if name in self._cache:
            return self._cache[name]

        path = self._config_dir / f"{name}.yaml"
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


# Backward-compatible alias
ConfigManager = ConfigLoader
