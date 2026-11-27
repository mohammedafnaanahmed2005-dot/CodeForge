# 🏥 HealthMate AI

General health information assistant powered by the CodeForge AI framework.

## Run

```bash
# From the project root
streamlit run apps/healthmate_ai/app.py
```

## Features

- Medical terminology explained in plain language
- General wellness, nutrition, and fitness information
- Doctor appointment preparation
- Health topic summaries

## Safety

HealthMate AI **never** diagnoses conditions or prescribes medication.  
Every response includes a medical disclaimer.  
Emergency keywords trigger an immediate redirect to emergency services.

## Configuration

Edit `apps/healthmate_ai/config.yaml` to change topic categories, model settings, or safety rules.

## Shared core

This app imports all AI, validation, safety, and conversation logic from `codeforge_core`.  
No core logic lives in this folder.
