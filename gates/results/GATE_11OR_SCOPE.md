# GATE 11-OR — OpenRouter Migration Scope

**Date:** 2026-09-07
**Scope:** Design and scoping only
**Protocol:** `gates/baselines/GATE_11OR_PROTOCOL.json`
**Provider/GCP spend in this gate:** USD 0.00 / 0 calls
**Repository artifact language:** English

This document records a bounded migration design. It does not implement an
adapter, change provider configuration, create a key, call a provider, call
GCP, rerun an evaluation, or authorize a later gate.

## OR-0 — Entry receipts

The required entry identity matched:

| Check | Receipt |
| --- | --- |
| Git root | `D:/Project cua Dat/VietRAGOps/ROOT/VietRagOps` |
| Branch | `main` |
| `git rev-parse HEAD` | `7e8db468be8eb45ce8de714ecdc8fbb542c1ad21` |
| `git -c http.sslBackend=openssl ls-remote origin main` | `7e8db468be8eb45ce8de714ecdc8fbb542c1ad21` |
| Remote note | The first bounded remote attempt could not connect to GitHub; one bounded retry returned the exact expected SHA. |
| `git status --short` | Exactly 26 paths, matching the authorized pre-existing overlay. |
| `git diff --cached --name-only` | Empty. |
| `git ls-files tests/test_groq_rotation.py` | Empty; the file remains untracked. |
| Full local suite | `564 passed, 2 warnings` is supplied program state and was not rerun in this design-only gate. |

The 26-path overlay observed at entry was:

```text
AGENTS.md
PROJECT_STATE.md
_agent_ops/PROJECT_CONTEXT_CARD.md
_agent_ops/REPO_MAP.md
_agent_ops/THIRD_PARTY_TOOLING.md
skills/implementation-logger/scripts/append_log.py
skills/project-context-cards/scripts/new_phase_card.py
skills/rag-eval-harness/scripts/compute_retrieval_metrics.py
skills/release-quality-gate/scripts/check_required_files.py
skills/zone-brain/scripts/scan_deps.py
_agent_ops/archive/
_agent_ops/env_templates/
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_03.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_04.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_EXECUTION_PROMPT.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_07_REPAIR_PROMPT.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_08.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_09.md
_agent_ops/phase_context_cards/evolve_2026_08_26/GATE_10.md
_agent_ops/tools/check_repo_hygiene.py
_agent_ops/tools/generate_context_card.py
_agent_ops/tools/scan_deps.py
_agent_ops/tools/summarize_implementation_log.py
gates/results/GATE_07_FIX_PROMPT.md
tests/test_groq_rotation.py
```

The approved pending correction was applied to the ignored, user-owned
`_agent_ops/SESSION_BRIEF.md`. Only its `Last Verified Commit` line changed:

```diff
-`17059a6` is the authoritative local governance commit at Gate 09R-C entry.
+`7e8db468be8eb45ce8de714ecdc8fbb542c1ad21` is the authoritative local governance commit; it is pushed and in sync with `origin/main`.
```

The rest of that file was preserved. Because `SESSION_BRIEF.md` is ignored by
`_agent_ops/.gitignore`, it is not a staged or tracked change.

The frozen protocol is valid JSON. Its SHA-256 is:

```text
894089365d9051eb2c7d4fd4636cdb209a52121dbcd93248864d71da454c77ed
```

No source file, dependency, deployment file, provider account, secret value,
GCP resource, or test file was modified. No provider or GCP call was made.

## OR-1 — Existing provider surface

### Router contract

`rag/generation/provider_router.py` exposes `ProviderRouter` and the immutable
`ProviderInvocation` result object.

Public methods are:

- `current_provider()` — accepts `mock`, `groq`, `ollama`, and `deepseek`; an
  unknown value becomes `mock`.
- `current_model()` — returns the selected client model or
  `deterministic-mock`.
- `status()` — reports the selected provider, mode, model, Groq availability,
  DeepSeek availability, and Ollama status without probing Ollama when it is
  not active.
- `generate_json(prompt, model=None, temperature=None, max_tokens=None)` —
  the structured generation entry point.
- `chat_with_tools(messages, tools)` and `chat(messages)` — agent chat paths;
  in the current build these paths are enabled only for Ollama.

`ProviderInvocation` carries `provider`, `model`, `payload`, `content`,
`tool_calls`, `fallback_used`, `error`, `failure_kind`, `mode`,
`primary_attempt`, `usage`, and `provider_error_body`.

