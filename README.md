# ⚡ CodeForge AI

**Reusable Multi-Domain AI Assistant Framework**  
*Kiroween Skeleton Crew Hackathon 2026*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](https://streamlit.io)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-76b900)](https://build.nvidia.com)
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What Is CodeForge AI?

CodeForge AI is a **modular, configuration-driven Python framework** that powers
multiple independent AI-assistant applications from a **single shared core**.

Both domain applications use the same AI engine, validation, safety rules, and
conversation management — with zero code duplication.

| App | Domain | Run command |
|-----|--------|-------------|
| 🎓 **EduTrack AI** | Education | `streamlit run apps/edutrack_ai/app.py` |
| 🏥 **HealthMate AI** | Healthcare | `streamlit run apps/healthmate_ai/app.py` |

---

## Repository Structure

```
CodeForge/
│
├── .kiro/                          # Kiro project specs and steering
│   ├── specs/
│   │   ├── architecture.md
│   │   ├── requirements.md
│   │   └── tasks.md
│   ├── steering/
│   │   └── project_context.md
│   └── hooks/
│       └── pre_commit.md
│
├── codeforge_core/                 # Shared reusable framework
│   ├── __init__.py
│   ├── ai_engine.py                # Multi-provider AI client
│   ├── config_loader.py            # YAML config loader
│   ├── prompt_manager.py           # Prompt registry & assembler
│   ├── conversation_manager.py     # Isolated session history
│   ├── validator.py                # Input validation
│   ├── safety_service.py           # Domain safety rules
│   ├── error_handler.py            # Exception translation
│   └── errors.py                   # Custom exception types
│
├── apps/
│   ├── edutrack_ai/                # EduTrack AI – standalone app
│   │   ├── app.py                  # streamlit run apps/edutrack_ai/app.py
│   │   ├── config.yaml
│   │   └── README.md
│   │
│   └── healthmate_ai/              # HealthMate AI – standalone app
│       ├── app.py                  # streamlit run apps/healthmate_ai/app.py
│       ├── config.yaml
│       └── README.md
│
├── config/                         # Shared YAML configuration
│   ├── framework.yaml
│   ├── edutrack.yaml
│   └── healthmate.yaml
│
├── tests/
│   ├── test_ai_engine.py
│   ├── test_edutrack.py
│   └── test_healthmate.py
│
├── requirements.txt
├── README.md
├── LICENSE
├── .env.example
└── .gitignore
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/mohammedafnaanahmed2005-dot/CodeForge.git
cd CodeForge
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env:
# NVIDIA_API_KEY=nvapi-your-key-here
# OPENAI_API_KEY=sk-or-your-openrouter-key-here   (optional fallback)
```

### 3. Run EduTrack AI

```bash
streamlit run apps/edutrack_ai/app.py
```

### 4. Run HealthMate AI

```bash
streamlit run apps/healthmate_ai/app.py
```

### 5. Run all tests (no API key required)

```bash
python -m pytest tests/ -v
```

---

## AI Providers

| Priority | Provider | Key variable | Model |
|----------|----------|-------------|-------|
| 1 (primary) | NVIDIA NIM | `NVIDIA_API_KEY` | `nvidia/nemotron-3.5-bolt-e4b` |
| 2 (fallback) | OpenRouter | `OPENAI_API_KEY` | free-tier models |

The engine automatically falls back to OpenRouter if NVIDIA is unavailable or rate-limited.

---

## Architecture

```
User input
    │
    ▼
Streamlit app  (apps/<domain>/app.py)
    │
    ├── ValidationService.validate()          ← codeforge_core
    ├── SafetyService.check_input()           ← codeforge_core
    ├── PromptManager.build_system_prompt()   ← codeforge_core
    ├── ConversationManager.add_message()     ← codeforge_core
    └── AIEngine.generate_response()          ← codeforge_core
                │
                ▼
         NVIDIA NIM → OpenRouter (fallback)
                │
                ▼
         SafetyService.build_response_with_disclaimer()
                │
                ▼
         Streamlit renders response
```

---

## Adding a Third Domain Application

The core never changes. To add **LegalEase AI**:

1. Create `apps/legalease_ai/app.py` and `apps/legalease_ai/config.yaml`
2. Import everything from `codeforge_core`
3. Write a domain system prompt inside `app.py`
4. Run: `streamlit run apps/legalease_ai/app.py`

---

## Deployment on Streamlit Community Cloud

1. Push to GitHub (`.env` is gitignored — never committed)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file path to `apps/edutrack_ai/app.py` **or** `apps/healthmate_ai/app.py`
4. Under **Advanced settings → Secrets**, add:

```toml
NVIDIA_API_KEY = "nvapi-your-key"
OPENAI_API_KEY = "sk-or-your-key"
```

5. Click **Deploy**

---

## Safety (HealthMate AI)

HealthMate AI never diagnoses conditions or prescribes medication.
Every response includes a medical disclaimer.
Crisis keywords immediately redirect to emergency services.
These rules are enforced in `codeforge_core.SafetyService`, not just the prompt.

---

## License

[MIT](LICENSE)
