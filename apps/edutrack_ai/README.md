# 🎓 EduTrack AI

Personal academic assistant powered by the CodeForge AI framework.

## Run

```bash
# From the project root
streamlit run apps/edutrack_ai/app.py
```

## Features

- Concept explanations at any academic level
- Quiz and practice problem generation
- Study material summarisation
- Personalised study plans
- Support for dyslexia, ADHD, and ESL learners

## Configuration

Edit `apps/edutrack_ai/config.yaml` to change subjects, levels, model settings, or example questions.

## Shared core

This app imports all AI, validation, and conversation logic from `codeforge_core`.  
No core logic lives in this folder.
