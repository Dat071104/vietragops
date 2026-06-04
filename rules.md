# VietRAGOps Workspace Rules

- Read the smallest useful context first: this file, `ALWAYS_READ/01_PROJECT_CONTEXT.md`, `ALWAYS_READ/02_CURRENT_PHASE.md`, `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`, then the active phase card.
- Do not print, commit, or copy local secrets. Keep `.env` local-only and use `.env.example` for placeholders.
- Use mock mode by default for tests, evals, API smoke checks, and demos unless a real provider check is explicitly requested.
- Do not overclaim readiness. Report Docker, browser, Groq, and Ollama checks only when they were actually run and passed.
- Do not use `git add .`; stage explicit files only.
- Validate before committing or pushing. At minimum run compile checks, pytest, relevant data/eval checks, smoke checks, and a secret scan.
