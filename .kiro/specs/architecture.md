# CodeForge AI – Architecture Specification

## Overview

CodeForge AI is a reusable, configuration-driven Python framework that powers
multiple independent AI-assistant applications from a single shared core.

## Guiding Principles

1. **Single shared core** – `codeforge_core` contains all AI, validation,
   safety, and conversation logic. Domain apps import from it; they never
   duplicate it.
2. **Configuration-driven** – switching domains changes prompts, safety rules,
   and model settings via YAML. No Python changes are needed for new domains.
3. **Independent execution** – each domain app is a standalone Streamlit
   application with its own entry point.
4. **Strategy pattern** – domain behaviour (prompts, safety) is injected into
   the AI engine at runtime, keeping the engine itself domain-agnostic.

## Module Responsibilities

| Module | Package | Responsibility |
|--------|---------|---------------|
| `ai_engine.py` | `codeforge_core` | Multi-provider OpenAI-compatible API client |
| `config_loader.py` | `codeforge_core` | YAML config loading and caching |
| `prompt_manager.py` | `codeforge_core` | Prompt registry and context assembler |
| `conversation_manager.py` | `codeforge_core` | Isolated per-session message history |
| `validator.py` | `codeforge_core` | Input length and type constraints |
| `safety_service.py` | `codeforge_core` | Domain safety rules and disclaimers |
| `error_handler.py` | `codeforge_core` | API exception translation |

## Provider Hierarchy

```
NVIDIA NIM  (NVIDIA_API_KEY)   ← primary
     │
     └── fallback on 429/empty
OpenRouter  (OPENAI_API_KEY)   ← secondary (free-tier models)
     │
     └── fallback model 2
```

## Request Flow

```
User input
    │
    ▼
Streamlit app (apps/<domain>/app.py)
    │
    ├── ValidationService.validate()
    ├── SafetyService.check_input()
    ├── PromptManager.build_system_prompt()
    ├── ConversationManager.add_user_message()
    └── AIEngine.generate_response()
              │
              ▼
        NVIDIA NIM / OpenRouter
              │
              ▼
        SafetyService.build_response_with_disclaimer()
        ConversationManager.add_assistant_message()
              │
              ▼
        Streamlit UI renders response
```

## Adding a New Domain Application

1. Create `apps/<newdomain>/app.py` and `apps/<newdomain>/config.yaml`
2. Add `config/<newdomain>.yaml` (or embed settings in the app config)
3. Register in `config/framework.yaml` under `applications:`
4. Import from `codeforge_core` — zero core changes required

## Security

- API keys stored in `.env` only (gitignored)
- Streamlit Cloud deployment uses `st.secrets`
- No keys in source code, YAML, or logs
