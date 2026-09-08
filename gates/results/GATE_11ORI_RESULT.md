# Gate 11-OR-I Result — OpenRouter Free-Tier Product Adapter

Date: 2026-09-08
Protocol: `gates/baselines/GATE_11ORI_PROTOCOL.json`
Protocol SHA-256: `8CC81C03B29722F23895FA2560489BE05FD07A15C7987EE9FCDE584A34C4B591`

## Verdict

**Implementation and local proof complete; the correction restores the measured
NVIDIA model as the product primary and keeps Gemma 31B as the configured
fallback.** The `.env` primary/fallback lines were already correct and were not
edited. The research lane remains provider-pinned and cannot reach OpenRouter.

No paid generation request, GCP call, deployment, Gate 07/08 rerun, Gate 09,
or Gate 10 action occurred.

## I1 — Entry and baseline receipts

- `git rev-parse HEAD` and `git -c http.sslBackend=openssl ls-remote origin main`
  both returned `8363f5d6b5247857c92ffcea6f2ab5c4626f2c39`.
- Entry state had 26 pre-existing dirty paths and an empty index.
- Bare command `.venv\Scripts\python.exe -m pytest -q` reproduced the host ACL
  failure: `433 passed, 2 warnings, 131 errors in 105.08s`; the 131 errors
  occurred while pytest scanned `C:/Users/ADMIN/AppData/Local/Temp/pytest-of-ADMIN`
  and hit `WinError 5` during `tmp_path` setup.
- The established diagnostic command
  `.venv\Scripts\python.exe -m pytest -q --basetemp D:\GRADUATION_THESIS\_gate11ori_pytest_basetemp_20260908`
  returned `564 passed, 3 warnings`. The third warning was the pre-existing
  `PytestCacheWarning` for the repository `.pytest_cache` ACL.
- The original untracked rotation experiment collected 6 tests. It was later
  moved and renamed without content changes under I7; the post-move collection
  returned 583 tests and zero archive matches.

## I2 — Live catalog and contract

Catalog endpoint: `GET https://openrouter.ai/api/v1/models`
Snapshot UTC: `2026-09-08T08:29:45.883697+00:00`
Catalog total: 428 models. Fixed zero-priced `:free` entries: 16. The live
snapshot contained 5 NVIDIA/Nemotron entries and 11 non-NVIDIA entries, so the
expectation that free models were NVIDIA-dominated was not observed.

The prose claim “4 of 16 declare response_format” was a counting error: the
live table contains 5 such entries and 3 with `structured_outputs`. The four
models selected for I3b, excluding the already measured Gemma 31B, were correct.

| Free model | Context | `response_format` | `structured_outputs` | `tools` |
|---|---:|:---:|:---:|:---:|
| `cohere/north-mini-code:free` | 256000 | no | no | yes |
| `dots-studio/dots-3-note-preview:free` | 512000 | yes | yes | yes |
| `google/gemma-4-26b-a4b-it:free` | 262144 | yes | no | yes |
| `google/gemma-4-31b-it:free` | 262144 | yes | no | yes |
| `inclusionai/ling-3.0-flash-fin:free` | 262144 | no | no | yes |
| `inclusionai/ling-3.0-flash-sante:free` | 262144 | no | no | yes |
| `liquid/lfm-2.5-2.6b:free` | 65536 | yes | yes | yes |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256000 | no | no | yes |
| `nvidia/nemotron-3-super-120b-a12b:free` | 262144 | yes | yes | yes |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1000000 | no | no | yes |
| `nvidia/nemotron-3.5-content-safety:free` | 128000 | no | no | no |
| `nvidia/nemotron-3.5-lightning:free` | 1000000 | no | no | yes |
| `poolside/laguna-s-2.1:free` | 262144 | no | no | yes |
| `poolside/laguna-xs-2.1:free` | 262144 | no | no | yes |
| `thinkingmachines/inkling-small:free` | 1048576 | no | no | yes |
| `thinkingmachines/inkling:free` | 1048576 | no | no | yes |

