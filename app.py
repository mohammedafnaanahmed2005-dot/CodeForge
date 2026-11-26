"""
CodeForge AI – Main Streamlit application entry point.

Run locally:
    streamlit run app.py
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure the project root is on sys.path regardless of cwd
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# ── Load environment variables BEFORE anything else ──────────────────────────
# Must happen before @st.cache_resource builds the engine, otherwise keys
# added after the first run are never seen.
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)
except ImportError:
    pass

# Inject Streamlit secrets into env for Cloud deployment
if hasattr(st, "secrets"):
    try:
        for _secret_key in ("OPENAI_API_KEY", "NVIDIA_API_KEY"):
            if _secret_key in st.secrets:
                os.environ.setdefault(_secret_key, st.secrets[_secret_key])
    except Exception:
        pass

from core.ai_engine import AIEngine
from core.config_manager import ConfigManager
from core.errors import AIEngineError, MissingAPIKeyError, SafetyError, ValidationError
from apps.edutrack.app import EduTrackApp
from apps.healthmate.app import HealthMateApp

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeForge AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared styles ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .big-title  { font-size: 2.6rem; font-weight: 800; line-height: 1.1; }
    .sub-title  { font-size: 1.1rem; color: #aaa; margin-bottom: 1.5rem; }
    .app-card   {
        background: #1A1F2E; border: 1px solid #2d3550;
        border-radius: 12px; padding: 1.4rem; margin-bottom: 1rem;
        transition: border-color .2s;
    }
    .app-card:hover { border-color: #FF6B35; }
    .badge      {
        display: inline-block; background: #FF6B35; color: #fff;
        border-radius: 20px; padding: 2px 10px; font-size: 0.75rem;
        font-weight: 600; margin-bottom .4rem;
    }
    .msg-user   {
        background: #252b40; border-radius: 10px 10px 0 10px;
        padding: .75rem 1rem; margin: .4rem 0; text-align: right;
    }
    .msg-bot    {
        background: #1A1F2E; border: 1px solid #2d3550;
        border-radius: 10px 10px 10px 0; padding: .75rem 1rem; margin: .4rem 0;
    }
    .stTextArea textarea { font-size: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Shared singletons (cached for the whole session) ──────────────────────────
@st.cache_resource
def _build_framework():
    cfg = ConfigManager()
    engine = AIEngine(config_manager=cfg)
    return cfg, engine


cfg, engine = _build_framework()

@st.cache_resource
def _build_apps(_cfg, _engine):
    return EduTrackApp(_cfg, _engine), HealthMateApp(_cfg, _engine)


edu_app, health_app = _build_apps(cfg, engine)

# ── Session state initialisation ──────────────────────────────────────────────
def _init_state() -> None:
    defaults: dict = {
        "page": "home",
        "edu_session": "edu_default",
        "health_session": "health_default",
        "edu_messages": [],
        "health_messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ── Navigation helpers ────────────────────────────────────────────────────────
def _go(page: str) -> None:
    st.session_state["page"] = page


# ═════════════════════════════════════════════════════════════════════════════
# HOME / DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
def render_home() -> None:
    # Hero
    st.markdown(
        '<p class="big-title">⚡ CodeForge AI</p>'
        '<p class="sub-title">Reusable Multi-Domain AI Assistant Framework '
        '— Kiroween Skeleton Crew Hackathon 2024</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        **CodeForge AI** is a modular, configuration-driven Python framework that powers
        multiple independent AI applications from a **single shared core**.
        Switch domains, plug in new apps, or extend the AI engine — without rewriting
        any shared logic.
        """
    )

    api_ready = engine.is_ready()
    nvidia_active = bool(engine.get_nvidia_key())
    if api_ready:
        if nvidia_active:
            st.success("✅ NVIDIA NIM API key detected — powered by `nvidia/nemotron-3.5-bolt-e4b`.")
        else:
            st.success("✅ OpenRouter API key detected — both applications are ready.")
    else:
        st.warning(
            "⚠️ No API key detected. "
            "Add `NVIDIA_API_KEY` or `OPENAI_API_KEY` to your `.env` file or Streamlit secrets."
        )

    st.markdown("---")

    # Application cards
    st.markdown("### 🚀 Choose an Application")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="app-card">
            <span class="badge">Education</span>
            <h3>🎓 EduTrack AI</h3>
            <p>Your personal academic assistant. Get concept explanations,
            practice quizzes, study plans, and subject-specific guidance —
            personalised to your level and learning style.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Features:**")
        st.markdown(
            "- Concept explanations at any academic level\n"
            "- Automatic quiz generation\n"
            "- Study material summarisation\n"
            "- Personalised study plans\n"
            "- Support for dyslexia, ADHD & ESL learners"
        )
        if st.button("Open EduTrack AI →", use_container_width=True, type="primary"):
            _go("edutrack")

    with col2:
        st.markdown(
            """
            <div class="app-card">
            <span class="badge">Healthcare</span>
            <h3>🏥 HealthMate AI</h3>
            <p>Your health education companion. Understand medical terminology,
            learn about wellness topics, and prepare for doctor appointments —
            safely and responsibly.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Features:**")
        st.markdown(
            "- Medical terminology explained simply\n"
            "- General wellness & nutrition info\n"
            "- Doctor appointment preparation\n"
            "- Health topic summaries\n"
            "- Always includes medical disclaimers"
        )
        if st.button("Open HealthMate AI →", use_container_width=True, type="primary"):
            _go("healthmate")

    st.markdown("---")

    # Architecture overview
    with st.expander("🏗️ Framework Architecture", expanded=False):
        st.markdown(
            """
            ```
            CodeForge AI Framework
            ├── core/
            │   ├── ai_engine.py          ← OpenAI integration (shared)
            │   ├── config_manager.py     ← YAML config loader (shared)
            │   ├── prompt_manager.py     ← Prompt registry & assembler
            │   ├── conversation_manager.py  ← Isolated session history
            │   ├── validation_service.py ← Input validation
            │   ├── safety_service.py     ← Domain safety rules
            │   └── error_handler.py     ← Exception translation
            │
            ├── apps/
            │   ├── edutrack/            ← EduTrack AI domain app
            │   │   ├── app.py
            │   │   └── prompts.py
            │   └── healthmate/          ← HealthMate AI domain app
            │       ├── app.py
            │       └── prompts.py
            │
            ├── config/
            │   ├── framework.yaml
            │   ├── edutrack.yaml
            │   └── healthmate.yaml
            │
            └── app.py                   ← Streamlit entry point
            ```

            **Adding a new domain app requires:**
            1. Create `apps/<newdomain>/app.py` and `prompts.py`
            2. Add `config/<newdomain>.yaml`
            3. Register the app in `config/framework.yaml`
            4. Add a UI card in `app.py`

            The core AI engine and all shared services need **zero modifications**.
            """
        )


# ═════════════════════════════════════════════════════════════════════════════
# SHARED CHAT RENDERER
# ═════════════════════════════════════════════════════════════════════════════
def _render_chat_history(msg_key: str) -> None:
    messages = st.session_state[msg_key]
    if not messages:
        st.info("No messages yet. Ask something below to get started.")
        return
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, MissingAPIKeyError):
        st.error(f"🔑 **API Key Missing**\n\n{exc}")
    elif isinstance(exc, ValidationError):
        st.warning(f"⚠️ **Input Error**\n\n{exc}")
    elif isinstance(exc, SafetyError):
        st.warning(f"🛡️ **Safety Notice**\n\n{exc}")
    elif isinstance(exc, AIEngineError):
        st.error(f"🤖 **AI Engine Error**\n\n{exc}")
    else:
        st.error(f"❌ **Unexpected Error**\n\n{exc}")


# ═════════════════════════════════════════════════════════════════════════════
# EDUTRACK AI PAGE
# ═════════════════════════════════════════════════════════════════════════════
def render_edutrack() -> None:
    edu_cfg = edu_app.app_config

    # Sidebar
    with st.sidebar:
        st.markdown("## 🎓 EduTrack AI")
        st.markdown("*Personalise your learning experience*")
        st.markdown("---")

        subject = st.selectbox(
            "📚 Subject",
            options=edu_cfg.get("subjects", []),
            index=0,
        )
        level = st.selectbox(
            "🎯 Academic Level",
            options=edu_cfg.get("academic_levels", []),
            index=2,
        )
        difficulty = st.selectbox(
            "🧠 Learning Profile",
            options=edu_cfg.get("learning_difficulties", []),
            index=0,
        )
        assistance = st.selectbox(
            "🛠️ Assistance Type",
            options=edu_cfg.get("assistance_types", []),
            index=0,
        )

        st.markdown("---")
        st.markdown("**💡 Example Questions**")
        for q in edu_cfg.get("example_questions", []):
            if st.button(q, key=f"eq_{q[:20]}", use_container_width=True):
                _send_edutrack_message(q, subject, level, difficulty, assistance)

        st.markdown("---")
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            edu_app.clear_conversation(st.session_state["edu_session"])
            st.session_state["edu_messages"] = []
            st.rerun()

        if st.button("🏠 Back to Home", use_container_width=True):
            _go("home")
            st.rerun()

    # Main area
    st.markdown("## 🎓 EduTrack AI — Academic Assistant")
    st.markdown(
        f"*Subject: **{subject}** · Level: **{level}** · "
        f"Assistance: **{assistance}***"
    )
    st.markdown("---")

    _render_chat_history("edu_messages")

    # Chat input
    user_input = st.chat_input("Ask EduTrack AI anything academic…")
    if user_input:
        _send_edutrack_message(user_input, subject, level, difficulty, assistance)


def _send_edutrack_message(
    text: str,
    subject: str,
    level: str,
    difficulty: str,
    assistance: str,
) -> None:
    st.session_state["edu_messages"].append({"role": "user", "content": text})
    with st.spinner("EduTrack AI is thinking…"):
        try:
            reply = edu_app.chat(
                session_id=st.session_state["edu_session"],
                user_message=text,
                subject=subject,
                academic_level=level,
                learning_difficulty=difficulty,
                assistance_type=assistance,
            )
            st.session_state["edu_messages"].append({"role": "assistant", "content": reply})
        except Exception as exc:  # noqa: BLE001
            _handle_error(exc)
            # Remove the user message we already appended so history stays clean
            if st.session_state["edu_messages"] and st.session_state["edu_messages"][-1]["role"] == "user":
                st.session_state["edu_messages"].pop()
    st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# HEALTHMATE AI PAGE
# ═════════════════════════════════════════════════════════════════════════════
def render_healthmate() -> None:
    health_cfg = health_app.app_config

    with st.sidebar:
        st.markdown("## 🏥 HealthMate AI")
        st.markdown("*General health education*")
        st.markdown("---")

        topic = st.selectbox(
            "🏷️ Topic Category",
            options=["(General)"] + health_cfg.get("topic_categories", []),
            index=0,
        )

        st.markdown("---")
        st.markdown("**💡 Example Questions**")
        for q in health_cfg.get("example_questions", []):
            if st.button(q, key=f"hq_{q[:20]}", use_container_width=True):
                _send_health_message(q, topic)

        st.markdown("---")
        st.info(
            "⚕️ HealthMate AI provides **general health education only**.\n\n"
            "It does not diagnose conditions or prescribe treatment.\n\n"
            "Always consult a qualified healthcare provider."
        )

        if st.button("🗑️ Clear Conversation", use_container_width=True):
            health_app.clear_conversation(st.session_state["health_session"])
            st.session_state["health_messages"] = []
            st.rerun()

        if st.button("🏠 Back to Home", use_container_width=True):
            _go("home")
            st.rerun()

    st.markdown("## 🏥 HealthMate AI — Health Information Assistant")
    st.markdown(f"*Topic: **{topic}***")
    st.markdown("---")

    _render_chat_history("health_messages")

    user_input = st.chat_input("Ask HealthMate AI a health question…")
    if user_input:
        _send_health_message(user_input, topic)


def _send_health_message(text: str, topic: str) -> None:
    st.session_state["health_messages"].append({"role": "user", "content": text})
    effective_topic = "" if topic == "(General)" else topic
    with st.spinner("HealthMate AI is thinking…"):
        try:
            reply = health_app.chat(
                session_id=st.session_state["health_session"],
                user_message=text,
                topic_category=effective_topic,
            )
            st.session_state["health_messages"].append({"role": "assistant", "content": reply})
        except Exception as exc:  # noqa: BLE001
            _handle_error(exc)
            if st.session_state["health_messages"] and st.session_state["health_messages"][-1]["role"] == "user":
                st.session_state["health_messages"].pop()
    st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════
page = st.session_state["page"]

if page == "home":
    render_home()
elif page == "edutrack":
    render_edutrack()
elif page == "healthmate":
    render_healthmate()
else:
    _go("home")
    st.rerun()
