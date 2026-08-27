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

## DEC-0008 — Typed Groq failure exceptions via a narrow, additive edit to the protected `groq_client.py` overlay

### Date

2026-08-27

### Context

Gate 05 Phase 5.1 requires distinct, typed 429/timeout/network/auth outcomes
for every provider, "never collapsed into a generic fallback error." The
dirty-overlay (uncommitted, pre-existing) `rag/generation/groq_client.py` --
a multi-key round-robin rotation client with 429 cooldown, which `AGENTS.md`
documents as "supported and encouraged" -- currently swallows every failure
mode (429/401/5xx/timeout/network) into one generic
`RuntimeError(f"...Last error: {last_exception}")` once all keys/retries are
exhausted. The committed `HEAD` version of this file is a 41-line minimal
single-key client with no rotation at all; the rotation logic exists only in
the uncommitted working tree. The Gate 05 contract explicitly forbids
touching this path "unless overlap analysis proves the existing change is
non-semantic and the user explicitly authorizes touching that path."

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Narrow additive edit: raise typed exception subclasses only at final retry exhaustion, zero change to rotation/cooldown/retry/backoff | Reliable, real typing; matches Phase 5.1's explicit requirement | Touches a protected overlay file; needs explicit authorization |
| B | Zero-touch: classify failures in the new Gate 05 layer by regex-parsing the wrapped `RuntimeError` message | Never touches the protected file | Fragile -- silently breaks if the message format changes; network vs. timeout not reliably separable this way |
| C | Bypass `GroqClient` entirely with a new, independent single-key HTTP client for Gate 05's typed path | Full control, no protected-file edit | Duplicates existing Groq call logic; two Groq code paths become an "overlapping side effect" (`AGENTS.md` coding standard); contradicts "preserve current Groq behavior for unchanged/default use" |

### Decision

Chose A. Asked the user directly (`AskUserQuestion`) given the contract's
explicit authorization requirement on this exact file; user confirmed the
multi-key rotation is intentional/desired and authorized the narrow typed-
exception edit, explicitly framed as "continue as it should be." Verified
before deciding that none of the overlay's own `tests/test_groq_rotation.py`
(5 tests) assert the final-exhaustion exception's type or message, so the
edit does not break that pre-existing, untouched test file either.

### Consequences

- Rotation/cooldown/retry/backoff behavior is unchanged byte-for-byte;
  only the shape of the exception raised after all keys/retries are
  exhausted changes (typed subclass instead of a bare `RuntimeError`,
  same message text preserved).
- Not yet implemented as of this entry -- Gate 05 is currently blocked at
  the Phase 5.0 preflight dependency gate (Groq not configured; MCP SDK
  dependency not yet approved). Implementation happens once Gate 05
  preflight passes.
- `groq_client.py` remains part of the pre-existing dirty overlay and will
  not be staged/committed as part of any Gate 05 commit unless the user
  separately authorizes committing that overlay path.

## DEC-0009 — `mcp` (official SDK) chosen over a standalone `fastmcp` package for Phase 5.3

### Date

2026-08-27

### Context

Phase 5.3 needs a maintained, standards-compliant Streamable HTTP MCP
implementation; the gate contract forbids hand-rolling the protocol and
asks for "the smallest maintained pinned dependency." No MCP SDK was
installed. User asked to pick whichever option is most optimized for this
project and to note why.

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Official `mcp` PyPI package (Model Context Protocol Python SDK, LF Projects, MIT) | Canonical/only officially maintained SDK; single dependency; includes the high-level ergonomic server API built in; native Streamable HTTP transport; v2.1.1's `MCPServer` ships built-in `TokenVerifier`/`auth_server_provider`/`resource_security` primitives that map directly onto Phase 5.4's auth/origin/scope requirements | v2.x is a recent major rewrite (FastMCP renamed to `MCPServer`); less real-world mileage than v1.x |
| B | Standalone third-party `fastmcp` package (jlowin/fastmcp) | Slightly more ergonomic decorator API in some releases | Adds a second dependency layered on top of the same protocol logic `mcp` already provides; not the canonical/official SDK; would violate "smallest dependency" |
| C | Pin `mcp<2` to keep the older v1 `FastMCP` API | Larger community track record | Deliberately installs an older, non-latest release with no material advantage here; the v2 auth primitives are a direct fit for this gate's security phase |

### Decision

Chose A: installed and pinned `mcp==2.1.1` (exact version pip resolved) in
`requirements.txt`. Verified: `pip show mcp` reports `License: MIT`,
`Home-page: https://modelcontextprotocol.io`, `Author: Model Context
Protocol a Series of LF Projects, LLC.`; imports cleanly
(`mcp.server.mcpserver.MCPServer`, `mcp.server.streamable_http`); full
suite re-run after install still **275 passed, 0 failed**; `compileall`
clean.

