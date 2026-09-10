# Gate 13-D — Grounding and defect diagnostic

**Status:** COMPLETE — diagnosis only; no production repair

**Gate objective:** determine why grounding failed, establish the root causes of
`max_tokens` omission, non-activating OpenRouter fallback, and the degraded Groq
control, then order the repairs by evidence.

**Scope boundary:** no provider generation call, GCP call, deployment, secret
read, research-lane execution, Gate 12-V rescore, golden-set edit, corpus/index
edit, dependency edit, or production-source edit occurred.

## Protocol and entry receipt

The frozen protocol was committed before analysis:

- Protocol: `gates/baselines/GATE_13D_PROTOCOL.json`
- Protocol commit: `464da8f` (`gate 13d freeze diagnostic protocol`)
- Protocol SHA-256: `efed5ef531b531d59b5b9885f205397b77403682cf52ad0b92fcabb8381bfe17`
- Entry HEAD: `5fb765d18e10604304796d7c4c1c8d608c3eeb7d`
- Entry `origin/main`: `5fb765d18e10604304796d7c4c1c8d608c3eeb7d`
- Entry dirty overlay: exactly 25 paths; Git index empty
- Interpreter: `.venv/Scripts/python.exe`, Python 3.13.9
- Full suite: `591 passed, 3 warnings` in 702.80 seconds, with an external
  `--basetemp` under `%TEMP%`
- Count-only `.env` inspection found one `RAG_MAX_OUTPUT_TOKENS` line at
  `.env:152`; its value was not read or printed. No source file references the
  variable.

The three warnings were the known Windows pytest-cache ACL warning and two
websockets deprecation warnings. There were no test failures.

### Gate 12-V files analyzed

The artifact directory was present and readable. SHA-256 values below were
computed before analysis and are retained as the identity of the evidence read.

| File | Bytes | SHA-256 |
|---|---:|---|
| `gates/artifacts/gate12v/groq/raw_responses.jsonl` | 170648 | `a54efd9ea807a6c5350a01374d8e8b01d99f63ab252ffc0e17b057f635637605` |
| `gates/artifacts/gate12v/groq/records.jsonl` | 393462 | `c6334f5911ca7ac307a7b2575a61698871b422236c26a11abe32e6918dd2d9e4` |
| `gates/artifacts/gate12v/groq/run_receipt.json` | 877 | `5aa235fbff0d3f5127dade8d8b34ddba8285c56b1857aa08e35e5443661d3f2c` |
| `gates/artifacts/gate12v/metrics_report.json` | 67919 | `4a4067cfa42da8c3db6cf4f0c576a64af5948801affdc563f1b068b7ee2938ec` |
| `gates/artifacts/gate12v/openrouter/raw_responses.jsonl` | 692088 | `1a32f496b08d29e056fad62323d0339ac0723290180a0fea35cc10286659b48a` |
| `gates/artifacts/gate12v/openrouter/records.jsonl` | 946201 | `7870301d1e5ba388903868f368bcc48d846a881e8c8b98adab511d3064ff7343` |
| `gates/artifacts/gate12v/openrouter/run_receipt.json` | 1064 | `eb6746b0be66cd12bfba2d1eaad12857d64470f1427bd2e2ec3905dff7d346eb` |

Retrieval-only inputs were the frozen product set `evals/datasets/golden_qa.jsonl`
(120 rows) and `data/chunks/chunks_500.jsonl` (695 chunks,
SHA-256 `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`).
The existing `evals/experiments/compare_retrievers.py` harness was run at
`top_k=10` and `top_k=50`; the latter was used only to identify hard candidate
pool misses.

## D1 — Metric audit

The implementation is `evals/metrics/gate12v_metrics.py:119-147` and the
frozen definitions are also recorded in `evals/gate12v_runner.py:349-359`.