The source declares four modes, not only the three user-facing axes named in
the gate prompt: `development`, `demo`, `research`, and `cloud`.
`FALLBACK_ELIGIBLE_MODES` is exactly `development` and `demo`.

Selection is configuration-driven through `LLM_PROVIDER` and `PROVIDER_MODE`.
`app/core/config.py` reads those settings and constructs two cached routers:
`get_provider_router()` for normal answers and `get_agent_provider_router()` for
the agent route.

### Fallback chain

| Selected provider | `development` / `demo` | `research` | `cloud` |
| --- | --- | --- | --- |
| `mock` | Deterministic mock result; no provider call. | Same. | Same. |
| `groq` | Groq first; any typed Groq failure is followed by local Ollama. The final invocation records the Groq `primary_attempt`. | Groq failure is terminal; no Ollama and no model substitution. | Groq failure becomes a deterministic mock result while retaining the primary failure kind. |
| `ollama` | Direct local Ollama generation. | Direct local Ollama if explicitly selected; no Groq rescue. | Selection is returned as `policy_denied` and becomes deterministic mock; localhost is not probed. |
| `deepseek` | Explicit DeepSeek only; its failure is not rescued by Ollama. | Explicit DeepSeek only. | Selection is returned as `policy_denied` and becomes deterministic mock. |

The Groq failure path is special-cased in `_resolve_groq_failure()`. The
Ollama and DeepSeek paths have separate provider-specific methods.

### Typed outcome names

The router returns `ProviderInvocation`; it does not emit a common exception
object. Its exact `failure_kind` string values are:

```text
rate_limited
auth_failure
timeout
network_failure
provider_error
config_error
policy_denied
```

Successful invocations normally carry `failure_kind=None`. Some direct
`chat()` error returns do not set a `failure_kind`, which is itself a current
contract detail to preserve or make explicit in an implementation gate.

The exact Groq exception classes imported and classified by the router are:

```text
GroqRequestError
GroqRateLimitError
GroqAuthError
GroqTimeoutError
GroqNetworkError
GroqProviderError
```

### Application and RAG call sites

| Location | Use |
| --- | --- |
| `app/core/config.py:271-279` | Builds the cached normal `ProviderRouter`. |
| `app/core/config.py:291-299` | Builds the cached agent `ProviderRouter`. |
| `app/api/routes_health.py:15-25` | Calls `status()`, `current_provider()`, and `current_model()` and exposes provider health. |
| `app/api/routes_agent.py:230-266` | Calls `status()`, `chat_with_tools()`, and `chat()` for `/agent/ask`. |
| `app/api/routes_query.py:16-39` | Uses the normal generator for the standard path, but its reranker branch constructs `AnswerGenerator` without a router. |
| `rag/generation/answer_generator.py:167-199` | Uses the injected router when present; otherwise it directly calls `GroqClient.generate_json()`. |
| `rag/generation/answer_generator.py:525-528` | Decides whether provider retry is allowed; currently only `groq` and `ollama` qualify when a router is injected. |
| `rag/generation/provider_router.py:160-405` | Internal provider dispatch, fallback, and Ollama chat implementation. |
| `rag/generation/__init__.py:7-20` | Exports the current client/router surface. |

Two additional generation entry points matter to the future blast radius even
though they are outside the requested `app/` and `rag/` call-site list:
`evals/experiments/run_generation_eval.py` constructs `AnswerGenerator` without
a router, and the frozen Gate 07/Gate 08 runners explicitly construct a
research-mode Groq router. The latter must remain untouched.

### Adapter pluggability assessment

The adapter shape is only partially pluggable. Dependency injection exists in
the constructor, but there is no shared `Protocol`, ABC, or common client
interface. The router has provider-name `if` branches, Groq-specific typed
exceptions and `_resolve_groq_failure()`, and `AnswerGenerator` has a direct
Groq fallback path. DeepSeek is a third isolated adapter, not proof of a
generic adapter boundary. Groq is special-cased in both the router and answer
generator.

### Key and dotenv path

- `app/main.py` loads the repository-local `.env` at
  `Path(__file__).resolve().parents[1] / ".env"` before project imports, unless
  `PYTHON_DOTENV_DISABLED` is truthy. It uses `override=True`.
- This ordering is deliberate: importing `markitdown` transitively invokes a
  bare `load_dotenv()` at import time, so a later project load could lose to an
  empty or partial value. The application load must stay first and authoritative.
