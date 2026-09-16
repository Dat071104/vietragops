# Local Environment Files

## Current Application Runtime

- Canonical committed template: `VietRagOps/.env.example`.
- Canonical local file: `VietRagOps/.env` (ignored, pre-existing, never read or
  overwritten by this task).
- Current code consumes one `GROQ_API_KEY` and one `GROQ_MODEL`, alongside
  `LLM_PROVIDER` and optional Ollama settings. It has no multi-key router.

Use a credential that you are authorized to use and stay within the provider's
published limits. Do not paste a pooled, borrowed or rotating key list into this
project or build a workaround to bypass quota/account controls.

## Firecrawl Handoff

- Gate-03 key file: `VietRagOps/.env.firecrawl.local` (ignored; exactly
  `FIRECRAWL_API_KEY=` until the owner supplies a valid key).
- Firecrawl self-host baseline: `ROOT/external_tools/firecrawl/.env` (ignored by
  that checkout; no external API key needed for the configuration check).

Get a Firecrawl key only from the owner's dashboard:
`https://www.firecrawl.dev/app/api-keys`. Paste it directly into the ignored
local handoff file; never send its value to an agent/chat or add it to a tracked
file. The first authenticated request stays blocked until Gate 03 is active.

Neither Firecrawl file is consumed by the current app. Gate 03 must implement and
test a backend-only adapter before either is a runtime contract.

## Secret-Safety Check

Before staging or reporting, inspect only file names/state and use scanners that
never print values. Never echo `.env` contents or put secrets in `_agent_ops`.
