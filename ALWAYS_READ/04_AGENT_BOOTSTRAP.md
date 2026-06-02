# Agent Bootstrap Prompt

Use this at the start of a coding or planning session.

```text
Read `rules.md`, `ALWAYS_READ/01_PROJECT_CONTEXT.md`, `ALWAYS_READ/02_CURRENT_PHASE.md`, `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`, then read the active phase card.

Do not read the full codebase. If this task requires code tracing, invoke zone-brain with a seed matching the bug/task and read only `.zone_context.md`.

Before finishing, update the implementation log with files changed, commands run, bug/fix details, verification, and next risks.
```