- `GroqClient` reads `GROQ_API_KEY` and, outside `PROVIDER_MODE=cloud`, also
  discovers the numbered names `GROQ_API_KEY_1` through the configured count.
  It reads `GROQ_MODEL`, then `RAG_MODEL`, and has separate Groq base URL,
  timeout, retry, strategy, and jitter settings.
- `DeepSeekClient` reads `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`,
  `DEEPSEEK_BASE_URL`, and its timeout setting.
- The deployed API template binds the Secret Manager names
  `GROQ_API_KEY` and `FIRECRAWL_API_KEY`, version key `1`, to
  `vietragops-api`. No secret value was read.
- There is currently no `OPENROUTER_*` application or deployment binding.

### Test inventory and expected change surface

Counts below are observed test-function counts in the current checkout. They
are not a claim that the full suite was rerun in this gate. “Extend” means the
file must gain or adjust provider-contract coverage if Option A is implemented;
the exact number of new test functions must be frozen in that later gate.

| Test file | Current functions | Migration action |
| --- | ---: | --- |
| `tests/test_provider_router.py` | 4 | Extend with OpenRouter selection/status and structured-result cases; preserve current mock/Ollama assertions. |
| `tests/test_provider_policy.py` | 14 | Extend with OpenRouter success, configuration/error typing, non-research fallback, and research-lane denial cases; preserve Groq and DeepSeek policy cases. |
| `tests/test_cloud_provider_policy.py` | 3 | Extend with OpenRouter cloud failure and no-localhost-fallback cases; preserve current Groq cloud checks. |
| `tests/test_api_agent.py` | 6 | Extend if OpenRouter tool-call parity is promised; otherwise record deterministic fallback as an explicit regression. |
| `tests/test_api_health.py` | 3 | Extend if the health payload adds an OpenRouter availability field; no existing field may be silently removed. |
| `tests/test_answer_generator.py` | 3 | Extend to prove the reranker/direct-construction path cannot silently bypass the selected provider. |
| `tests/test_answer_generator_evidence_state.py` | 4 | No provider-semantic change required; deterministic evidence-state behavior stays unchanged. |
| `tests/test_groq_typed_errors.py` | 7 | No change; this is Groq regression coverage. |
| `tests/test_groq_rotation.py` | 6 | No change, no stage, no move, no delete; it remains an untracked local experiment. |
| `tests/test_ollama_client.py` | 2 | No change unless the existing Ollama contract is deliberately altered, which is outside this scope. |
| Gate 07/Gate 08 tests | Existing frozen suites | Zero changes; research protocol, runners, baselines, and results remain outside the migration. |

The minimum existing test files that must be extended for a full product
parity implementation therefore contain 33 current functions across six
files. The 13 current functions in the Groq-regression/rotation rows above
remain unchanged, and the exact new-test count is intentionally not invented
before the wire contract is frozen.

## OR-2 — OpenRouter versus current Groq contract

Official public documentation was read on 2026-09-07. No OpenRouter, Groq,
DeepSeek, Ollama, Firecrawl, or GCP API endpoint was called. “Verified” below
means documented on the linked first-party page; it does not mean this account
or a selected endpoint was authenticated or tested.

