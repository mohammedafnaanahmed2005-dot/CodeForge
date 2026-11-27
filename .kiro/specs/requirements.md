# CodeForge AI – Functional and Non-Functional Requirements

## Functional Requirements

### Framework (codeforge_core)
- FR-01: Provide a reusable AI engine that accepts system prompts and conversation history
- FR-02: Support multiple AI providers (NVIDIA NIM primary, OpenRouter fallback)
- FR-03: Load domain configuration from YAML files
- FR-04: Manage per-session, per-domain conversation history with configurable turn limits
- FR-05: Validate user input for length and type before passing to the AI engine
- FR-06: Apply domain-specific safety rules to block prohibited requests
- FR-07: Append domain disclaimers to every AI response
- FR-08: Detect emergency keywords universally and redirect to emergency services
- FR-09: Translate all API exceptions into user-readable error messages

### EduTrack AI
- FR-10: Answer academic questions across configurable subjects
- FR-11: Adjust explanation depth and language to academic level
- FR-12: Generate quizzes and practice problems on request
- FR-13: Summarise study material
- FR-14: Create structured study plans
- FR-15: Support learning profiles (ADHD, dyslexia, ESL)

### HealthMate AI
- FR-16: Explain medical terminology in plain language
- FR-17: Provide general wellness and nutrition information
- FR-18: Help users prepare for doctor appointments
- FR-19: Never diagnose medical conditions
- FR-20: Never prescribe or recommend medication changes
- FR-21: Append a medical disclaimer to every response
- FR-22: Immediately redirect to emergency services on crisis keywords

## Non-Functional Requirements

- NFR-01: Both apps must start in under 5 seconds on a standard laptop
- NFR-02: All 70+ automated tests must pass without a real API key
- NFR-03: No API keys may appear in source code, YAML, or git history
- NFR-04: Both apps must run independently with a single `streamlit run` command
- NFR-05: Adding a third domain app must require zero changes to `codeforge_core`
- NFR-06: Code must follow PEP 8 and include module-level docstrings
