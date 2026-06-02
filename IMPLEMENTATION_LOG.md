# Implementation Log

<!-- newest first -->

## 2026-06-02 15:01 - [unknown_phase/bugfix] Isolate Local Agent provider to Ollama

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Local Agent tab mistakenly used Groq when LLM_PROVIDER=groq was set, breaking the local tool calling demo.
- Root cause: routes_agent.py used the global get_provider_router() which inherits the environment's LLM_PROVIDER, instead of strictly enforcing Ollama.
- Fix: Added get_agent_provider_router() and get_agent_answer_generator() in config.py hardcoded to 'ollama'. Updated routes_agent.py to use these specific instances.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none



## 2026-06-02 14:51 - [unknown_phase/bugfix] Enable python-dotenv for API startup

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Adding GROQ_API_KEY to .env does not take effect when running uvicorn directly.
- Root cause: The app/main.py script did not load the .env file explicitly, causing local environment variables to not be registered on Windows.
- Fix: Imported and called load_dotenv() in app/main.py.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none



## 2026-06-02 14:39 - [unknown_phase/bugfix] Fix Streamlit API timeout for local agent

### Goal
- not specified

### Files changed
- none

### Bug or issue fixed
- Symptom: Web UI Local Agent tab hangs or fails to generate appropriate answer
- Root cause: The local Ollama generation for agent tasks takes ~60s, but frontend requests.post had a hardcoded 30s timeout, causing it to fail and trigger a duplicate fallback.
- Fix: Increased timeout in frontend/streamlit_app.py api_post to 120 seconds.
- Why this fix is safe: not specified

### Commands run
```bash
not run
```

### Verification
- not verified

### Decisions
- none

### Remaining risks / next step
- none