| Dimension | Groq as used today | OpenRouter | 1-to-1? |
| --- | --- | --- | --- |
| Base URL / endpoint shape | Code defaults to `https://api.groq.com/openai/v1/chat/completions`; the Groq API reference documents the same POST endpoint. | Official Chat Completions endpoint is `https://openrouter.ai/api/v1/chat/completions`. | Mechanical URL change, but not identical routing semantics. |
| Auth header | `Authorization: Bearer <key>` plus `Content-Type`; current code also sends a Groq-specific user agent. The environment name is `GROQ_API_KEY`. | `Authorization: Bearer <key>` plus `Content-Type`; optional `HTTP-Referer` and `X-OpenRouter-Title` are documented. The new environment name would be `OPENROUTER_API_KEY`. | No: key name, optional attribution, and provider identity change. |
| Model identifier format | Current runtime default is `qwen/qwen3.6-27b`; `GROQ_MODEL` and `RAG_MODEL` can override it. Gate 07 froze `openai/gpt-oss-120b` and `openai/gpt-oss-20b` on Groq. | Public model pages list `qwen/qwen3.6-27b`, `openai/gpt-oss-120b`, and `openai/gpt-oss-20b`. OpenRouter may route one slug to multiple upstream providers. | String format is reusable; serving identity is not. |
| Request body schema | Sends `model`, `temperature`, legacy `response_format: {type: json_object}`, `messages`, and optional `max_tokens`. | Chat Completions accepts the OpenAI-style fields and adds routing controls such as `provider`, `models`, and provider preferences. | Partial: the common body is close, but routing and parameter support must be frozen. |
| Response body schema | Assumes `choices[0].message.content` is a JSON string; extracts prompt/completion/total token counts from `usage`. | Documents the same `choices`/message/usage shape, but also supports routing metadata. A provider error can arrive as an `error` body without usable `choices`, including a non-streaming HTTP 200 after processing has started. | No: error-bearing 200 responses and metadata require explicit parsing. |
| Structured / JSON output mechanism | Current code sends legacy JSON mode `response_format: {type: json_object}` and parses the returned content with `json.loads()`. | Structured outputs use `response_format: {type: json_schema, json_schema: ...}` on compatible endpoints. Support is per endpoint/provider; exact legacy `json_object` behavior for every eligible endpoint is unverified. | No. This is a contract test, not a string replacement. |
| Streaming | Current client does not stream. Groq documents SSE when `stream=true`. | OpenRouter documents SSE. After a stream starts, failures are delivered inside SSE while HTTP remains 200; failover stops after partial output. | Default path is non-streaming, but streaming behavior is not 1-to-1. |
| Error shape and status codes | `urllib` raises `HTTPError`; code special-cases 429, 401, 500/502/503/504, network, and timeout, then maps exhausted attempts to Groq typed exceptions. Other HTTP errors reach the router's generic path. | Error envelope is `{error: {code, message, metadata}}` with canonical `error_type`; documented statuses include 400, 401, 402, 403, 404, 408, 413, 422, 429, 500, 502, 503, 524, and 529. | No. The adapter needs a new parser and mapping table. |
| Rate-limit semantics and headers | Groq documents organization-level RPM, RPD, TPM, TPD and related limits. Current code consumes `Retry-After`, performs local cooldown, and can rotate numbered keys outside cloud mode. | OpenRouter separates credit limits from rate limits, says additional accounts/API keys do not increase rate limits, may load-balance/fail over upstream providers, and documents `X-RateLimit-*` and `Retry-After` behavior. | No. Account credits, platform limits, upstream limits, and internal failover are different axes. |
| Per-request cost accounting | Current `GroqClient` records token usage only; Gate 07's separate `CostBudget` calculates cost from a frozen model price table. | OpenRouter documents per-token and possible per-request, reasoning, cache, image, and web-search pricing fields, deducts request cost from credits, and states that inference pricing is passed through without markup while credit purchase fees can exist. | No. Model/provider routing and billable dimensions must be recorded and frozen. |
| Timeout behavior | `GroqClient` default HTTP timeout is 120 seconds, configurable by `GROQ_REQUEST_TIMEOUT_SECONDS`; the current path is a blocking request. | OpenRouter documents request timeout options in SDK surfaces and HTTP 408 errors, but no fixed server-side cutoff for this raw HTTP path was found in the reviewed docs. | No. Client timeout and server/provider timeout need separate typed handling. |

### Non-1-to-1 dimensions that drive the real work

The non-mechanical work is: key/configuration names; OpenRouter's multi-provider
routing and hidden failover; structured-output compatibility; error-envelope
parsing including HTTP 200 error bodies; rate/credit semantics and headers;
provider and cost attribution; timeout mapping; and agent tool-call behavior.
The common `POST` shape and model-slug syntax reduce transport work but do not
establish behavioral equivalence.

### Model identity conclusion

The exact product default slug `qwen/qwen3.6-27b` is documented by both Groq and
OpenRouter as checked on 2026-09-07. The two Gate 07 research slugs
`openai/gpt-oss-120b` and `openai/gpt-oss-20b` are also listed on public
OpenRouter model pages. Therefore a product-lane migration does not inherently
require a model-id change. CI's fixture value `llama-3.3-70b-versatile` was not
treated as an OpenRouter-compatible slug; that exact mapping is unverified.

This does **not** mean “same model” or “same behavior.” OpenRouter documents
multiple providers for a model slug and automatic routing/failover. The
serving provider, tokenizer/cost path, supported parameters, latency, and
output behavior can differ. A provider change is therefore still a behavior
change even when the model string stays the same.

## OR-3 — Architecture options

### A. Add `OpenRouterClient` beside the existing adapters — recommended

Scope the new provider to product lanes (`development`, `demo`, and an
explicitly approved `cloud` deployment). Keep Groq as the current default until
the later implementation gate proves the new contract. The `research` lane
must remain Groq/provider-pinned.