The two largest fixed free models, Nemotron Ultra and Thinking Machines
Inkling, do not declare `response_format`; they are excluded from the current
`generate_json()` contract despite their larger context windows.

OpenRouter contract sources reviewed:

- [Models API](https://openrouter.ai/docs/guides/overview/models) — catalog
  fields and `supported_parameters`.
- [Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
  — JSON Schema support is model-dependent.
- [Limits](https://openrouter.ai/docs/api-reference/limits) and
  [FAQ](https://openrouter.ai/docs/faq) — at least $10 purchased credits gives
  1000 free-model requests/day; the documented free-model ceiling is 20 RPM.
- [Errors and debugging](https://openrouter.ai/docs/api-reference/errors) —
  `{ "error": { "code": number, "message": string, "metadata": object } }`,
  typed `error_type`, `Retry-After`, and non-streaming errors inside HTTP 200.
- [Model fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks)
  — the `models` array is ordered fallback routing; the response identifies the
  model that ultimately served the request.
- [Provider logging](https://openrouter.ai/docs/guides/privacy/provider-logging)
  — provider data policies vary; this gate accepts training-permissive free
  endpoints while keeping OpenRouter-side prompt logging off.

## I3 / I3b — Bounded live probes

All prompts were synthetic and contained no corpus, user data, PII, or secrets.
I3 used 6 generation requests. I3b used 7 additional requests, at a different
probe session time, for an original total of 13 generation requests. The
owner-supplied correction adds five further free Nemotron requests, bringing the
gate total to 18.

### I3 initial table

| # | Model / format | Result | Strict JSON | Usage / route |
|---:|---|---|---|---|
| 1 | Nemotron Super / `json_object` | HTTP 200 body error `502`, NVIDIA overload | UNMEASURED | no usage; no provider response |
| 2 | Gemma 31B / `json_object` | HTTP 200 success, 2108.7 ms | raw yes; fenced yes | prompt 23, completion 11, total 34; Google AI Studio; cost 0 |
| 3 | Gemma 26B / `json_object` | HTTP 429 upstream shared pool | UNMEASURED | Google AI Studio; retry/capacity error |
| 4 | Dots / `json_object` | HTTP 200, 3344.5 ms, no content | no content | completion 64, reasoning 75, total 98; AtlasCloud; cost 0 |
| 5 | Liquid / `json_object` | HTTP 429, `Retry-After=37` | UNMEASURED | Liquid shared-pool rate limit |
| 6 | Gemma 31B / `json_schema` | HTTP 429 upstream shared pool | UNMEASURED | Google AI Studio; no schema verdict |

Transient HTTP 429/502 observations are recorded as `UNMEASURED`, never as a
capability failure.

### I3b narrowed table

| # | Model / format | Result | Strict JSON / reasoning | Usage / route |
|---:|---|---|---|---|
| 1 | Nemotron Super / `json_object` | HTTP 200 body error `502`, 1696.0 ms | UNMEASURED | NVIDIA overload |
| 2 | Dots / `json_object` | HTTP 200, 4909.9 ms, `finish_reason=length` | raw no; fenced no; `message.reasoning` separate, 1170 chars | completion 256, reasoning 299, total 293; AtlasCloud; cost 0 |
| 3 | Liquid / `json_object` | HTTP 200, 2410.6 ms, `finish_reason=stop` | raw yes; fenced yes; `message.reasoning` separate, 538 chars | prompt 37, completion 137, reasoning 125, total 174; Liquid; cost 0 |
| 4 | Nemotron Super / `json_schema` | HTTP 200 body error `502`, 853.6 ms | UNMEASURED | NVIDIA overload |
| 5 | Gemma 26B / `json_object` | HTTP 200, 3330.5 ms, `finish_reason=stop` | raw yes; fenced yes; reasoning field present as null | prompt 26, completion 11, total 37; Google AI Studio; cost 0 |
| 6 | Nemotron Super retry / `json_object` | HTTP 200 body error `502`, 1285.8 ms | UNMEASURED | NVIDIA overload |
| 7 | Nemotron Super retry / `json_schema` | HTTP 200 body error `502`, 834.2 ms | UNMEASURED | NVIDIA overload |

Operating decision before the correction: Gemma 31B was the only end-to-end
measured candidate in I3/I3b. The owner-supplied correction evidence below
supersedes that routing decision without changing the frozen research lane.

### I3c — Owner-supplied Nemotron correction evidence

Five additional live free requests to `nvidia/nemotron-3-super-120b-a12b:free`
were observed outside the original I3/I3b ledger and are added to the gate
total. All five returned `cost: 0`; paid spend remains zero.

| Attempt(s) | Prompt / result | Structural evidence |
|---:|---|---|
| 1 | Trivial JSON prompt, `json_object`, `max_tokens=400`: HTTP 200 in 3.6 s | `provider=Nvidia`, `finish=stop`, raw `content` passed `json.loads()`, cost 0 |
| 2 | Realistic Vietnamese RAG prompt, `json_object`, `max_tokens=1024`, `temperature=0.1`: HTTP 200 in 16.9 s | `finish=stop`, `reasoning_tokens=410`, `completion_tokens=494`; reasoning was in a separate field and raw `content` passed `json.loads()`, cost 0 |
| 3 | Repeat: HTTP 200 carrying `error.code=502` | `error.message` reported NVIDIA upstream temporary overload; no `choices` key; cost 0 |
| 4–5 | Two further owner-observed attempts | Both failed; individual response details were not supplied, so no narrower shape is claimed; cost 0 |

The observed NVIDIA sample is **2 successes / 5 attempts** (40% success,
60% failure), with intermittent overload arriving inside HTTP 200 as an error
envelope. The successful realistic answer's quality was not assessed. The
separate reasoning field resolves the prior content-interleaving concern, but a
longer response can still exhaust `max_tokens=1024`; the client now rejects
`finish_reason=length` as a typed provider error before attempting JSON parsing.
Recommendation: treat `RAG_MAX_OUTPUT_TOKENS=1024` as potentially inadequate for
longer reasoning-heavy product answers and consider a larger owner-approved
value after measuring latency and fallback behavior. The `.env` value was not
changed; adequacy remains unverified.

## I4 decision and owner boundary

The owner correction supersedes the interim Gemma recommendation. DEC-0032 now
selects Nemotron Super as the operating product primary and Gemma 31B as the
fallback in the OpenRouter `models` array. The `.env` lines already expressed
that configuration; this gate did not edit `.env`. No unverified-primary flag
is part of the routing contract.

## I5–I6 — Implemented contract

- `rag/generation/openrouter_client.py` is isolated and uses `urllib` only.
- Exactly one `OPENROUTER_API_KEY` is read. No indexed OpenRouter key name is
  read anywhere in Python code.
- The client validates every `models` entry against the frozen I2 catalog and a
  live catalog fetched before the completion request. Missing, changed, or
  non-zero pricing fails closed before the completion transport is opened.
- `OPENROUTER_ALLOW_PAID_MODELS` defaults off; enabling it emits a warning and
  is visible in status. The gate never enabled it.
- Typed errors cover rate limit, auth, timeout, network, provider, and config
  outcomes. HTTP 200 error bodies are parsed as errors, including an error body
  with no `choices` key. A `finish_reason=length` response is a typed provider
  failure and is rejected before `json.loads(content)`. `Retry-After` is honored
  with a bounded backoff.
- Status contains provider/model/availability/ledger/routing metadata and no
  key. Logs contain requested/served model, served upstream, status, usage,
  typed error, and remaining allowance, never prompts or keys.
- `ProviderRouter` selects OpenRouter only explicitly, never as a Groq/Ollama/
  DeepSeek fallback. Research mode returns deterministic `policy_denied` with
  no HTTP attempt.
- `AnswerGenerator` uses the configured router by default; explicit injected
  legacy test clients retain their test seam.
- `.env.example` contains empty OpenRouter setting names only. `.env` was not
  edited.

## I7 — Groq retirement and archive

- Removed indexed discovery, round-robin selection, strategy switching,
  per-key cooldown map, and per-key redacted statistics.
- Preserved request path, timeout, typed 429/401/5xx/network/timeout
  classification, single-key backoff, and `Retry-After` handling. Groq now
  reads exactly one `GROQ_API_KEY`.
- Updated tracked typed-error expectations to the single-key contract and added
  an all-mode regression guard for indexed variables.
- Moved the untouched untracked experiment to
  `_agent_ops/archive/groq_rotation_experiment.py`; original SHA-256:
  `30A7AC21DF261BF5E6A2E76AAB71D18FD279D678778DB866F03C38EC43F04349`.
- `_agent_ops/archive/README.md` records evidence-only retention and DEC-0033.
- `pytest --collect-only -q --basetemp ...` returned `583 tests collected` and
  `archive_collection_line_count=0`. The archive directory remains in the
  pre-existing overlay and is never staged.

## I8 — Ledger

The client uses a per-process reserve/settle ledger keyed to the UTC calendar
day. It reserves before a completion request, settles after the transport, and
retains the reservation for ambiguous or dispatched outcomes. It refuses the
next request at 1000. The ledger is not persisted across process restarts; the
limitation is explicit in client status and this result.

## I9 / I10 — Tests and proof

- Full suite command:
  `.venv\Scripts\python.exe -m pytest -q --basetemp D:\GRADUATION_THESIS\_gate11ori_pytest_basetemp_after_i7_20260908`
- Result before the correction tests: **590 passed, 3 warnings** in 308.50
  seconds. The two deprecation warnings are from websockets; the third is the
  known `.pytest_cache` `PytestCacheWarning` caused by host ACLs.
- I10 rerun with the same command and basetemp: **591 passed, 3 warnings** in
  418.75 seconds. The same three warnings remained; no test failure occurred.
- Pre-I7 result was 589 passed with the 6 rotation tests still collected. After
  archiving those six, the new all-mode Groq guard and retry-after guard
  reconciled to 590 before the Nemotron correction tests.
- `requirements.txt`, `Dockerfile`, and `deploy/` were not changed.
- The five owner-supplied Nemotron requests are added to the original 13-request
  total: **18 observed live generation requests** across the gate. All five were
  free requests with `cost: 0`; total paid spend is zero.
- The account/key credit checks before and after live probes returned
  `limit=0.2`, `limit_remaining=0.2`, `usage=0`, and `usage_daily=0`.
- The bare pytest ACL failure is retained under RISK-0027; all before/after
  comparisons use the same external-basetemp method.

## I11 — Registers and limitations

- DEC-0032 adopts measured Nemotron as the product primary with Gemma 31B as the
  `models` fallback. The two successful Nemotron runs establish structural JSON
  capability and separate reasoning-field placement; they do not establish
  answer quality or endpoint reliability.
- DEC-0033 retires Groq rotation and supersedes DEC-0030 with archive
  disposition (a).
- RISK-0009 is mitigated. RISK-0028 records measured Nemotron capability,
  intermittent overload, the 60% small-sample failure rate, and the fallback
  mitigation. RISK-0029 records the training-permissive/PII boundary.
- The lane is not a privacy-preserving research lane, not a Gate 07/08
  replacement, and not evidence for provider reliability beyond the bounded
  probes above. Free availability, upstream congestion, catalog drift, and
  model deprecation remain possible.

## Closure boundary

I10 is complete. The named implementation, test, gate-result, and register
files are ready for the explicitly requested commit and push. No deployment,
GCP call, paid request, research-gate rerun, or `.env` edit is part of this
closure.
