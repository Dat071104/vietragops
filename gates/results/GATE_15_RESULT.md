# Gate 15 — Retrieval tuning, then generation repair and re-run

**Status:** CHECKPOINT — Phase A complete; Phase B B1/B2 repaired offline;
waiting at the owner decision checkpoint B3 before any live generation request.

## Protocol and entry receipts

- Frozen protocol: `gates/baselines/GATE_15_PROTOCOL.json`.
- Protocol freeze commit: `ce26941`.
- Protocol SHA-256: `6feb4d7cbd5bf38b44adde252bda9adc8075dcfd3efef51cd4c0e839c5f20c0e`.
- Entry HEAD and `origin/main`: `86dd77d5ce58857d9330b19df8f8d3e1cacd44e1`.
- Entry overlay: exactly 25 pre-existing paths; Git index empty.
- Interpreter: `.venv\Scripts\python.exe`.
- A0 suite reproduction: `598 passed, 3 warnings` in `389.80` seconds with an
  external `--basetemp`.
- Count-only `.env` presence check found `.env`; no value was read or printed.
- No provider generation request, GCP call, deployment, research-lane write,
  golden-set/corpus/manifest/chunk-store write, or secret access occurred.

## A0 — Frozen Phase A bar and Phase B entry condition

The protocol fixed these conditions before Phase A measurement:

1. selected product default answerable ceiling at least `83/116`;
2. `curriculum_structure` at least `7/15` question hits; and
3. raw top-50 question hits at least `104/116`.

All three were required to authorize Phase B. The sparse top-5 control had to
reproduce `71/116` before interpreting any lever.

## A1 — Top-k decision

The three premises behind the Gate 14-R top-k decision were independently
checked:

- `RAG_MAX_INPUT_TOKENS_SOFT` has no consumer in `app/`, `rag/`, `evals/`, or
  `scripts/`; top-k is not truncated on the wire. The variable name was checked
  by count-only presence inspection; its value was not printed.
- The OpenRouter catalog embedded in `rag/generation/openrouter_client.py`
  records context length `262144` for both the configured Nemotron primary and
  Gemma fallback.
- Top-5 already exceeds the nominal 3,000 budget in the current PromptBuilder
  path, so the former top-5 rationale does not distinguish top-5 from top-10.

Prompt token measurements used the active E5 tokenizer over all 120 questions:

| top_k | mean | p50 | p95 | max | rows over 3,000 |
|---:|---:|---:|---:|---:|---:|
| 5 | 3,080.61 | 3,121 | 3,552 | 3,654 | 75/120 |
| 8 | 4,786.65 | 4,891 | 5,745 | 5,756 | 117/120 |
| 10 | 5,900.53 | 5,952 | 7,186 | 7,251 | 119/120 |
| 12 | 7,052.17 | 7,116 | 8,700 | 8,711 | 119/120 |

Retrieval-only results on the frozen 116 answerable questions:

| path | k | ceiling | 95% Wilson | macro recall | macro precision | MRR | curriculum hits / 15 | wall-clock |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| sparse hybrid | 5 | 71/116 | 0.521160–0.695793 | 0.612069 | 0.124138 | 0.452730 | 3/15 | 39.718 s |
| sparse hybrid | 8 | 78/116 | 0.582676–0.751098 | 0.668103 | 0.085129 | 0.461299 | 5/15 | 41.412 s |
| sparse hybrid | 10 | 83/116 | 0.627536–0.789681 | 0.715517 | 0.073276 | 0.465897 | 6/15 | 38.083 s |
| sparse hybrid | 12 | 88/116 | 0.673268–0.827393 | 0.758621 | 0.064655 | 0.469750 | 7/15 | 39.069 s |
| dense E5 int8 | 5 | 73/116 | 0.538591–0.711739 | 0.625000 | 0.127586 | 0.455603 | 3/15 | 67.767 s |
| dense E5 int8 | 8 | 83/116 | 0.627536–0.789681 | 0.715517 | 0.091595 | 0.468278 | 6/15 | 76.529 s |
| dense E5 int8 | 10 | 88/116 | 0.673268–0.827393 | 0.758621 | 0.077586 | 0.472876 | 7/15 | 73.136 s |
| dense E5 int8 | 12 | 91/116 | 0.701183–0.849544 | 0.784483 | 0.066810 | 0.475161 | 8/15 | 72.743 s |

Top-10 is the adopted value: it adds `15/116` (`12.931` percentage points)
over the current dense top-5 default and `5/116` over dense top-8. Top-12 adds
only `3/116` more than top-10 while adding `1,151.64` mean tokens and lowering
macro precision. The product `/ask` default was changed from 5 to 10 in
`c6395df`, with a pinning test. `ContextBuilder` still requests 50 candidates;
this is a selection-side change, not an index-depth change.

## A2 — Fusion anomaly

The implementation uses equal-component reciprocal-rank fusion:
`HybridRetriever` retrieves 50 BM25 and 50 dense candidates, scores each list
with `1 / (rrf_k + rank)`, uses `rrf_k=60`, and truncates the fused list to 50.
`AdvancedHybridRetriever` then applies fixed `0.7` reranker / `0.3` hybrid
normalization and fixed authority/recency weights when that path is enabled.
No corpus-specific tuning artifact exists; these are inherited constants.