Expected files:

- New `rag/generation/openrouter_client.py`.
- `rag/generation/provider_router.py` for client injection, explicit provider
  selection, typed OpenRouter outcomes, cloud behavior, and product-lane
  fallback policy.
- `rag/generation/answer_generator.py` to include OpenRouter in retry/provider
  metadata handling and remove or explicitly guard the direct-Groq bypass for
  production constructions.
- `rag/generation/__init__.py` for the public export if the new client is
  exported.
- `app/core/config.py` for provider/client configuration.
- `app/api/routes_query.py` so the reranker path does not silently bypass the
  configured router.
- `app/api/routes_health.py` for truthful provider status if the health
  contract is expanded.
- `app/api/routes_agent.py` only if OpenRouter tool calling is required for
  agent parity; otherwise the existing deterministic fallback must be declared
  and tested as a limitation.
- `.env.example`, `docker-compose.yml`, `README.md`,
  `deploy/gcp/api-service.yaml`, `deploy/gcp/README.md`, and, if the CI model
  selector is renamed, `.github/workflows/ci.yml`.
- A new provider-client test file plus the existing test suites listed in
  OR-1. `tests/test_groq_rotation.py` is excluded.

Pros:

- Preserves the proven Groq path and gives local rollback through configuration
  while the candidate is not selected.
- Keeps the change bounded to the provider layer and its real application
  wiring instead of rewriting all generation behavior.
- Allows a single OpenRouter key and no rotation, which is the cleanest future
  resolution path for RISK-0009.

Cons:

- The current router is not genuinely generic, so this is more than adding one
  file.
- OpenRouter's internal provider routing creates additional observability and
  data-policy decisions.
- Agent tool calls require explicit implementation; a JSON completion adapter
  alone does not make the current Ollama-only tool path work.

Blast radius: Medium, limited to non-research generation/configuration and
deployment wiring if the research boundary is enforced. Relative effort:
Medium; no schedule is claimed.

Rollback: keep Groq and the existing configuration path intact; for Cloud Run,
deploy the candidate revision with 0% traffic, verify its tagged URL, promote
only after acceptance, and restore 100% traffic to the healthy revision on
failure. Locally, restore the provider selector. No rollback action is part of
this gate.

What breaks if wrong: an unparsed OpenRouter error can be misreported as a
successful or generic answer; unsupported structured output can degrade to
deterministic fallback; hidden upstream failover can make cost/provider traces
false; and the agent route can silently remain deterministic if tool parity is
assumed but not implemented.

### B. Replace the Groq adapter outright

Expected files would include `rag/generation/groq_client.py` or its replacement,
`rag/generation/provider_router.py`, `rag/generation/answer_generator.py`,
`app/core/config.py`, health/agent/query wiring, local/deployment configuration,
documentation, and Groq/provider tests. The research runners and Gate 07/Gate
08 assumptions also depend on the Groq path.

Pros:

- Fewer apparent provider branches in the product runtime.
- One provider-specific implementation to maintain after a full cutover.

Cons:

- Removes the known rollback path and changes the current provider behavior at
  once.
- Risks losing Groq typed-error, usage, retry, and cloud policy behavior.
- Makes old CI/docs/configuration and direct `AnswerGenerator` uses stale in
  one step.

Blast radius: High. Relative effort: High.

Rollback: requires reverting the replacement code and redeploying; an env-only
rollback is not sufficient once the Groq adapter is gone. The approved 0%
traffic candidate pattern still applies to deployment, but the source change
is broad.

What breaks if wrong: research execution and frozen evidence comparability,
Groq regression coverage, provider-specific error classification, and any
caller that still expects Groq client attributes.

Tests touched: the provider policy, cloud provider policy, router, health,
answer-generator, and Groq typed-error suites would be changed or rewritten;
the rotation test and all Gate 07/Gate 08 tests remain prohibited from change.

This option is **disqualified** if it touches the research lane or replaces the
Groq path used by the frozen Gate 07/Gate 08 runners.

### C. Insert a thin gateway abstraction and put every provider behind it

Expected files would include a new shared provider protocol/gateway module,
all current clients, `provider_router.py`, `answer_generator.py`, app config,
health/agent/query wiring, deployment/configuration files, and most provider
tests. A correctly designed gateway would normalize payloads, typed errors,
usage, timeout, and provider metadata.

Pros:

- The adapter boundary would become genuinely pluggable.
- Error and cost normalization could be designed once.
- Future providers would have a clearer extension point.