### Consequences

- Phase 5.3's `/mcp` endpoint will be built on `mcp.server.mcpserver.MCPServer`
  with the `streamable-http` transport, not a hand-rolled protocol
  implementation and not a second `fastmcp` dependency.
- Phase 5.4's auth/origin/scope work should prefer the SDK's built-in
  `TokenVerifier`/`auth_server_provider`/`resource_security` hooks over
  new bespoke middleware where they cover the requirement.
- Transitive dependencies added: `mcp-types`, `httpx2`, `httpcore2`,
  `opentelemetry-api`, `sse-starlette`, `pyjwt`, `truststore` (all pulled
  in by the official package's own `Requires`, not separately chosen).

## DEC-0010 — Compose the SDK's own auth middleware manually instead of `MCPServer`'s OAuth-only `auth=` path

### Date

2026-08-27

### Context

Phase 5.4 requires server-owned bearer auth with no OAuth, no token
issuer, no cloud identity. `mcp==2.1.1`'s `MCPServer(token_verifier=...)`
raises `ValueError: Cannot specify auth_server_provider or token_verifier
without auth settings` at construction -- discovered empirically, not
documented up front. Its `auth=` parameter is `AuthSettings`, which
mandatorily requires `issuer_url` (an OAuth authorization-server URL) and
wires OAuth metadata routes (`create_auth_routes`) when
`auth_server_provider` is also set. Using `MCPServer`'s convenience path
at all would mean either adding real OAuth infrastructure (forbidden) or
constructing a fake/unused `issuer_url` purely to satisfy a type
constraint (misleading, and the SDK still wires OAuth-shaped machinery
around it).

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Compose `AuthenticationMiddleware`+`BearerAuthBackend`+`AuthContextMiddleware`+`RequireAuthMiddleware` directly (all public SDK classes) around the unauthenticated `MCPServer.streamable_http_app()` output | Real, SDK-tested bearer-auth code; zero OAuth surface; no fake issuer URL | Bypasses the SDK's one "supported" convenience method; must get middleware ordering right manually |
| B | Supply a dummy/placeholder `issuer_url` to satisfy `AuthSettings` and use `MCPServer`'s built-in path | Uses the "intended" API surface | Still wires OAuth protected-resource-metadata routes and semantics into a server that has no OAuth issuer; actively misleading given the "no token issuer" boundary |
| C | Hand-roll bearer-token checking as new custom middleware, ignoring the SDK's auth classes entirely | Full control | Reimplements logic the SDK already provides and tests; more code to maintain and get right ourselves |

### Decision

Chose A. Verified end-to-end before writing the committed test suite: a
manual smoke script using the real `mcp` client (`ClientSession.initialize()`
-> `list_tools()` -> `call_tool()`) against the composed app succeeded
with a valid bearer token and correctly returned 401 for missing/wrong
tokens (initially returned 421 "Invalid Host header" during that same
smoke pass due to an `allowed_hosts` wildcard-pattern gap for a bare
`Host` header with no port -- fixed by adding the bare-hostname form to
`LOCALHOST_TRANSPORT_SECURITY.allowed_hosts` in `app/mcp/server.py`,
confirmed harmless for real dynamic-port servers which always send an
explicit port).

### Consequences

- `app/mcp/server.py::build_mcp_server()` is the one place this
  composition lives; any future change to bearer-auth policy touches only
  that function, not `tools.py`'s per-tool scope checks (those stay
  independent, reading `get_access_token()` from the SDK's own
  contextvar, unaffected by how the token was originally verified).
- No OAuth authorization-server code, metadata endpoint, or issuer URL
  exists anywhere in this gate's surface.
- If a future gate legitimately needs OAuth (multi-tenant, cloud identity
  -- both explicitly out of scope through Gate 05), it would replace this
  composition with `MCPServer`'s `auth=`/`auth_server_provider=` path
  rather than extend it, since that is what those parameters are actually
  for.

## DEC-0011 — Load `.env` from the parent `ROOT` folder, before any other project import, with `override=True`

### Date

2026-08-27

### Context