| Metric | Exact definition | Groq observed | OpenRouter observed |
|---|---|---:|---:|
| Citation validity | Count final responses whose `CitationVerification.is_valid` is true; denominator is all 40 completed rows. Refusals are valid because `CitationVerifier.verify` returns valid for a refusal. | 40/40 | 40/40 |
| Citation validity, non-refusal | Same verifier result, restricted to non-refusal rows. | 15/15 | 24/24 |
| Grounding precision | On answerable rows, make a set of cited `chunk_id` values. Numerator is `cited ∩ relevant`; denominator is all unique cited IDs. | 8/29 = 27.6% | 11/46 = 23.9% |
| Grounding recall | On answerable rows, numerator is the same intersection; denominator is the sum of all relevant chunk IDs. | 8/37 = 21.6% | 11/37 = 29.7% |

The ID comparison performs no case folding, whitespace trimming, prefix/suffix
repair, separator conversion, or document-ID conversion. It applies `str()` to
the values and compares sets directly (`gate12v_metrics.py:141-147`). The
citation verifier separately maps citation IDs by exact `chunk_id` at
`rag/generation/citation_verifier.py:28-33`; its `normalize_text` call is for
quoted evidence text only (`:38-41`), not for IDs.

**D1 verdict: metric-sound.** The 100% validity and approximately 24% grounding
precision are not contradictory. They mean that the product cited chunks that
were genuinely in its retrieved context and quoted text found in those chunks,
while only 8/29 or 11/46 of those cited chunk IDs matched the independent
golden relevant set. Validity is local retrieval/evidence support; grounding is
gold-set semantic alignment. The anomaly therefore points to wrong retrieved or
selected evidence, not to a validity metric that silently measures the same
thing as grounding. Gate 12-V's grounding conclusion is not invalidated by a
metric-definition defect.

## D2 — Full retrieval-only evaluation

The golden set contains 116 answerable and 4 unanswerable rows, with 118
relevant IDs across the answerable rows. The harness metrics are macro averages
over the 116 answerable rows. Raw recall is shown both as the sum of per-query
recall fractions over 116 and as a micro `relevant-ID hits / 118` count. Raw
precision is `relevant hits / (116 * k)`. MRR is computed over the returned
top-10 list, matching the existing harness contract.

### Direct retriever path

`hybrid` is the no-reranker control. `hybrid_reranker` is the same hybrid
candidate path through `AdvancedHybridRetriever` with the configured lexical
reranker and source priority/recency disabled, matching the reranker branch of
`routes_query._build_answer_generator`. The runtime dense backend was
`sparse_semantic_fallback`, not the sentence-transformer model.

| Config | k | Recall | Recall raw | Recall micro | Precision | Precision raw | Any-hit queries | MRR |
|---|---:|---:|---|---|---:|---|---|---:|
| hybrid | 3 | 0.573276 | 66.500000/116 | 68/118 | 0.195402 | 68/348 | 67/116 | 0.469992 |
| hybrid | 5 | 0.629310 | 73.000000/116 | 75/118 | 0.129310 | 75/580 | 73/116 | 0.469992 |
| hybrid | 10 | 0.715517 | 83.000000/116 | 85/118 | 0.073276 | 85/1160 | 83/116 | 0.469992 |
| hybrid_reranker | 3 | 0.538793 | 62.500000/116 | 64/118 | 0.183908 | 64/348 | 63/116 | 0.463889 |
| hybrid_reranker | 5 | 0.625000 | 72.500000/116 | 74/118 | 0.127586 | 74/580 | 73/116 | 0.463889 |
| hybrid_reranker | 10 | 0.715517 | 83.000000/116 | 85/118 | 0.073276 | 85/1160 | 83/116 | 0.463889 |

On the direct retriever output, the reranker does not improve the headline
recall or precision and lowers MRR slightly. The product path has an additional
`ContextBuilder` support-score selection layer, so it was evaluated separately
without generating an answer:

| Product context path | k | Recall | Recall raw | Precision raw | Any-hit queries | MRR |
|---|---:|---:|---|---|---|---:|
| `use_reranker=false` (default) | 3 | 0.560345 | 65.000000/116 | 66/348 | 65/116 | 0.465897 |
| `use_reranker=false` (default) | 5 | 0.612069 | 71.000000/116 | 72/580 | 71/116 | 0.465897 |
| `use_reranker=false` (default) | 10 | 0.715517 | 83.000000/116 | 85/1160 | 83/116 | 0.465897 |
| `use_reranker=true` | 3 | 0.568966 | 66.000000/116 | 67/348 | 66/116 | 0.468938 |
| `use_reranker=true` | 5 | 0.616379 | 71.500000/116 | 73/580 | 72/116 | 0.468938 |
| `use_reranker=true` | 10 | 0.741379 | 86.000000/116 | 88/1160 | 86/116 | 0.468938 |