Cons:

- Largest blast radius for a migration whose immediate need is one additional
  product provider.
- High risk of changing stable fallback, trace, or deterministic semantics while
  also changing the provider.
- A gateway does not remove OpenRouter's endpoint-level structured-output and
  upstream-routing decisions.

Blast radius: High. Relative effort: High.

Rollback: revert the gateway and all client adaptations as one coordinated
source change, then use the approved Cloud Run traffic restoration pattern.
This is materially less reversible than Option A's additive adapter.

What breaks if wrong: every provider invocation can change shape, error typing,
fallback, or trace fields; a subtle normalization error can affect Groq,
Ollama, and DeepSeek at the same time.

Tests touched: a new gateway-contract suite plus the provider router, provider
policy, cloud policy, health, agent, answer-generator, and client regression
suites would be affected; Gate 07/Gate 08 tests remain prohibited from change.

An implementation that edits the research runner to pass through the gateway
is **disqualified** by the frozen research-lane rule. A non-research-only
gateway is technically possible but is not the least-risk scope for this
migration.

### Recommendation

Recommend exactly **Option A**, restricted to the non-research product lanes,
with single-key OpenRouter configuration and an explicit decision about
OpenRouter provider routing, JSON schema support, agent tool calls, and cost
attribution. This recommendation follows the evidence: the exact product slug
is available on both public catalogs, the existing product router already has
an additive provider-selection seam, and retaining Groq makes rollback local
and operationally understandable. Option B is disqualified for a global
cutover; Option C spends a larger blast radius to solve a broader abstraction
problem that this gate does not need.

### Frozen research-lane constraint

Gate 07 and Gate 08 froze the research lane against pinned providers and models.
**Gate 07 and Gate 08 froze the `research` lane against pinned providers and
models. Changing the provider on the research lane would destroy comparability
with the frozen Gate 07 baselines and invalidate the only evidence the program
has. The research lane must stay provider-pinned. Any option that touches it is
disqualified.**

The migration therefore cannot be a global “Groq to OpenRouter” replacement.
It can only be a separately approved product-lane adapter while the frozen
research path remains unchanged.

## OR-4 — Rotation and RISK-0009

`tests/test_groq_rotation.py` was read and remains untouched. It implements:

- API-key redaction assertions.
- Multi-key discovery from `GROQ_API_KEY_1` through the configured
  `GROQ_KEY_COUNT`, plus the legacy `GROQ_API_KEY`, with empty values skipped
  and duplicates removed.
- Round-robin key selection.
- Cooldown skipping for a key that is currently unavailable.
- Retry after HTTP 429 using `Retry-After`, rotating from a failing key to a
  succeeding key.
- Redacted operational statistics for the key set.

The test does not ship, but the operative question is whether rotation enters
`app/` or `rag/`. It does: the current tracked
`rag/generation/groq_client.py` contains numbered-key discovery, round-robin
selection, cooldown, and retry logic. Its cloud-specific branch restricts
discovery to the single `GROQ_API_KEY`, but non-cloud configuration can activate
the indexed-key path. Therefore keeping the test untracked is not, by itself,
a complete RISK-0009 resolution.

The governing boundary is narrower than “does the test exist”: RISK-0009
targets multi-account key pools used to evade a provider's quota controls. No
future OpenRouter option may use multiple keys against one provider account.
OpenRouter's official limits documentation also states that making additional
accounts or API keys does not increase rate limits.

A single-key OpenRouter configuration makes rotation unnecessary for the new
provider. It is the cleanest available resolution path because it avoids
quota-striping and gives the product one explicit `OPENROUTER_API_KEY`.

### Proposed future RISK-0009 register update — not applied here

Keep the current register row unchanged during this design gate. After a
separately approved implementation has retired the active multi-key path and
proved the product configuration, replace its mitigation with:

```text
Use exactly one OPENROUTER_API_KEY for the OpenRouter product lane; do not add
numbered OpenRouter keys, rotate keys, or use additional accounts to evade
provider limits. Keep the research lane on its frozen provider and model.
Retire the current Groq multi-key path from app/rag only under a separately
approved change, and retain tests/test_groq_rotation.py as the untracked,
untouched historical experiment.
```

The corresponding future status should be:

```text
Mitigated — single-key OpenRouter product configuration verified; no rotation
is active in app/rag; research lane remains provider-pinned.
```

Until those conditions are proven, the status must remain open. No RISK-0009
register change was made in this gate. Any option that requires multiple keys
against one provider account is disqualified on policy grounds, not technical
grounds.

