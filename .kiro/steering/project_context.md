# CodeForge AI – Project Steering Context

## Project Identity

- **Name:** CodeForge AI
- **Type:** Reusable Multi-Domain AI Assistant Framework
- **Event:** Kiroween Skeleton Crew Hackathon 2026
- **Status:** Complete and functional

## Core Package

All reusable logic lives in `codeforge_core/`.  
When modifying core behaviour, always run `python -m pytest tests/ -v` before committing.

## Application Structure

Each domain app in `apps/` is self-contained:
- Its own `app.py` Streamlit entry point
- Its own `config.yaml`
- Its own `README.md`
- All shared logic imported from `codeforge_core`

## AI Providers

Primary: NVIDIA NIM via `NVIDIA_API_KEY`  
Fallback: OpenRouter free-tier via `OPENAI_API_KEY`  
Both keys stored in `.env` only — never in source code.

## Coding Standards

- Python 3.11+ syntax (use `from __future__ import annotations`)
- Type hints on all public methods
- Module-level docstrings on every file
- No hardcoded API keys anywhere
- All new features need corresponding tests

## Running the Project

```bash
# EduTrack AI
streamlit run apps/edutrack_ai/app.py

# HealthMate AI
streamlit run apps/healthmate_ai/app.py

# Tests
python -m pytest tests/ -v
```