The reranker therefore gives only a small product-path lift after the second
selection stage; it does not remove the grounding defect.

### Category and difficulty breakdown

The following is the direct-harness breakdown. Each cell is
`recall@5 / precision@5 / recall@10 / precision@10`, followed by MRR in the
last column. Raw hit counts are retained in the `Q-hit` columns.

| Group | n | hybrid R5/P5/R10/P10 | hybrid Q-hit 5/10 | hybrid MRR | reranker R5/P5/R10/P10 | reranker Q-hit 5/10 | reranker MRR |
|---|---:|---|---|---:|---|---|---:|
| academic_schedule | 5 | .4000/.0800/.6000/.0600 | 2/5, 3/5 | .2867 | .4000/.0800/.4000/.0400 | 2/5, 2/5 | .4000 |
| course_registration | 6 | .8333/.2000/.8333/.1000 | 5/6, 5/6 | .5139 | .8333/.2000/.8333/.1000 | 5/6, 5/6 | .6389 |
| credit_requirement | 22 | .7727/.1545/.7727/.0773 | 17/22, 17/22 | .6530 | .7273/.1455/.7727/.0773 | 16/22, 17/22 | .5280 |
| curriculum_structure | 15 | .1333/.0267/.2000/.0200 | 2/15, 3/15 | .0500 | .0667/.0133/.2667/.0267 | 1/15, 4/15 | .0519 |
| email_usage | 4 | .7500/.1500/1.0000/.1000 | 3/4, 4/4 | .6607 | .7500/.1500/.7500/.0750 | 3/4, 3/4 | .6250 |
| graduation_requirement | 3 | 1.0000/.2000/1.0000/.1000 | 3/3, 3/3 | .7778 | .6667/.1333/1.0000/.1000 | 2/3, 3/3 | .7222 |
| policy_exception | 4 | .7500/.1500/.7500/.0750 | 3/4, 3/4 | .1625 | .7500/.1500/.7500/.0750 | 3/4, 3/4 | .2167 |
| source_conflict | 1 | 1.0000/.4000/1.0000/.2000 | 1/1, 1/1 | .3333 | .5000/.2000/1.0000/.2000 | 1/1, 1/1 | .3333 |
| student_account | 3 | 1.0000/.2000/1.0000/.1000 | 3/3, 3/3 | .7778 | 1.0000/.2000/1.0000/.1000 | 3/3, 3/3 | 1.0000 |
| training_regulation | 53 | .6415/.1283/.7736/.0774 | 34/53, 41/53 | .5018 | .6981/.1396/.7925/.0792 | 37/53, 42/53 | .5041 |
| easy | 51 | .5882/.1176/.6667/.0667 | 30/51, 34/51 | .4427 | .5686/.1137/.6471/.0647 | 29/51, 33/51 | .4226 |
| medium | 28 | .6429/.1357/.7143/.0750 | 18/28, 20/28 | .4527 | .6071/.1286/.7500/.0786 | 17/28, 21/28 | .4083 |
| hard | 37 | .6757/.1405/.7838/.0811 | 25/37, 29/37 | .5208 | .7162/.1459/.7838/.0811 | 27/37, 29/37 | .5628 |

The failure concentrates sharply in `curriculum_structure`: direct hybrid
recall@5 is 2/15 questions with any hit and macro recall 0.1333; the reranker
is 1/15 and 0.0667 at k=5. This is a corpus/chunking and ranking signal, not a
provider signal. `training_regulation` is the second largest failure mass.

### Hard misses and achievable ceiling

At raw top-50 candidate depth, both direct hybrid configurations missed the
same nine answerable questions entirely:

