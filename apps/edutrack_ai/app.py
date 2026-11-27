"""
EduTrack AI – Standalone Streamlit entry point.

Run:
    streamlit run apps/edutrack_ai/app.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Project root on sys.path so codeforge_core is importable from anywhere
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# Load .env before cache is built
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)
except ImportError:
    pass

# Inject Streamlit Cloud secrets
if hasattr(st, "secrets"):
    try:
        for _k in ("OPENAI_API_KEY", "NVIDIA_API_KEY"):
            if _k in st.secrets:
                os.environ.setdefault(_k, st.secrets[_k])
    except Exception:
        pass

from codeforge_core import (
    AIEngine, ConfigLoader, PromptManager,
    ConversationManager, ValidationService, SafetyService,
    AIEngineError, MissingAPIKeyError, SafetyError, ValidationError,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduTrack AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.big-title { font-size: 2.4rem; font-weight: 800; }
.sub-title  { font-size: 1rem; color: #aaa; margin-bottom: 1.2rem; }
.msg-user  { background:#252b40; border-radius:10px 10px 0 10px; padding:.7rem 1rem; margin:.3rem 0; }
.msg-bot   { background:#1A1F2E; border:1px solid #2d3550; border-radius:10px 10px 10px 0; padding:.7rem 1rem; margin:.3rem 0; }
</style>
""", unsafe_allow_html=True)

# ── App config dir points to this app's own config.yaml ──────────────────────
_APP_DIR = Path(__file__).parent


class _EduConfig:
    """Thin config wrapper that reads this app's own config.yaml."""
    def __init__(self) -> None:
        import yaml
        with open(_APP_DIR / "config.yaml", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def get(self, key, default=None):
        return self._data.get(key, default)

    # Mimic ConfigLoader interface used by AIEngine
    def get_framework_config(self):
        import yaml
        with open(_ROOT / "config" / "framework.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_app_config(self, app_id: str):
        return self._data

    def get_openai_settings(self, app_id=None):
        fw = self.get_framework_config().get("openai", {})
        return {**fw, **self._data.get("openai", {})}


# ── Shared singletons ─────────────────────────────────────────────────────────
@st.cache_resource
def _build():
    cfg    = _EduConfig()
    engine = AIEngine(config_loader=cfg)
    return cfg, engine


cfg, engine = _build()

SYSTEM_PROMPT = """You are EduTrack AI, an expert academic assistant built on the CodeForge AI framework.

Your purpose is to help students learn effectively through clear explanations, guided practice, and personalised study strategies.

CORE CAPABILITIES:
- Explain academic concepts clearly, adjusting depth to the student's level
- Answer subject-specific questions across mathematics, sciences, humanities, and technology
- Generate quizzes and practice problems with worked solutions
- Summarise textbook passages, lecture notes, or study material
- Create structured, realistic study plans tailored to deadlines
- Offer memory techniques, mnemonics, and study strategies

COMMUNICATION GUIDELINES:
- Match language complexity to the academic level provided
- For ADHD learners: be concise, use bullet points
- For dyslexic learners: plain language, short sentences
- For ESL learners: clear language, avoid idioms
- Never complete assignments or exams on behalf of students; guide them toward the answer
"""

# ── Session state ─────────────────────────────────────────────────────────────
if "edu_messages" not in st.session_state:
    st.session_state["edu_messages"] = []
if "edu_session" not in st.session_state:
    st.session_state["edu_session"] = "edu_main"


# ── Helpers ───────────────────────────────────────────────────────────────────
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


def _send(text: str, subject: str, level: str, difficulty: str, assistance: str) -> None:
    validator = ValidationService(max_length=2000)
    safety    = SafetyService(cfg.get_app_config("edutrack"))
    pm        = PromptManager()
    pm.register("edutrack", SYSTEM_PROMPT)

    try:
        clean = validator.validate(text)
        safety.check_input(clean)
        context = {"subject": subject, "academic_level": level,
                   "learning_difficulty": difficulty, "assistance_type": assistance}
        sys_prompt = pm.build_system_prompt("edutrack", context)

        convo = _get_convo(st.session_state["edu_session"])
        convo.add_user_message(clean)
        st.session_state["edu_messages"].append({"role": "user", "content": clean})

        with st.spinner("EduTrack AI is thinking…"):
            reply = engine.generate_response(
                system_prompt=sys_prompt,
                messages=convo.get_messages(),
                app_id="edutrack",
            )

        disclaimer = cfg.get("safety", {}).get("disclaimer", "")
        final = f"{reply}\n\n---\n*{disclaimer}*" if disclaimer else reply
        convo.add_assistant_message(final)
        st.session_state["edu_messages"].append({"role": "assistant", "content": final})

    except Exception as exc:  # noqa: BLE001
        _handle_error(exc)
        if st.session_state["edu_messages"] and st.session_state["edu_messages"][-1]["role"] == "user":
            st.session_state["edu_messages"].pop()

    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 EduTrack AI")
    st.markdown("*Personalise your learning*")
    st.markdown("---")

    subject    = st.selectbox("📚 Subject",          cfg.get("subjects", []))
    level      = st.selectbox("🎯 Academic Level",   cfg.get("academic_levels", []), index=2)
    difficulty = st.selectbox("🧠 Learning Profile", cfg.get("learning_difficulties", []))
    assistance = st.selectbox("🛠️ Assistance Type",  cfg.get("assistance_types", []))

    st.markdown("---")
    st.markdown("**💡 Example Questions**")
    for q in cfg.get("example_questions", []):
        if st.button(q, key=f"eq_{q[:18]}", use_container_width=True):
            _send(q, subject, level, difficulty, assistance)

    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        _get_convo(st.session_state["edu_session"]).reset()
        st.session_state["edu_messages"] = []
        st.rerun()

    if engine.is_ready():
        if engine.get_nvidia_key():
            st.success("✅ NVIDIA NIM active")
        else:
            st.success("✅ OpenRouter active")
    else:
        st.error("❌ No API key found")

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown('<p class="big-title">🎓 EduTrack AI</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub-title">Subject: <b>{subject}</b> · Level: <b>{level}</b> · Mode: <b>{assistance}</b></p>', unsafe_allow_html=True)
st.markdown("---")

for msg in st.session_state["edu_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state["edu_messages"]:
    st.info("Ask EduTrack AI anything academic. Use the sidebar to set your subject and level.")

user_input = st.chat_input("Ask EduTrack AI…")
if user_input:
    _send(user_input, subject, level, difficulty, assistance)
