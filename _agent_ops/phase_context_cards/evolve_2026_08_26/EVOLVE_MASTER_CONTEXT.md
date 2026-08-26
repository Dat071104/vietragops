# Evolve 2026-08-26 — Integrated Master Context

## What This Adds

VietRAGOps remains an offline-first Vietnamese academic-policy RAG workbench.
The Evolve proposal adds a staged path to governed ingestion, version-aware RAG
operations, and a separate research track on cross-version tool alignment. It
does not prove production readiness or research viability.

## Product and Research Separation

| Lane | Goal | Evidence standard | Status |
| --- | --- | --- | --- |
| Product | Trusted public academic-policy retrieval and operations | Tests, provenance, review/publish controls, deployment proof | No Evolve gate started |
| Tool platform | Provider modes, approved MCP, education sandbox | Auth/security tests, typed failures, deterministic reset | Not started |
| Research | Determine whether alignment needs a new method | Frozen protocol, hidden mappings, strong baselines, raw outputs | Not started; STOP valid |

Never use product fallback to rescue research results. Never turn a historical
report into current proof without rerunning its named check.

## Ordered Design Intent

1. Freeze/verify current behavior before changing it.
2. Build a governed candidate lifecycle: validate, preserve original, register
   source/version, parse/chunk candidate, review, atomically publish/retire.
3. Add local MarkItDown behind validated ingestion and retain existing fallback.
4. Add Firecrawl only as an admin-controlled bounded candidate importer.
5. Make evidence/retrieval version-aware before agent/research complexity.
6. Isolate providers/modes and secure MCP before a deterministic drift sandbox.
7. Run falsification-first Gate-0 before implementing a proposed method.
8. Deploy/publish only from frozen evidence.

## Current Repository Fit

- `ChunkIndexStore` and the retrieval/guardrail core are the baseline; do not
  migrate infrastructure for appearance.
- Upload/index endpoints are lifecycle gaps; a candidate must not be a live path.
- Current routing consumes one `GROQ_API_KEY` and one `GROQ_MODEL`; a multi-key
  router is neither implemented nor authorized.
- Existing Compose does not provide the proposed future lifecycle or Firecrawl
  adapter.

## Security and Local Setup

- Local secrets stay untracked; never inspect or print values.
- `VietRagOps/.env.example` is the app template. The pre-existing `.env` remains
  untouched.
- `VietRagOps/.env.firecrawl.local` is empty, ignored, and only becomes relevant
  at Gate 03 with explicit user confirmation.
- Local third-party pins live in `_agent_ops/THIRD_PARTY_TOOLING.md` outside the
  application Git root.
- A self-hosted Firecrawl baseline is localhost-only and not production-ready;
  public exposure needs separately approved auth, TLS, network, persistence,
  backup and recovery design.

## Decision Discipline

- Every gate ends in a result record and STOP. Tool installation is not a pass.
- Freeze manifests, prompts, model IDs, retry/timeouts and metrics before
  held-out research work.
- Retain raw results; distinguish provider failure from incorrect answer.
- Gates 08–10 are unavailable unless their explicit prerequisites pass.
- Google Cloud and arXiv are late evidence deliverables, never setup milestones.

## Source Routing

| Need | Original source package |
| --- | --- |
| Overall scope / research claim | `00_README_PACK.md`, `01_MASTER_SCOPE_AND_RESEARCH.md` |
| Architecture plan | `02_ARCHITECTURE_AND_FOLDER_STRUCTURE.md` |
| Agent contract | `03_AGENT_OPERATING_CONTRACT.md` |
| Provider/secrets | `04_PROVIDER_SECRETS_AND_LOCAL_SETUP.md` |
| Cloud/paper rules | `05_GOOGLE_CLOUD_DEPLOYMENT.md`, `06_ARXIV_AFTER_DEPLOYMENT.md` |
| Kill criteria | `07_RISKS_AND_KILL_CRITERIA.md` |
| Exact checklist | matching `gates/GATE_XX_*.md` |

## Status

`Planning integration complete. Gate 00 is the first permitted implementation
gate; it has not been run in this task.`