`gold_training_regulation_047`, `gold_credit_requirement_023`,
`gold_curriculum_structure_048`, `gold_training_regulation_049`,
`gold_credit_requirement_116`, `gold_curriculum_structure_013`,
`gold_credit_requirement_024`, `gold_training_regulation_001`,
`gold_curriculum_structure_014`.

This is the hard candidate-pool ceiling: 107/116 answerable questions (92.24%)
have a relevant ID somewhere in the top-50 raw retrieval output; the nine above
are not answerable by a generator restricted to that candidate pool. The shipped
default `/ask` path passes `top_k=5` to `ContextBuilder`, so its stricter
answerable correctness ceiling is 71/116 (61.21%) without the reranker and
72/116 (62.07%) with it. If the four unanswerable questions are also perfectly
refused, the corresponding all-120 ceilings are 75/120 (62.50%) and 76/120
(63.33%). These are retrieval ceilings, not measured generator accuracies.

### Cross-check against Gate 12-V's seven shared misses

The seven IDs classified in the closed Gate 12-V report as
`retrieval_miss_affecting_both` were:

`gold_curriculum_structure_013`, `gold_manual_003`,
`gold_policy_exception_012`, `gold_training_regulation_052`,
`gold_training_regulation_153`, `gold_training_regulation_163`, and
`gold_training_regulation_233`.

On the exact default product context path (`use_reranker=false`, selected
top-5), all 7/7 remain misses: agreement is 7/7. With the opt-in reranker,
`gold_manual_003` becomes a top-5 hit and the other 6 remain misses: agreement
is 6/7. The raw direct `HybridRetriever` top-5 is not the final product
context: it hit `gold_manual_003` and `gold_training_regulation_153`, so its
agreement is 5/7. This difference is evidence of the additional ContextBuilder
selection layer, not evidence that the Gate 12-V records were recomputed.

## D3 — Grounding root cause

Ranked by evidence:

1. **(b) Retriever/context ranking quality — dominant.** The default product
   top-5 path has only 71/116 answerable questions with any relevant chunk;
   direct hybrid recall@5 is 75/118 relevant-ID hits and direct hybrid misses
   33/116 questions at top-10. The `curriculum_structure` slice is especially
   poor. The reranker does not materially change the default ceiling.
2. **(c) Chunking granularity and annotation-to-fragment mismatch — major
   contributor.** Several curriculum tables and repeated regulation headings are
   split across many chunks. The retriever often returns adjacent fragments from
   the same document/heading while missing the one fragment named by the gold
   answer. This produces locally valid but gold-misaligned citations.
3. **(d) Dense backend/runtime mismatch — contributor, not proven index
   staleness.** The evaluated dense component reports
   `sparse_semantic_fallback`; the intended local sentence-transformer backend
   was not active. The current product chunks file is the frozen 695-chunk
   `chunks_500.jsonl`, and the prompt's already-verified identifier alignment
   rules out stale gold IDs. There is no evidence here that the index bytes are
   stale relative to the corpus; there is direct evidence that the intended
   embedding backend was unavailable and silently substituted.
4. **(e) Golden-set annotation quality — not supported as the dominant cause.**
   Five hard cases were inspected without editing the dataset. In all five, the
   named relevant chunk contains the question's requested heading/content:
   `gold_curriculum_structure_013`, `gold_training_regulation_047`,
   `gold_credit_requirement_023`, `gold_curriculum_structure_048`, and
   `gold_training_regulation_049`. The labels look correct, although title-only
   questions expose a narrow-fragment sensitivity.
5. **(a) Metric definition/normalization defect — not found.** D1 is
   metric-sound; validity and grounding measure different relationships.

The grounding failure is therefore a real retrieval/context-selection failure,
amplified by the unavailable dense model and corpus chunk structure. It is not a
provider-choice problem and not a reason to weaken the metric.

## D4 — `max_tokens` omission (RISK-0030)

The configuration contains the variable name at `.env:152`, but there is no
consumer in `app/core/config.py`, `answer_generator.py`, the router, or any
client. The exact product-path drop points are:

- `rag/generation/answer_generator.py:178-180` calls
  `provider_router.generate_json(prompt)` without `max_tokens`.
- The direct legacy seam at `answer_generator.py:204-207` calls
  `groq_client.generate_json(prompt)` without `max_tokens`.
