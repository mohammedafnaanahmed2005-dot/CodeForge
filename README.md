# ⚡ CodeForge AI

**Reusable Multi-Domain AI Assistant Framework**  
*Kiroween Skeleton Crew Hackathon 2024*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green)](https://openai.com)
[![Tests](https://img.shields.io/badge/Tests-70%20passing-brightgreen)]()

---

## What Is CodeForge AI?

CodeForge AI is a **modular, configuration-driven Python framework** that powers multiple independent AI applications from a **single shared core engine**.

Out of the box it ships two domain applications:

| App | Domain | Purpose |
|-----|--------|---------|
| 🎓 **EduTrack AI** | Education | Academic assistant: explanations, quizzes, study plans |
| 🏥 **HealthMate AI** | Healthcare | Health information: terminology, wellness, appointment prep |

Switching domains changes the AI's behaviour, prompts, safety rules, and UI — without modifying the shared core.

---

## Project Structure

```
codeforge-ai/
├── app.py                      # Streamlit entry point
├── requirements.txt
├── .env.example
├── .gitignore
│
├── core/                       # Shared framework (never modify for new domains)
│   ├── ai_engine.py            # OpenAI integration
│   ├── config_manager.py       # YAML config loader
│   ├── prompt_manager.py       # Prompt registry & assembler
│   ├── conversation_manager.py # Isolated session history
│   ├── validation_service.py   # Input validation
│   ├── safety_service.py       # Domain safety rules & disclaimers
│   ├── error_handler.py        # Exception translation
│   └── errors.py               # Custom exceptions
│
├── apps/
│   ├── edutrack/               # EduTrack AI domain app
│   │   ├── app.py
│   │   └── prompts.py
│   └── healthmate/             # HealthMate AI domain app
│       ├── app.py
│       └── prompts.py
│
├── config/
│   ├── framework.yaml          # Framework-level settings
│   ├── edutrack.yaml           # Education domain settings
│   └── healthmate.yaml         # Healthcare domain settings
│
├── tests/                      # 70 automated tests (all mocked, no API key needed)
│   ├── test_ai_engine.py
│   ├── test_config_manager.py
│   ├── test_conversation_manager.py
│   ├── test_domain_apps.py
│   ├── test_prompt_manager.py
│   ├── test_safety_service.py
│   └── test_validation_service.py
│
└── .streamlit/
    └── config.toml             # Streamlit theme
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-username/codeforge-ai.git
cd codeforge-ai
pip install -r requirements.txt
```

### 2. Configure your OpenAI API key

```bash
cp .env.example .env
# Edit .env and set:
# OPENAI_API_KEY=sk-your-real-key-here
```

### 3. Run locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### 4. Run the tests (no API key required)

```bash
python -m pytest tests/ -v
```

All 70 tests use mocked API responses.

---

## Deployment on Streamlit Community Cloud

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "feat: initial CodeForge AI implementation"
git branch -M main
git remote add origin https://github.com/your-username/codeforge-ai.git
git push -u origin main
```

> **Important:** confirm `.env` is in `.gitignore` before pushing. Never commit your API key.

### Step 2 — Create a Streamlit Cloud app

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repository, branch (`main`), and set the main file path to `app.py`.
4. Click **Advanced settings → Secrets** and add:

```toml
OPENAI_API_KEY = "sk-your-real-key-here"
```

5. Click **Deploy**.

Streamlit Cloud automatically installs `requirements.txt` and starts the app.

---

## Architecture: How the Strategy Pattern Works

```
User request
     │
     ▼
Streamlit UI  (app.py)
     │  selects domain
     ▼
Domain App  (EduTrackApp / HealthMateApp)
     │
     ├─► ValidationService.validate()       ← shared
     ├─► SafetyService.check_input()        ← domain-configured
     ├─► PromptManager.build_system_prompt() ← domain prompt injected
     ├─► ConversationManager.get_messages() ← isolated per app
     └─► AIEngine.generate_response()       ← shared core
              │
              ▼
         OpenAI API
```

The **AI engine never changes** regardless of domain. Domain behaviour is entirely injected through configuration, prompts, and the safety service.

---

## Adding a Third Domain Application

To add, say, **LegalEase AI**:

1. **Create the app package:**

```
apps/
└── legalease/
    ├── __init__.py
    ├── app.py      # copy edutrack/app.py, change APP_ID and imports
    └── prompts.py  # write your domain system prompt
```

2. **Add configuration:**

```
config/legalease.yaml
```

3. **Register the app** in `config/framework.yaml`:

```yaml
applications:
  - id: "legalease"
    name: "LegalEase AI"
    description: "Legal Information Assistant"
    icon: "⚖️"
```

4. **Add a card and route** in `app.py` (the Streamlit entry point).

**Zero changes required** to the core AI engine, config manager, conversation manager, validation service, or error handler.

---

## Core Modules Reference

| Module | Responsibility |
|--------|---------------|
| `AIEngine` | Communicates with OpenAI; domain-agnostic |
| `ConfigManager` | Loads and caches YAML configs; shared singleton |
| `PromptManager` | Registry + assembler for domain system prompts |
| `ConversationManager` | Per-session isolated message history |
| `ValidationService` | Input length and type constraints |
| `SafetyService` | Domain-specific blocked patterns + disclaimers |
| `ErrorHandler` | Translates OpenAI/network exceptions to user messages |

---

## Safety Notes (HealthMate AI)

HealthMate AI is configured to:

- **Never** diagnose medical conditions
- **Never** prescribe or recommend medications
- **Always** append a medical disclaimer to every response
- **Immediately** redirect to emergency services when crisis keywords are detected
- **Always** recommend consulting a qualified healthcare provider

These rules are enforced at the application layer (not just the prompt) so they cannot be bypassed through prompt injection.

---

## Hackathon Demonstration Script

1. Open the app — show the **CodeForge AI dashboard** with both application cards.
2. Click **EduTrack AI** → ask: *"Quiz me on 5 photosynthesis questions at high school level."*
3. Change subject to **Mathematics** → ask: *"Explain the Pythagorean theorem with examples."*
4. Go back to home → open **HealthMate AI**.
5. Ask: *"What does hypertension mean in plain language?"*
6. Demonstrate safety: ask *"Can you diagnose my chest pain?"* → show the safety block.
7. Clear both conversations — show they reset independently.
8. Run `pytest tests/ -v` in a terminal — show all 70 tests passing.

---

## License

MIT — free to extend, fork, and deploy.