## OR-5 — Cost model and caps

### Structural comparison

- Groq's current code reports token usage but does not calculate a price in the
  client. The earlier research ledger uses a frozen input/output price table,
  reserves a conservative maximum before each call, and settles against actual
  usage afterward.
- The Groq model page reviewed for `qwen/qwen3.6-27b` displayed USD 0.60 per
  million input tokens and USD 3.00 per million output tokens at verification
  time. This is a time-sensitive documented price, not an account quote.
- OpenRouter's public `qwen/qwen3.6-27b` page displayed USD 0.30 per million
  input tokens and USD 2.00 per million output tokens at verification time. The
  page also shows that providers can have different effective prices.
- OpenRouter's FAQ describes model/provider pricing that is generally per
  input/output token, with some models or features charging per request, image,
  reasoning, or other unit. It describes credit prepayment and says inference
  pricing is passed through without markup, while purchasing credits can carry a
  fee. Exact account credit state and current effective cost were not checked.
- No USD-to-VND conversion is used here. No current OpenRouter account price,
  credit balance, rate limit, or bill was observed.

### Proposed implementation-gate cap

Propose a hard cap of **USD 0.50** for the eventual bounded implementation
gate. This is a derived control policy, not an observed price and not a target
to spend. It must be re-approved against the current price pages before any
provider call.

The future product ledger must preserve the earlier reserve/settle semantics:

1. Freeze the eligible model/provider price table before the first call.
2. Estimate input tokens and reserve the cost of estimated input plus the
   maximum output before each request.
3. Settle with actual input/output usage when the response supplies it.
4. If a billable response has no reliable usage, conservatively retain the
   reservation rather than claim zero cost.
5. Stop before the next request when `spent + reserved + next_reservation`
   would exceed USD 0.50.
6. Freeze the number of application retries and the OpenRouter internal
   provider-fallback policy. The docs reviewed do not establish a safe
   account-specific rule for the cost of every hidden upstream attempt, so an
   implementation must either bound that behavior explicitly or reserve a
   conservative maximum.

The frozen Gate 07 research ledger and its protocol must not be modified or
reused to alter the research lane. Product migration accounting should use the
same reserve/settle semantics in a product-owned, separately approved path.

### Cost observability impact

The migration would add observability requirements: requested model, selected
OpenRouter model slug, provider/routing metadata when available, input/output
tokens, reserved cost, settled cost, whether usage was complete, retry/fallback
counts, HTTP status, and typed `error_type`. It must not log prompts, keys, or
other secret values.

OpenRouter's internal provider selection means the application must not report
`provider: openrouter` as though it were the final upstream endpoint unless the
trace deliberately distinguishes the gateway from the serving provider.

The existing GCP gap remains: current GCP spend is not observable read-only.
Only an interactive Console sign-in or a billing export reaches consumption;
the latter is a mutation with cost. No billing export was created, and no GCP
cost observation was attempted in this gate.

## OR-6 — Secret and deployment impact

Names and paths only are recorded below. No secret value was read or written.

| Surface | Future required name/path | Impact |
| --- | --- | --- |
| Local application | Repository-local `.env`; `OPENROUTER_API_KEY`, plus an OpenRouter model/base URL/timeout configuration if adopted | `app/main.py` already loads this file first with `override=True`; do not create or edit it in this gate. |
| Safe template | `.env.example`; placeholder `OPENROUTER_API_KEY` and non-secret provider settings | Documentation/configuration update only in the implementation gate. |
| Local Docker | `docker-compose.yml`; a Docker-side input such as `VIETRAGOPS_DOCKER_OPENROUTER_API_KEY` mapped to `OPENROUTER_API_KEY` | Required if Docker is expected to exercise the new provider; no live call is authorized by this scope. |
| Secret Manager | Existing approved GCP project `vietragops-evolve-20260831`; new secret container name `OPENROUTER_API_KEY`, version `1` | Creating the secret and entering its value require a separate cloud/secret approval. |
| Cloud Run service | `deploy/gcp/api-service.yaml`, service `vietragops-api`; `LLM_PROVIDER=openrouter`, `PROVIDER_MODE=cloud`, and a secretKeyRef named `OPENROUTER_API_KEY` at version key `1` | Replaces the provider binding only in a later deployment gate. The public web service does not need the provider key. |
| CI | `.github/workflows/ci.yml` currently has no provider key binding and no live-provider step; it only sets a `GROQ_MODEL` fixture | Do not add a provider secret to CI. Rename the non-secret model fixture only if the implementation changes the generic configuration contract. |
| Documentation | `README.md`, `deploy/gcp/README.md` | Add names and no values in a later approved documentation update. |