- `rag/generation/provider_router.py:201-208` accepts `max_tokens`, and
  `:260-267` / `:413-419` forward it only when a caller supplied it. The
  caller does not supply it.
- `rag/generation/groq_client.py:165-172` and
  `rag/generation/openrouter_client.py:504-511` correctly add the wire field
  only when present. They are not the first drop point; the parameter is already
  absent before either client is entered.
- Ollama's structured path is `ollama_client.py:70-79` and its payload options
  are built at `:46-60`; it has no output-token argument in `generate_json`.
  DeepSeek similarly builds a fixed payload at `deepseek_client.py:37-45`.

**Blast radius:** every provider path reached through the product
`AnswerGenerator` lacks the configured cap. Gate 12-V observed
`max_tokens_present=false` on all 108 Groq and all 58 OpenRouter requests;
16/26 usage-bearing OpenRouter completions exceeded 1024 tokens and 2/2
usage-bearing Groq completions did as well.

**Smallest correct fix (prose only):** make the approved output budget a real
configuration field, pass it from `AnswerGenerator` into the router, and map it
to each provider's native request field (`max_tokens` for Groq/OpenRouter and
the provider-specific output option for Ollama/DeepSeek). Prove it with a
router propagation test plus request-body capture tests for every supported
client, including a no-value/disabled-policy case. Do not implement this in
Gate 13-D.

## D5 — OpenRouter fallback

`openrouter_client.py:368-373` builds the ordered chain and
`:504-511` sends the exact `models` array. Gate 12-V raw artifacts show all 58
requests carried:

`["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-31b-it:free"]`.

All 58 HTTP statuses were 200. Thirty-two bodies contained
`{"error":{"code":502,"message":"Upstream error from Nvidia: Service temporarily overloaded"}}`;
zero raw response reported Gemma as served. In the client, the body error is
detected and raised at `openrouter_client.py:535-537`. The exception handler at
`:609-631` may retry the same payload, but it never selects
`model_chain[1]` or issues a client-side fallback request.

The current OpenRouter documentation says that the `models` array is an
automatic ordered fallback and that an error, including downtime and rate
limiting, should trigger the next model:
<https://openrouter.ai/docs/guides/routing/model-fallbacks>.
The API reference documents 502 as an HTTP error response:
<https://openrouter.ai/docs/client-sdks/typescript/api-reference/generations>.
The observed shape is different: HTTP 200 carrying a top-level error object
whose embedded code is 502. The documentation does not explicitly guarantee
automatic model fallback for that non-standard HTTP-200 envelope.

**D5 classification:** the request was not malformed (the `models` array and
endpoint contract were present), so (b) is rejected. The evidence shows that
OpenRouter did not produce a fallback serving model for this exact HTTP-200
error shape, which is (a) as observed. The shipped client also has no
independent fallback request, so (c) is a contributing resilience gap: once the
gateway returned the envelope, the client could only raise/retry the same
request. Without a provider call, this gate cannot distinguish an undocumented
OpenRouter server-side trigger rule from a transient provider-routing defect;
that internal distinction is explicitly **not observed**. A future client-side
fallback would require a second POST to Gemma after the primary error, adding
at least one network/model latency interval and consuming another request/quota
unit (and any output quota for a successful fallback).

The 591 mocked tests could type the envelope but could not exercise OpenRouter's
server-side routing. In particular, `tests/test_openrouter_client.py:115-137`
asserts that the fake HTTP-200 envelope raises; no test supplies a first-error,
second-served sequence and asserts actual fallback metadata. A contract test
with a controlled HTTP double plus a separately authorized zero-cost live smoke
would be needed; neither was run here.

## D6 — Groq single-key consequence (RISK-0009)

The closed Groq receipt reports `total_keys=1`, model `qwen/qwen3.6-27b`, 108
generation POSTs, 2 successes, 67 `429_hits`, and 106 failures. The current
client confirms the one-key contract at:

- `rag/generation/groq_client.py:115-136`: exactly one `GROQ_API_KEY` is read;
  `_keys` is only a one-item compatibility view.
- `rag/generation/groq_client.py:177-184`: every attempt uses `self._key`;
  there is no discovery, rotation, pool, or per-key retry.

