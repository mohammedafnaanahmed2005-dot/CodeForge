"""
AIEngine – multi-provider AI engine for the CodeForge framework.

Provider priority:
  1. NVIDIA NIM   (NVIDIA_API_KEY)
  2. OpenRouter   (OPENAI_API_KEY)

Domain apps call generate_response() only; provider selection is
transparent and automatic.
"""

from __future__ import annotations

import os
from typing import Any

from codeforge_core.config_loader import ConfigLoader
from codeforge_core.error_handler import ErrorHandler
from codeforge_core.errors import AIEngineError, MissingAPIKeyError


class AIEngine:
    """Multi-provider, domain-agnostic AI response engine."""

    _NVIDIA_BASE_URL       = "https://integrate.api.nvidia.com/v1"
    _NVIDIA_DEFAULT_MODEL  = "nvidia/nemotron-3.5-bolt-e4b"
    _OR_BASE_URL           = "https://openrouter.ai/api/v1"
    _OR_PRIMARY_MODEL      = "nvidia/nemotron-3.5-super-vl:free"
    _OR_FALLBACK_MODEL     = "particle-ai/particle-1:free"

    def __init__(
        self,
        config_loader: ConfigLoader,
        api_key: str | None = None,
    ) -> None:
        self._cfg = config_loader
        self._explicit_key = api_key
        self._clients: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_nvidia_key(self) -> str | None:
        self._load_dotenv()
        return os.environ.get("NVIDIA_API_KEY") or None

    def get_api_key(self) -> str | None:
        if self._explicit_key:
            return self._explicit_key
        self._load_dotenv()
        return (
            os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or None
        )

    def is_ready(self) -> bool:
        return bool(self.get_api_key())

    def generate_response(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        app_id: str | None = None,
    ) -> str:
        """Generate a response, trying providers in priority order."""
        if not self.is_ready():
            raise MissingAPIKeyError(
                "No API key found. Add NVIDIA_API_KEY or OPENAI_API_KEY "
                "to your .env file or Streamlit secrets."
            )

        settings    = self._cfg.get_openai_settings(app_id)
        temperature = settings.get("temperature", 0.7)
        max_tokens  = settings.get("max_tokens", 1024)
        timeout     = settings.get("timeout", 30)
        app_model   = settings.get("model", "")

        attempts = self._build_attempts(app_model, temperature, max_tokens, timeout)

        last_exc: Exception | None = None
        for base_url, key, model, temp, tokens, tout in attempts:
            try:
                client = self._get_client(base_url, key, tout)
                response = client.chat.completions.create(
                    model=model,
                    temperature=temp,
                    max_tokens=tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *messages,
                    ],
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
                last_exc = AIEngineError("The model returned an empty response.")
                continue

            except AIEngineError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if "429" in str(exc) or "rate" in str(exc).lower() or "502" in str(exc):
                    continue
                ErrorHandler.handle(exc)

        if last_exc:
            ErrorHandler.handle(last_exc)
        raise AIEngineError("All AI providers failed to return a response.")

    def set_client_for_testing(self, client: Any) -> None:
        """Inject a mock client used by unit tests."""
        self._clients["__default__"] = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_attempts(
        self,
        app_model: str,
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> list[tuple]:
        self._load_dotenv()
        fw         = self._cfg.get_framework_config()
        nvidia_cfg = fw.get("nvidia", {})
        nvidia_key = os.environ.get("NVIDIA_API_KEY") or None
        or_key     = os.environ.get("OPENAI_API_KEY") or None

        attempts = []

        if nvidia_key:
            model = app_model or nvidia_cfg.get("model", self._NVIDIA_DEFAULT_MODEL)
            attempts.append((
                nvidia_cfg.get("base_url", self._NVIDIA_BASE_URL),
                nvidia_key,
                model,
                nvidia_cfg.get("temperature", temperature),
                nvidia_cfg.get("max_tokens", max_tokens),
                nvidia_cfg.get("timeout", timeout),
            ))

        if or_key:
            attempts.append((self._OR_BASE_URL, or_key, self._OR_PRIMARY_MODEL,
                              temperature, max_tokens, timeout))
            attempts.append((self._OR_BASE_URL, or_key, self._OR_FALLBACK_MODEL,
                              temperature, max_tokens, timeout))

        return attempts

    def _get_client(self, base_url: str, api_key: str, timeout: int) -> Any:
        if "__default__" in self._clients:
            return self._clients["__default__"]

        cache_key = f"{base_url}::{api_key[:16]}"
        if cache_key not in self._clients:
            import openai  # noqa: PLC0415
            self._clients[cache_key] = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
            )
        return self._clients[cache_key]

    @staticmethod
    def _load_dotenv() -> None:
        try:
            from dotenv import load_dotenv  # noqa: PLC0415
            load_dotenv(override=False)
        except ImportError:
            pass
