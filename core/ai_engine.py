"""
AIEngine – reusable interface for communicating with AI providers.

Supports multiple OpenAI-compatible providers.  NVIDIA NIM is used as the
primary provider when NVIDIA_API_KEY is present; OpenRouter (OPENAI_API_KEY)
is the fallback.  Domain apps never reference providers directly — they just
call generate_response() and the engine handles routing transparently.
"""

from __future__ import annotations

import os
from typing import Any

from core.config_manager import ConfigManager
from core.error_handler import ErrorHandler
from core.errors import AIEngineError, MissingAPIKeyError


class AIEngine:
    """
    Multi-provider AI engine.  Priority order:
      1. NVIDIA NIM  (NVIDIA_API_KEY)
      2. OpenRouter  (OPENAI_API_KEY)
    """

    _NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    _NVIDIA_FALLBACK_MODEL = "nvidia/nemotron-3.5-bolt-e4b"
    _OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    _OPENROUTER_FALLBACK_MODEL = "nvidia/nemotron-3.5-super-vl:free"

    def __init__(
        self,
        config_manager: ConfigManager,
        api_key: str | None = None,
    ) -> None:
        self._cfg = config_manager
        self._explicit_key = api_key
        # One cached client per (base_url, key) pair
        self._clients: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_nvidia_key(self) -> str | None:
        """Return the NVIDIA NIM API key if available."""
        self._load_dotenv()
        return os.environ.get("NVIDIA_API_KEY") or None

    def get_api_key(self) -> str | None:
        """
        Return whichever key is available (NVIDIA first, then OpenRouter).
        Used by is_ready() and tests.
        """
        if self._explicit_key:
            return self._explicit_key
        self._load_dotenv()
        return (
            os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or None
        )

    def is_ready(self) -> bool:
        """True when at least one API key is available."""
        return bool(self.get_api_key())

    def generate_response(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        app_id: str | None = None,
    ) -> str:
        """
        Generate a response, trying providers in priority order.

        Provider 1 – NVIDIA NIM (if NVIDIA_API_KEY present)
        Provider 2 – OpenRouter (if OPENAI_API_KEY present)

        Within each provider, also retries the OpenRouter free-tier
        fallback model on 429 rate-limit errors.
        """
        if not self.is_ready():
            raise MissingAPIKeyError(
                "No API key found. Add NVIDIA_API_KEY or OPENAI_API_KEY "
                "to your .env file or Streamlit secrets."
            )

        settings = self._cfg.get_openai_settings(app_id)
        temperature = settings.get("temperature", 0.7)
        max_tokens  = settings.get("max_tokens", 1024)
        timeout     = settings.get("timeout", 30)
        app_model   = settings.get("model", "")

        # Build the ordered list of (base_url, api_key, model) attempts
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
                # Empty response — try next attempt
                last_exc = AIEngineError("The model returned an empty response.")
                continue

            except AIEngineError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                # Retry next attempt on rate-limit or empty-response conditions
                if "429" in str(exc) or "rate" in str(exc).lower() or "502" in str(exc):
                    continue
                # Any other error — translate and raise immediately
                ErrorHandler.handle(exc)

        # All attempts exhausted
        if last_exc:
            ErrorHandler.handle(last_exc)
        raise AIEngineError("All AI providers failed to return a response.")

    def set_client_for_testing(self, client: Any) -> None:
        """Inject a mock client (used by unit tests)."""
        self._clients["__test__"] = client
        # Also set as default so _get_client returns it for any base_url
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
        """
        Return an ordered list of (base_url, key, model, temp, tokens, timeout)
        tuples to try in sequence.
        """
        self._load_dotenv()
        fw = self._cfg.get_framework_config()
        nvidia_cfg     = fw.get("nvidia", {})
        nvidia_key     = os.environ.get("NVIDIA_API_KEY") or None
        openrouter_key = os.environ.get("OPENAI_API_KEY") or None

        attempts = []

        # 1 – NVIDIA NIM (primary)
        if nvidia_key:
            nvidia_model = (
                app_model if app_model else nvidia_cfg.get("model", self._NVIDIA_FALLBACK_MODEL)
            )
            attempts.append((
                nvidia_cfg.get("base_url", self._NVIDIA_BASE_URL),
                nvidia_key,
                nvidia_model,
                nvidia_cfg.get("temperature", temperature),
                nvidia_cfg.get("max_tokens", max_tokens),
                nvidia_cfg.get("timeout", timeout),
            ))

        # 2 – OpenRouter primary free model
        if openrouter_key:
            attempts.append((
                self._OPENROUTER_BASE_URL,
                openrouter_key,
                self._OPENROUTER_FALLBACK_MODEL,
                temperature,
                max_tokens,
                timeout,
            ))
            # 3 – OpenRouter secondary free model
            attempts.append((
                self._OPENROUTER_BASE_URL,
                openrouter_key,
                "particle-ai/particle-1:free",
                temperature,
                max_tokens,
                timeout,
            ))

        return attempts

    def _get_client(self, base_url: str, api_key: str, timeout: int) -> Any:
        """Return a cached OpenAI-compatible client for (base_url, key)."""
        # Allow test injection
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
        """Load .env once; subsequent calls are no-ops via dotenv's internals."""
        try:
            from dotenv import load_dotenv  # noqa: PLC0415
            load_dotenv(override=False)
        except ImportError:
            pass