Raw timing and error evidence:

- 108 raw calls from `2026-09-08T12:37:39.132+00:00` through
  `2026-09-08T13:09:07.174+00:00`: 1888.042 seconds.
- Observed request rate: 108 / 31.467 minutes = 3.432 requests/minute
  (107 inter-start intervals = 3.400/minute).
- 67/108 HTTP 429 `rate_limit_exceeded`; 38/108 HTTP 400
  `json_validate_failed`; 2/108 HTTP 200 successes; 1/108 had no HTTP status
  in the captured record.
- Of the 67 rate-limit bodies, 55 said output-token-per-minute limit 1000 and
  “Request too large” (requested expected output 1026–2048 in those bodies),
  11 said output-token-per-minute limit 1000 with a retry interval of 3.24–36.72
  seconds, and 1 said input-token-per-minute limit 7000 with 2967 requested
  input tokens. The other 38 bodies were JSON validation errors, including one
  explicit “max completion tokens reached before generating a valid document”.

Groq's current rate-limit documentation states that limits apply at the
organization level, not per individual user/key; it also documents separate
ITPM/OTPM limits and a 429 response when exceeded:
<https://console.groq.com/docs/rate-limits>. Its current high-level free-limit
table lists `qwen/qwen3.6-27b` at 30 RPM, 1K RPD, and 8K TPM. The observed
3.432 RPM is far below 30 RPM, while the captured bodies directly report the
organization's OTPM/ITPM limits. The observations are therefore strongly
consistent with a single free organization quota being exhausted by oversized
reasoning/output requests, not with RPM exhaustion.

**Direct causal answer:** the evidence does **not** establish that the
RISK-0009 single-key remediation alone caused 67/108 rate limits. It establishes
that the allowed one-key lane exposed one organization-level quota and that
the missing `max_tokens` cap drove requests into the OTPM/ITPM limits. Multiple
keys within the same organization would not be evidence of more organization
quota, and multi-key rotation is prohibited by RISK-0009 and DEC-0033. The
remediation did, however, leave the program without a usable free Groq control
under this workload: only 2 raw responses succeeded and 36 questions degraded
through the development fallback trace. Future provider comparisons therefore
do not have a healthy Groq control until the owner chooses one of the following:

1. accept a degraded Groq lane and treat OpenRouter as primary without a
   control;
2. obtain one paid or higher-limit Groq key so the single-key control fits
   policy and workload; or
3. select a different provider as the control, with a new provider contract and
   fresh protocol.

This is an owner decision, not a Gate 13-D recommendation. Reinstating
multi-key rotation is not an option.

## D7 — Evidence-ordered repair plan

| Order | Defect | Root cause | Blast radius | Smallest correct fix | Proof test | Gate placement |
|---:|---|---|---|---|---|---|
| 1 | A — grounding | Retrieval/context selection misses or demotes gold chunks; dense backend silently falls back to sparse features; chunk fragments compete with adjacent fragments. | Default top-5 answerable ceiling is 71/116; grounding precision was 23.9% OpenRouter and 27.6% Groq. | Repair the retrieval-to-context contract so relevant chunks enter and remain in the configured context; choose the backend/chunking change from the new retrieval evidence rather than changing the metric. | Fresh 120-row retrieval gate with exact product `ContextBuilder` paths, raw recall/precision/MRR, top-50 hard-miss list, and cited-vs-gold diagnostics. | Own grounding-repair gate; first. |
| 2 | B — max_tokens | `RAG_MAX_OUTPUT_TOKENS` has no consumer and `AnswerGenerator` omits the router argument. | All observed Groq/OpenRouter requests; Groq OTPM collapse and OpenRouter overlong completions. | Propagate the configured budget through `AnswerGenerator` -> router -> each client wire body. | Configuration propagation test plus captured Groq/OpenRouter/Ollama/DeepSeek request-body assertions. | Can join the provider-remediation gate after A is frozen. |
| 3 | C — fallback | Server-side `models` fallback did not yield Gemma for HTTP-200 embedded 502; client has no independent second-model request. | 32 OpenRouter overload envelopes, 0 Gemma serving, no measured resilience. | Implement or contract-test a bounded client-side fallback after a typed primary error, preserving free-model and request-budget guards. | Controlled first-error/second-served sequence, actual served-model trace, request/quota accounting, and a fresh no-paid smoke. | Same provider-remediation gate as B, but after B propagation. |
| 4 | D — control | One authorized free Groq key cannot provide a stable control for this request/token workload; the immediate errors are org OTPM/ITPM limits. | Provider comparisons are not control-valid; 2/108 raw Groq successes. | Owner selects option (i), (ii), or (iii) above; no rotation workaround. | New approved control-provider protocol and live-call ledger. | Separate decision/validation gate; requires owner choice. |