User explicitly asked the app to load `D:\...\ROOT\.env` (one level above
`VietRagOps\`) instead of `VietRagOps\.env`. A first attempt just changed
`load_dotenv()`'s `dotenv_path` argument in place -- still failed
silently. Root-caused by bisecting every import in `app/main.py`'s chain:
importing `rag.lifecycle.pipeline` -> `rag.ingestion.markitdown` (an
unrelated, pre-existing transitive dependency) calls a bare `load_dotenv()`
of its own at *import time*, which finds `VietRagOps\.env` (nearest
ancestor from cwd) first and sets `GROQ_API_KEY` to an **empty string**
into `os.environ`. Since `app/main.py`'s own `app.api`/`app.core.config`
imports ran *before* its dotenv call, and `load_dotenv()` defaults to
never overriding an already-set variable, the correctly-targeted later
load silently lost to that empty value.

### Options

| Option | Description | Pros | Cons |
| --- | --- | --- | --- |
| A | Move the dotenv load to the very top of `app/main.py`, before any project import, and pass `override=True` | Fixes the root cause; authoritative regardless of import order anywhere else in the dependency tree | Slightly unusual to see `override=True`, needs a comment explaining why |
| B | Only change the `dotenv_path` in place, leave import order as-is | Minimal diff | Does not actually fix the bug -- proven by testing, this was tried first and failed |
| C | Patch `rag/ingestion/markitdown.py` or pin an env var to stop the third-party package's internal `load_dotenv()` call | Addresses the interaction at its other end | Touches unrelated, working, pre-existing code for a problem this app can fully solve on its own side; larger and riskier diff |

### Decision

Chose A. Verified via direct bisection (individually importing
`app.mcp.tools`, `rag.lifecycle.service`, `rag.lifecycle.pipeline`,
`rag.ingestion.markitdown` and checking `os.environ` before/after each)
before concluding this was the actual cause, not guessed. After the fix,
a live bounded Groq call through the real `/ask` endpoint succeeded
(`provider: groq`, `latency_ms: 3714.383`, `fallback_used: false`,
answer supported with a verified citation) -- confirming the fix works
end-to-end, not just in isolation.

### Consequences

- `ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"` in
  `app/main.py` is now the single source of truth for which `.env` file
  the running app loads, and it always wins over any other package's
  internal dotenv side effects.
- `VietRagOps\.env` is no longer read by the app at all (only the parent
  `ROOT\.env` is) -- any secrets/config the user still wants to keep in
  `VietRagOps\.env` specifically will no longer take effect; they should
  move to `ROOT\.env`; user was informed of this via the change itself.
- This fix is unrelated to Gate 05's own feature scope but was necessary
  to complete Phase 5.5's bounded live Groq proof, so it is included in
  this gate's file list rather than deferred.

## DEC-0012 — Consolidate to the project-local `.env` (supersedes DEC-0011's `ROOT`-parent path)

### Date

2026-08-27

### Context

DEC-0011 pointed `app/main.py` at `D:\...\ROOT\.env` (one level above
`VietRagOps\`) per the user's initial explicit request. That created a
real inconsistency this agent had not surfaced until asked directly: the
pre-existing `scripts/web_import.py` (Gate 03) already loads
`.env`/`.env.firecrawl.local` from *inside* the project
(`Path(__file__).resolve().parents[1] / ".env"` == `VietRagOps\.env`),
and `.env`/`.env.*` are already properly gitignored there. Two different
entry points into the same codebase would otherwise read two different
secret files.

### Decision

User confirmed: consolidate to `VietRagOps\.env` (moved the real values
there manually). `app/main.py::ENV_FILE_PATH` changed from
`parents[2] / ".env"` to `parents[1] / ".env"` -- now identical in
resolution to `scripts/web_import.py`'s `_REPO_ROOT / ".env"`. The
import-ordering fix from DEC-0011 (load dotenv before any other project
import, `override=True`) was kept -- that part of the fix is independently
correct regardless of which file is targeted, since it addresses
`markitdown`'s own internal `load_dotenv()` call winning the race by
import order, not by path.

### Verification

- `dotenv_values('.env')` (project-local) parsed 79 keys, `GROQ_API_KEY`
  56 characters, all 20 `GROQ_API_KEY_1..20` populated -- length/count
  only, values never read or printed by this agent.
- Re-ran the bounded live Groq proof against the consolidated file: real
  `/ask` call, `provider: groq`, `latency_ms: 5415.665`, `fallback_used:
  false`, `refusal: false`, 1 citation -- succeeded again, confirming the
  consolidation didn't regress the Phase 5.5 proof.
- Full suite: 319 passed, 0 failed. `compileall` clean. `git diff --check`
  clean except the same pre-existing `groq_client.py` EOF warning.

### Consequences

- `D:\...\ROOT\.env` (the parent folder) is no longer read by the app at
  all. The user manually moved its real values into `VietRagOps\.env`
  first; this agent did not read or copy any secret content itself.
- `app/main.py` and `scripts/web_import.py` now agree on exactly one
  secret-file location again.
- No secret values are recorded anywhere in `_agent_ops/` by this
  decision or its logging -- only the fact that the consolidation
  happened, why, and length/count-only verification evidence.

## DEC-0013 — Run the deferred Qwen live smoke via a directly-constructed router/client with an explicit larger timeout, and commit the Gate 05 slice

### Date

2026-08-27

### Context

A later session attempted to start Gate 06. Its mandatory entry gate
independently required two things Gate 05 had not yet satisfied: (1) a
real, successful, bounded local `qwen3:8b` Ollama smoke in
development/demo mode (Gate 05 had only an incidental timed-out call, not
a deliberate success), and (2) the Gate 05 slice actually committed,
separately from the pre-existing dirty overlay (Gate 05 had explicitly
deferred committing pending user authorization). Gate 06 was correctly
blocked and reported to the user with exactly these two missing items.
The user replied by quoting both missing items back and explicitly
instructing "do it for me please" -- authorizing both the live smoke and
the commit in the same message.

### Decision

1. **Smoke methodology.** Rather than calling the real `/ask` HTTP
   endpoint with the app's production `ProviderRouter` (which hardcodes
   `OllamaClient`'s 30s default timeout via `app/core/config.py`), the
   smoke constructed the real `AnswerGenerator` + real
   `get_context_builder()` (same real 37-doc corpus) directly in a
   script, paired with a real `ProviderRouter(provider="groq",
   mode="development")` whose `ollama_client` was an `OllamaClient`
   instance built with an explicit `timeout=300.0`. This is the same
   class, same fallback logic, same real local model -- only the
   client-side timeout budget differs, and only for this measurement.
   Chosen over lowering the bar to "attempt and accept a timeout" because
   a timeout caused purely by an undersized client budget (not a real
   provider/model failure) would not actually prove the Qwen path works;
   raising the bound to find the real completion time, then confirming a
   real success at that bound, is what "successful... smoke" in the
   entry gate requires. The production default (`OllamaClient`'s 30s,
   used by `get_provider_router()`) was deliberately left unchanged --
   this was a measurement/proof exercise for Gate 05's acceptance
   evidence, not a production tuning change, which is out of Gate 05's
   frozen scope.
2. **Commit scope.** Only the exact files `GATE_05_RESULT.md` (in "Exact
   source and dependency scope") plus this gate's own ops entries
   (`_agent_ops/DECISION_LOG.md`, `_agent_ops/IMPLEMENTATION_LOG.md`,
   `_agent_ops/PROJECT_CONTEXT_CARD.md`, `_agent_ops/RISK_REGISTER.md`,
   `_agent_ops/phase_context_cards/evolve_2026_08_26/README.md` and
   `GATE_05.md`, `_agent_ops/REPO_MAP.md`) were staged by explicit name.
   The pre-existing dirty overlay (`AGENTS.md`, five
   `skills/*/scripts/*.py` deletions, `tests/test_groq_rotation.py`, and
   the rest of the untracked `_agent_ops/` bootstrap layer --
   `PHASE_ROADMAP.md`, `archive/`, `env_templates/`, gate cards for gates
   other than 05, additional tools) was deliberately left unstaged, per
   the standing instruction to never use `git add .`/`-A` and to keep the
   Gate 05 slice separate from unrelated dirty state.

### Verification

- Real call succeeded at `timeout=300.0`: `provider: "ollama"`, `model:
  "qwen3:8b"`, `fallback_used: true`, `error: null`, `failure_kind:
  null`, `latency_ms: 105656.945`, grounded/correct Vietnamese answer,
  citation verified, `evidence_state: supported`. Two smaller bounds
  (30s via the real `/ask` endpoint, 90s via the same direct
  construction) were tried first and genuinely timed out -- not repeated
  to force a pass, but to find the real completion time honestly (see
  `GATE_05_RESULT.md`'s "Real latency finding").
- Full suite reconfirmed: 319 passed, 0 failed. `compileall` clean.
  Corpus validators and retrieval smoke reconfirmed bit-for-bit identical
  to the Gate 04 baseline. `git status --short -- data/ gates/` shows
  only the new `GATE_05_RESULT.md` itself.
- `git diff --check` after staging: only the same pre-existing
  `groq_client.py` EOF warning already documented in Gate 04/05.

### Consequences

- A new risk (RISK-0015) records the production timeout/real-latency gap
  discovered by this measurement.
- Gate 05 is now committed as its own slice, unblocking Gate 06's entry
  gate re-verification.