The private `vietragops-api` service would need a new Cloud Run revision when
its environment, secret binding, or image changes. Deploying that revision is
out of scope here.

The standing rollback model is the approved one: deploy the candidate revision
with 0% traffic, verify its tagged URL, promote it only after verification, and
restore 100% traffic to the healthy revision on failure. No alternative
rollback model is proposed and no deployment occurred.

`RISK-0026` (“API unavailable” in the web UI, cause unknown) must be resolved
before any provider migration ships. Otherwise an unexplained API-path fault
would make a provider migration failure unattributable. `RISK-0024` remains a
separate intermittent web-capacity issue; changing Cloud Run `minScale` is not
part of this scope.

## Limitations and implementation-gate entry conditions

- No live OpenRouter request was made, so request acceptance, exact JSON mode
  behavior, actual error bodies, account eligibility, provider selection,
  account rate limits, and measured latency are unverified.
- Public model pages establish catalog presence, not authenticated access or
  endpoint-level parameter support. Structured-output support is explicitly
  documented as endpoint/provider-specific.
- The official pages and prices are time-sensitive. The values above must be
  refreshed and frozen before spend.
- No Groq, DeepSeek, Ollama, Firecrawl, or GCP call was made.
- The supplied `564 passed, 2 warnings` suite state was not rerun. This gate
  validates JSON syntax and the scope receipts only.
- Gate 07 and Gate 08 were not rerun, rescored, or modified. The rejected Gate
  08 alignment method remains rejected.
- Gate 09 and Gate 10 were not started.
- The current Groq client contains multi-key rotation outside cloud mode; the
  future single-key OpenRouter design does not erase that current source fact.
  RISK-0009 remains open until a later approved change proves retirement.

Before any implementation or deployment gate, require at least: resolution of
RISK-0026; a frozen OpenRouter request/response/error/structured-output
contract; a decision on OpenRouter upstream routing and data policy; a single
key and account-scope approval; the USD 0.50 reserve/settle ledger; unit and
route tests; and an explicit proof that the research lane and Gate 07/Gate 08
artifacts remain byte- and behaviorally out of scope.

## Final verdict

**REFORMULATE** — OpenRouter is worth evaluating as a bounded, single-key
product-lane adapter under Option A, but a global Groq migration is not
decision-safe. The exact product slug is available on both public catalogs, yet
OpenRouter changes routing, structured-output support, errors, rate/credit
semantics, cost attribution, and potentially model behavior. The research lane
must remain provider-pinned, RISK-0026 must be resolved before shipping, and a
separately approved implementation gate must prove the live contract under the
proposed hard cap.

## Sources

- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq OpenAI Compatibility](https://console.groq.com/docs/openai)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq Supported Models](https://console.groq.com/docs/models)
- [OpenRouter Chat Completions API Reference](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion)
- [OpenRouter Errors and Debugging](https://openrouter.ai/docs/api_reference/errors-and-debugging)
- [OpenRouter Credit and Rate Limits](https://openrouter.ai/docs/api_reference/limits)
- [OpenRouter Provider Routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter FAQ](https://openrouter.ai/docs/faq)
- [OpenRouter Qwen3.6 27B](https://openrouter.ai/qwen/qwen3.6-27b)
- [OpenRouter gpt-oss-120b](https://openrouter.ai/openai/gpt-oss-120b)
- [OpenRouter gpt-oss-20b](https://openrouter.ai/openai/gpt-oss-20b)

## Closure Receipt

```text
Closure Receipt
- CURRENT_TASK.md      : updated (Gate 11-OR completion, evidence, next step)
- IMPLEMENTATION_LOG.md: appended 2026-09-07/Gate 11-OR scope
- SESSION_BRIEF.md     : state + Last Verified Commit -> 7e8db468be8eb45ce8de714ecdc8fbb542c1ad21 (approved one-line correction; all other lines preserved)
- PROJECT_CONTEXT_CARD : not needed (the file is part of the pre-existing 26-path overlay; result and DEC-0031 carry the new scope state)
- DECISION_LOG.md      : DEC-0031 added
- RISK_REGISTER.md     : not needed (RISK-0009 future update was proposed but explicitly not applied; no new risk was registered)
- REPO_MAP.md          : not needed (no code files were added, moved, or removed)
```