Fixing B and C and immediately rerunning would still leave poor answers if A is
unresolved: a capped, resilient generator cannot answer a question when the
relevant chunk is absent from the product context, and a fallback model cannot
repair a semantically wrong retrieved chunk. **A is the one thing to fix
first.** It is the only defect that directly establishes a sub-70% default
answerable ceiling before generation; the metric audit shows that changing the
measurement would not be a valid shortcut.

The closed Gate 12-V NO-GO remains valid for its frozen run. A grounding repair
could change future grounding and answer-correctness outcomes; B could change
token, rate-limit, schema, and latency outcomes; C could change fallback and
reliability outcomes; D changes whether a future comparison has a control. None
of these repairs retroactively changes Gate 12-V, and B/C/D alone cannot make
the current grounding evidence pass.

## Limitations and non-claims

- No provider generation was made in Gate 13-D. The exact OpenRouter internal
  rule for HTTP-200 error envelopes remains unobserved; the result records the
  artifact-backed behavior, not a new live-provider claim.
- The retrieval run uses the frozen product `chunks_500.jsonl` and product QA
  set, not the frozen research lane. No Gate 07/08 file, metric, baseline, or
  dataset was invoked or rescored.
- The nine hard misses are hard misses within the tested raw top-50 candidate
  depth. They are not proof that the chunk text is absent from every possible
  future index.
- The 61.21%/62.07% ceilings are retrieval bounds for the current product
  top-5 context, not measured end-to-end correctness rates.
- Five annotation cases were manually inspected; that is evidence against a
  dominant annotation defect, not a full reannotation.
- The Groq documentation limits are current published high-level limits; the
  raw run's exact OTPM/ITPM values are the captured provider error bodies, not a
  claim that every free account has the same breakdown.

## Recommended next gate

**Recommended next gate: a separately authorized grounding-repair gate**
(proposed `Gate 13-D-R`), with a new protocol and no provider calls in its first
phase. It should repair and re-measure the exact product retrieval/context path
on all 120 rows, then stop at a retrieval verdict before any provider spend.
Only if that gate earns a materially higher answerable ceiling should a later
provider-remediation/control decision gate address B, C, and D.

## Closure state

- Result file: this file; no production behavior changed.
- Protocol freeze and hash are recorded above; protocol commit was verified
  before analysis.
- Full suite evidence is the D0 receipt above; production source remained
  unchanged during this gate.
- Final release commit and remote SHA are recorded in the final Git receipt and
  `_agent_ops/IMPLEMENTATION_LOG.md`; no overlay path is included in the stage.

## Gate 14-R correction addendum — reranker identity

Gate 13-D's reranker rows exercised `LexicalReranker`, not
`BAAI/bge-reranker-v2-m3`. The local `FlagEmbedding`/transformer runtime was
absent, and the configured BGE construction degraded to the lexical fallback;
therefore Gate 13-D's statement that the reranker did not help is not evidence
about the real BGE model.

Gate 14-R measured the corrected product-lane comparison on the same frozen
120-question set: E5-small ONNX int8 without BGE reached `88/116` answerable
question hits at top-10, while the real `BAAI/bge-reranker-v2-m3` reached
`89/116`. The +1-question (`+0.862 pp`) lift is below Gate 14-R's registered
`+3 pp` reranker threshold. The original Gate 13-D findings remain unchanged;
this addendum only corrects the reranker identity and interpretation. See
`gates/results/GATE_14R_RESULT.md`.