Raw product-path measurement:

| candidate path | top-50 question hits |
|---|---:|
| sparse hybrid control | 107/116 |
| dense E5 hybrid | 104/116 |
| union of the two product candidate sets | 110/116 |

The net `107 -> 104` loss is a rank-fusion truncation effect, not missing
component recall. Six sparse-found questions were absent after dense fusion:

- `gold_email_usage_002` — sparse-fused rank 25;
- `gold_training_regulation_163` — rank 13;
- `gold_training_regulation_233` — rank 31;
- `gold_credit_requirement_032` — rank 27;
- `gold_training_regulation_012` — rank 29;
- `gold_training_regulation_154` — rank 41.

Dense recovered three sparse misses: `gold_curriculum_structure_048`,
`gold_credit_requirement_116`, and `gold_curriculum_structure_013`. Equal RRF
therefore lets candidates present in both lists crowd out single-component
hits at mid-ranks; the “three lost” figure is the net change, not the number of
individual sparse-found rows discarded.

Fusion alternatives were evaluated at product top-10. Component extraction was
shared (`37.872` seconds); context-selection wall-clock was measured separately:

| fusion | raw top-50 hits | top-10 ceiling | 95% Wilson | macro recall | macro precision | MRR | curriculum |
|---|---:|---:|---|---:|---:|---:|---:|
| RRF k=60 (current) | 104/116 | 88/116 | 0.673268–0.827393 | 0.758621 | 0.077586 | 0.472876 | 7/15 |
| RRF k=10 | 104/116 | 85/116 | 0.645718–0.804877 | 0.732759 | 0.075000 | 0.490894 | 7/15 |
| normalized weighted, dense=.25 | 106/116 | 85/116 | 0.645718–0.804877 | 0.732759 | 0.075000 | 0.478773 | 7/15 |
| normalized weighted, dense=.75 | 104/116 | 88/116 | 0.673268–0.827393 | 0.758621 | 0.077586 | 0.512521 | 8/15 |

The `.75` row improves MRR and the curriculum slice but does not improve the
ceiling. Selecting it from this same set would be optimistic. RRF k=60 remains
the recommendation until a separately frozen tuning/holdout set can test a
coverage-preserving fusion policy.

## A3 — Mechanical verdict

The Phase A bar **PASSED**:

- selected default ceiling: `88/116 >= 83/116`;
- `curriculum_structure`: `7/15 >= 7/15`;
- raw top-50 ceiling: `104/116 >= 104/116`.

Phase B is authorized by the frozen protocol. The new retrieval ceiling is
`88/116 = 75.86%`, compared with the current dense top-5 `73/116 = 62.93%`
and original sparse top-5 `71/116 = 61.21%`. The raw union shows six remaining
candidate-pool misses at depth 50; these are a mixture of corpus/chunk coverage
and fusion ranking. This phase did not justify an annotation-quality claim.

## B1/B2 — Offline generation repairs completed; no live calls

- `RAG_MAX_OUTPUT_TOKENS` is read with code default `2048`, chosen to leave room
  for the observed reasoning workload while allowing structured answer output.
- `AnswerGenerator` now passes `max_tokens` to the router and legacy Groq seam.
  ProviderRouter passes it to Groq, OpenRouter, DeepSeek, and Ollama; the latter
  uses Ollama's `options.num_predict` wire field.
- `RAG_MAX_INPUT_TOKENS_SOFT` is not silently treated as enforcement. The new
  name `RAG_INPUT_TOKEN_BUDGET_ADVISORY` is primary, the old name is a
  compatibility alias, and an over-budget prompt emits a warning with no hidden
  truncation.
- OpenRouter now submits the primary model in one request. On typed retryable
  failures, including the exact observed HTTP-200 embedded 502 envelope, it
  submits a separate fallback-model request. Every request is counted in the
  daily ledger and `Retry-After` is honored.
- Offline focused provider/client tests: `79 passed, 1 warning` in `0.53 s`.
  The exact 502 test observed two captured request bodies, primary then Gemma,
  with both requests carrying `max_tokens=2048`, and ledger usage `2`.
- Final full suite after the Gate 15 source and test changes: `603 passed,
  3 warnings` in `433.08` seconds with an external `--basetemp`. Relative to
  the `598 passed, 3 warnings` entry baseline, the five additional passing
  tests are the top-k pin, exact OpenRouter fallback contract, and four client
  wire-budget assertions; no existing test was removed.

## B3 — Owner checkpoint; live phase not started

No fresh Phase B live protocol has been committed because the first generation
request is forbidden until the owner chooses the control posture. The available
options are:

1. accept a single-lane OpenRouter measurement with no Groq control;
2. obtain an approved higher-limit single-key Groq control; or
3. approve a different control provider.

Groq key rotation is not an option. After the choice, a fresh B4 protocol must
be committed before any request, with the 40-question Gate 12-V sample,
free-only slugs, at most 200 requests, 20 RPM pacing, actual served-model
tracking, and zero paid spend. Gate 12-V remains closed and will not be
rescored.

## Scope not measured

This checkpoint does not measure answer quality, provider availability under a
fresh live run, actual fallback serving, cloud mode, deployment readiness,
concurrency, multi-turn behavior, the agent/MCP path, or authenticated API
access. No deployment or GCP action is authorized.
