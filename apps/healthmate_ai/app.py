"""
HealthMate AI – Standalone Streamlit entry point.

Run:
    streamlit run apps/healthmate_ai/app.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)
except ImportError:
    pass

if hasattr(st, "secrets"):
    try:
        for _k in ("OPENAI_API_KEY", "NVIDIA_API_KEY"):
            if _k in st.secrets:
                os.environ.setdefault(_k, st.secrets[_k])
    except Exception:
        pass

from codeforge_core import (
    AIEngine, PromptManager,
    ConversationManager, ValidationService, SafetyService,
    AIEngineError, MissingAPIKeyError, SafetyError, ValidationError,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HealthMate AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.big-title { font-size: 2.4rem; font-weight: 800; }
.sub-title  { font-size: 1rem; color: #aaa; margin-bottom: 1.2rem; }
</style>
""", unsafe_allow_html=True)

_APP_DIR = Path(__file__).parent


class _HealthConfig:
    def __init__(self) -> None:
        import yaml
        with open(_APP_DIR / "config.yaml", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def get_framework_config(self):
        import yaml
        with open(_ROOT / "config" / "framework.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_app_config(self, app_id: str):
        return self._data

    def get_openai_settings(self, app_id=None):
        fw = self.get_framework_config().get("openai", {})
        return {**fw, **self._data.get("openai", {})}


@st.cache_resource
def _build():
    cfg    = _HealthConfig()
    engine = AIEngine(config_loader=cfg)
    return cfg, engine


cfg, engine = _build()

SYSTEM_PROMPT = """You are HealthMate AI, a general health information assistant built on the CodeForge AI framework.

Your purpose is to provide educational health information, explain medical terminology, support doctor appointment preparation, and promote general wellness awareness. You are NOT a doctor and do not replace professional medical consultation.

CORE CAPABILITIES:
- Explain medical terminology in plain, accessible language
- Provide general wellness, nutrition, and fitness information
- Help users prepare for doctor appointments
- Summarise general health topics from reputable public health perspectives

ABSOLUTE RULES – never violate these:
1. NEVER diagnose medical conditions
2. NEVER prescribe or recommend medication changes
3. NEVER give personalised medical treatment advice
4. ALWAYS encourage users to consult qualified healthcare providers
5. ALWAYS recommend emergency services for potentially life-threatening symptoms

TONE: Professional, calm, supportive, and informative.
"""

if "health_messages" not in st.session_state:
    st.session_state["health_messages"] = []
if "health_session" not in st.session_state:
    st.session_state["health_session"] = "health_main"

_conversations: dict[str, ConversationManager] = {}


def _get_convo(session_id: str) -> ConversationManager:
    if session_id not in _conversations:
        _conversations[session_id] = ConversationManager()
    return _conversations[session_id]


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, MissingAPIKeyError):
        st.error(f"🔑 **API Key Missing**\n\n{exc}")
    elif isinstance(exc, ValidationError):
        st.warning(f"⚠️ **Input Error**\n\n{exc}")
    elif isinstance(exc, SafetyError):
        st.warning(f"🛡️ **Safety Notice**\n\n{exc}")
    elif isinstance(exc, AIEngineError):
        st.error(f"🤖 **AI Error**\n\n{exc}")
    else:
        st.error(f"❌ **Error**\n\n{exc}")


def _send(text: str, topic: str) -> None:
    validator = ValidationService(max_length=2000)
    safety    = SafetyService(cfg.get_app_config("healthmate"))
    pm        = PromptManager()
    pm.register("healthmate", SYSTEM_PROMPT)

    try:
        clean = validator.validate(text)
        safety.check_input(clean)

        context    = {"topic_category": topic} if topic and topic != "(General)" else None
        sys_prompt = pm.build_system_prompt("healthmate", context)

        convo = _get_convo(st.session_state["health_session"])
        convo.add_user_message(clean)
        st.session_state["health_messages"].append({"role": "user", "content": clean})

        with st.spinner("HealthMate AI is thinking…"):
            reply = engine.generate_response(
                system_prompt=sys_prompt,
                messages=convo.get_messages(),
                app_id="healthmate",
            )

        disclaimer = cfg.get("safety", {}).get("medical_disclaimer", "")
        final = f"{reply}\n\n---\n*{disclaimer}*" if disclaimer else reply
        convo.add_assistant_message(final)
        st.session_state["health_messages"].append({"role": "assistant", "content": final})

    except Exception as exc:  # noqa: BLE001
        _handle_error(exc)
        if st.session_state["health_messages"] and st.session_state["health_messages"][-1]["role"] == "user":
            st.session_state["health_messages"].pop()

    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 HealthMate AI")
    st.markdown("*General health education*")
    st.markdown("---")

    topic = st.selectbox(
        "🏷️ Topic Category",
        ["(General)"] + cfg.get("topic_categories", []),
    )

    st.markdown("---")
    st.markdown("**💡 Example Questions**")
    for q in cfg.get("example_questions", []):
        if st.button(q, key=f"hq_{q[:18]}", use_container_width=True):
            _send(q, topic)

    st.markdown("---")
    st.info(
        "⚕️ HealthMate AI provides **general health education only**.\n\n"
        "It does not diagnose conditions or prescribe treatment.\n\n"
        "Always consult a qualified healthcare provider."
    )

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        _get_convo(st.session_state["health_session"]).reset()
        st.session_state["health_messages"] = []
        st.rerun()

    if engine.is_ready():
        if engine.get_nvidia_key():
            st.success("✅ NVIDIA NIM active")
        else:
            st.success("✅ OpenRouter active")
    else:
        st.error("❌ No API key found")

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<p class="big-title">🏥 HealthMate AI</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Topic: <b>{topic}</b></p>', unsafe_allow_html=True)
st.markdown("---")

for msg in st.session_state["health_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state["health_messages"]:
    st.info("Ask HealthMate AI a health question. Remember: this is educational information only.")

user_input = st.chat_input("Ask HealthMate AI…")
if user_input:
    _send(user_input, topic)
