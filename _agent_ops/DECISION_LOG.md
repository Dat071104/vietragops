# Decision Log / Nhat ky quyet dinh

## DEC-0001 — Continue from the existing VietRAGOps foundation

### Date

2026-08-26

### Context

The existing project was dropped mid-work and should be improved rather than rebuilt blindly. The supplied master card identifies useful retrieval, citation, refusal/guardrail and evaluation foundations, with document lifecycle as the largest product gap.

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Rebuild the project around a new architecture immediately | Clean conceptual reset | High regression risk; loses useful baseline and makes claims harder to compare |
| B | Preserve the current core, first establish a fresh baseline, then improve in bounded stages | Lowest rework and preserves evidence | Requires discipline and may expose old weaknesses before improvement |
| C | Continue feature work without a fresh baseline | Fast short-term changes | Cannot distinguish improvement from drift or historical behavior |

### Decision

Choose B: preserve the current RAG/evaluation foundation and begin future work with a fresh baseline gate.

### Rationale

This follows the supplied context card's recommendation and protects falsification-first comparison. No source behavior was changed during bootstrap.

### Consequences

- Gate 00/baseline is the next valid implementation starting point, unless the user explicitly selects another bounded task.
- Existing historical reports remain context, not current proof.
- Product architecture remains a modular-monolith candidate until measured requirements justify larger infrastructure.

## DEC-0002 — Defer the Evolve Research Pack

### Date

2026-08-26

### Context

The user explicitly said the Evolve Research Pack is for the next task.

### Decision

Do not import, execute, or implement anything from `VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26.zip` during this bootstrap.

### Consequences

- The current ops context is based on the supplied 2026-08-17 master card and current repo inspection only.
- The Evolve pack must be reintroduced deliberately in a separate task with its own scope and read order.

## DEC-0003 — Import the Evolve pack as a gated planning context

### Date

2026-08-26

### Context

The user explicitly started the formerly deferred Evolve proposal and required it
to become durable agent-ops context, while also asking to prepare MarkItDown and
Firecrawl.

### Decision

Import the package as one master integration card and eleven small gate cards.
Keep its source directory/archive as provenance, make Gate 00 the first valid
implementation slice, and record a STOP/result boundary after every gate.

### Rationale

The proposal aligns with the prior audit's lifecycle gap but also contains future
research/deployment assertions that are not current proof. A compact, sourced
tracker preserves its useful order without executing its embedded instructions.

### Consequences

- No Evolve gate is marked passed by this import.
- Gate 07 can end in `STOP` or `REFORMULATE`; Gate 08 requires explicit `GO`.
- MarkItDown and Firecrawl preparation remains external tooling, not app behavior.

## DEC-0004 — Use single-authorized-key provider configuration

### Date

2026-08-26

### Context

The pasted ArgScope configuration assumes a multi-account rotating Groq pool,
whereas VietRAGOps currently reads one `GROQ_API_KEY` and one `GROQ_MODEL`.

### Decision

Preserve the app's single-key contract and reject automatic borrowed-key rotation
or quota-striping. Keep the existing local `.env` untouched and document only
secret-free templates/hand-offs.

### Consequences

- No key list, router state, quotas or credentials enter the repository.
- Future provider-router work belongs to Gate 05 and must remain compliant with
  provider policy and the research no-silent-fallback rule.

## DEC-0005 — Web import is a local CLI, not a FastAPI route

### Date

2026-08-26

### Context

Gate 03 required admin-controlled Firecrawl search/scrape. The application
(`app/main.py`) wires six routers with no authentication/authorization
dependency anywhere; adding a public `/documents/web-import`-style route
would expose bounded-but-real outbound network fetch capability with no
access control at all.

### Decision

Implement `rag/lifecycle/web_import.py::WebImportService` as a plain
service class with no HTTP route, and expose it only through
`scripts/web_import.py`, a local CLI run directly by an operator on this
machine. `app/core/config.py::get_web_import_service()` wires it the same
way `get_lifecycle_service()` wires the existing lifecycle, so a future
route is additive if a gate ever adds real admin authorization.

### Consequences

- No new attack surface was added to the running API.
- If a later gate adds admin authorization, an HTTP route on top of the
  existing `WebImportService` is a small wrapper, not a rewrite.
- Until then, web import requires local shell access to this machine.

## DEC-0006 — Freshness/conflict resolution is opt-in via manifest-row keys, not a schema change

### Date

2026-08-27

### Context

Gate 04 requires deterministic `stale_source`/`source_conflict` states.
The real, tracked `data/manifests/documents_manifest.csv` (37 rows) is a
frozen baseline artifact under explicit instruction not to alter; it has
no column expressing "this source is now stale" or "this source conflicts
with that one".

### Decision

`VersionResolver` reads two additional, entirely optional keys off
whatever manifest-row dict it is given -- `stale_after` and
`conflict_key` -- neither of which is ever written into the real
`documents_manifest.csv`. Fixtures inject these keys directly into
synthetic manifest-row dicts (in-memory or via a throwaway on-disk CSV
under `tmp_path`); the real corpus's rows simply lack the keys, so
`freshness_state`/`conflict_key` resolve to `unknown`/`None` for it,
exactly matching pre-Gate-04 behavior.

### Consequences

- Zero risk of corrupting or reinterpreting the frozen corpus/manifest.
- The real 37-doc corpus cannot surface `stale_source`/`source_conflict`
  on its own yet -- tracked as RISK-0014. A future gate must make an
  explicit, reviewed call (and migration) before adding these columns to
  the live manifest or an equivalent registry-backed mechanism.
- `authority_state`/`source_version` reuse existing manifest columns
  (`status`, `checksum`) and the existing lifecycle registry instead of
  introducing any new identity concept.

## DEC-0007 — Fixed `citations_verified` to use the real verifier result, in scope for Gate 04

### Date

2026-08-27

### Context

Gate 04 Phase 0 preflight found that `app/api/routes_agent.py::run_agent_query`
set the response's `citations_verified` field from
`bool(citations) and not refusal` -- a presence heuristic that never
consulted `CitationVerifier`'s actual grounding-verification result, which
was computed internally by `AnswerGenerator` and then discarded. This
directly contradicts Gate 04's explicit MUST DO ("distinguish citation
verification from answer correctness").

### Decision

Thread the real `CitationVerificationResult` out of `AnswerGenerator`
(via a new `citation_verification` key on every response dict, attached
by a new `_finalize_response` helper) and have `routes_agent.py` read
`citation_verification["is_valid"]` for `citations_verified`, falling back
to the old heuristic only when a caller's answer generator does not
provide the new field (keeps the existing stub-based test working
unchanged).

### Consequences

- `citations_verified` now means what its name says for every real
  request; the one existing test asserting it was re-verified still
  passing (the case it covers is genuinely grounded, so the real result
  agrees with what the heuristic used to guess).
- No control-flow branch (which path executes, when a retry happens) was
  changed -- only which data is attached to the response before it
  returns.
