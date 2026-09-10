# Gate 16 — Generation parameter tuning and fallback policy repair

**Status: NO-GO for deployment; closed locally.** No GCP call, deployment,
Cloud Run revision, Secret Manager mutation, IAM mutation, paid request, or Git
push occurred. The result is a candidate OpenRouter configuration and a repaired
client policy, not deployment authorization.

## Protocol and commit receipts

| Item | Receipt |
|---|---|
| Entry protocol | `gates/baselines/GATE_16_PROTOCOL.json`, commit `5cbc9ce`, canonical SHA-256 `sha256:b84668c11c100309d7f7e3e91112143a3947e13813859565d16e6bf5c139e869`, file SHA-256 `sha256:4c7f888211fbf8fd3c93eda73c70259fac93605159a86d905bf1ca2532880d8` |
| G5 protocol | `gates/baselines/GATE_16_G5_PROTOCOL.json`, commit `35cf218`, canonical SHA-256 `sha256:c846d24a757c1b28c726b2f8a04bb0accbbb14dbbe6becda8e68006ff429f826`, file SHA-256 `sha256:bb0bdd729ef1325474a57bdeccb7f1bee5a032e3c21b40396b313d573f252a13` |
| Source/test repair | `7e7da2c` — reasoning configuration, upstream-only fallback, daily accounting, global governor, offline tests |
| G5 runner extension | `4a20e41` — frozen 40-question recorder mode |
| Entry HEAD / remote | `6124dfed8976c4698541d688147e790d5d507b8d` / same |
| Final raw G3 artifacts | External ignored root `C:/Users/ADMIN/AppData/Local/Temp/vietragops-gate16-g3-r1-20260910`; cfg1 `sha256:0a005fe9deeb1ecd7ef133e87c334e0ddbcf1940abe0b2b48c7709f5043b3093`, cfg2 `sha256:42aee48d4db828f96d71a622449c6c11b1cd7bded005066f547fc870acc741b5`, cfg3 `sha256:5ad90d7840ca97d82d92f8cca1f958594d79f31dea96d4862b7e815633fbe6e0`, cfg4 `sha256:bc7c5c824b13f8e6cf068ca054c26dba8b34edd74f2a6c83d8c57d987065abd9` |
| Final raw G5 artifact | External ignored root `C:/Users/ADMIN/AppData/Local/Temp/vietragops-gate16-g5-20260910/cfg3.json`, SHA-256 `sha256:c6739dee88cf27c16f14368cb3302de0bd221e184a5e272bcb9d2125a9ff7193` |

## G0 — Entry gate

- HEAD and `origin/main` matched the required `6124dfed8976c4698541d688147e790d5d507b8d`.
- The pre-existing dirty overlay was exactly 25 paths and the index was empty.
- `.env` was checked by presence count only: one line each for the OpenRouter
  key/model/fallback variables and the legacy Groq key. No secret value was
  printed, stored, or committed.
- The external-basetemp baseline was **603 passed, 3 warnings** in `529.06s`
  with `.venv\Scripts\python.exe`. The warnings are the known websockets
  deprecations and the host `.pytest_cache` ACL warning.
- The account preflight before generation returned HTTP 200 with
  `limit=0.2`, `limit_remaining=0.2`, `usage=0`, and `usage_daily=0`. The same
  count-only read after G5 remained at those values; all generation slugs were
  `:free`.
- An initial probe request was stopped after one request because the local
  environment was missing the already-frozen `tokenizers==0.23.2` runtime and
  had downgraded to sparse retrieval. That one request is counted in the G3
  budget and excluded from scoring. Restoring the exact Gate 14-R pin (without
  torch, transformers, or sentence-transformers) produced an ONNX-active smoke:
  `rrf(offline_bm25+onnx:intfloat/multilingual-e5-small:int8_dynamic_weight)`,
  `state=active`, `degraded=false`, top_k=10.

## G1 — Offline output-budget sizing

The distributions below are from `usage.output_tokens_actual` and
`usage.reasoning_tokens_actual`; missing values are provider/error rows, not
zeros.

| Artifact | Token field | n | p50 | p90 | p95 | p99 | max | missing |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Gate 12-V OpenRouter | completion | 26 | 1,151 | 2,846 | 5,407 | 5,456 | 5,941 | 32/58 |
| Gate 12-V OpenRouter | reasoning | 26 | 711 | 1,552 | 2,382 | 3,721 | 4,552 | 32/58 |
| Gate 15-B B4 valid retry | completion | 46 | 1,660 | 2,048 | 2,048 | 2,048 | 2,048 | 18/64 |
| Gate 15-B B4 valid retry | reasoning | 46 | 906 | 2,161 | 2,451 | 2,633 | 2,635 | 18/64 |

All 17 B4 `finish_reason=length` rows had `completion_tokens=2048`; they are
right at the artificial cap. The B4 cap therefore censored the upper tail. A
defensible next cap is **8192**: it is above the previously observed
completion p95 of 5,407 and the observed maximum of 5,941, leaving 2,251 tokens
above that maximum. The 262,144-token context window makes this structurally
feasible. Gate 12-V also observed approximately 84 visible content tokens
against approximately 410 reasoning tokens on a realistic prompt, so the
budget was being consumed mainly by reasoning, not answer text.

## G2 — Reasoning control

The implementation follows the current OpenRouter documentation rather than
memory:

- [Reasoning Tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
  documents `reasoning.effort` values `max`, `xhigh`, `high`, `medium`, `low`,
  `minimal`, and `none`; `reasoning.max_tokens` as a reasoning-token budget;
  `reasoning.exclude` to omit reasoning from the returned response while still
  reasoning; and `reasoning.enabled` for default enablement.
- The same page documents model-catalog fields such as
  `supported_efforts`, `default_enabled`, `supports_max_tokens`, and
  `mandatory`. A mandatory model must not be sent `effort=none`.
- [OpenRouter Models](https://openrouter.ai/docs/guides/overview/models) documents
  `supported_parameters` and model-specific capability discovery.

The live catalog read returned Nemotron as free, 262,144 context, reasoning
`default_enabled=true`, `mandatory=false`, `supported_efforts=["medium",
"low"]`, and `supports_max_tokens=true`. Gemma was free, 262,144 context,
reasoning `default_enabled=false`, with no mandatory flag. The selected
`reasoning={"effort":"none"}` was accepted by Nemotron in G3 and G5: G3 cfg3
returned 8/8 HTTP-200 responses with `reasoning_tokens=0`; G5 returned 38/38
HTTP-200 responses with `reasoning_tokens=0`. This proves the wire parameter was
accepted and the observed reasoning usage fell to zero; it does not prove an
internal provider implementation detail beyond that observable behavior.

The client now supports explicit constructor/request configuration plus the
environment keys `OPENROUTER_REASONING_EFFORT`,
`OPENROUTER_REASONING_MAX_TOKENS`, `OPENROUTER_REASONING_EXCLUDE`, and
`OPENROUTER_REASONING_ENABLED`. With no setting, it sends no reasoning field;
G3 selected the carried setting. Expected effects—less truncation and latency,
with possible multi-step correctness loss—were tested rather than assumed.

## G3 — Configuration probe

The eight pre-registered IDs were `dev_q003`, `dev_q006`, `dev_q012`,
`gold_credit_requirement_096`, `gold_curriculum_structure_006`,
`gold_manual_002`, `gold_manual_003`, and `gold_training_regulation_068`.
The selection rule was frozen before the probe: first require length rate at or
below 5%, then maximize hand-correct answers, minimize provider-availability
failures, maximize first-attempt schema, minimize p95 latency, minimize
reasoning p95, and use fixed tie order cfg3/cfg4/cfg2/cfg1.

| Config | POSTs | Finish | First schema | Latency p50/p95 ms | Completion n/p50/p95/max/missing | Reasoning n/p50/p95/max/missing | HTTP / typed errors | Served models | Hand C/P/W/R | Frozen / corrected |
|---|---:|---|---:|---:|---|---|---|---|---|---|
| cfg1 Nemotron, default, 2048 | 9 | stop 7, length 2 | 7/8 | 18,598 / 37,122 | 9/934/2048/2048/0 | 9/614/2666/2709/0 | 200x9; provider_error 2 | Nemotron 9 | 5/1/0/2 | 4/8 / 4/8 |
| cfg2 Nemotron, default, 8192 | 11 | stop 7, no finish 4 | 7/8 | 17,477 / 39,294 | 7/955/1890/2134/4 | 7/580/1326/1338/4 | 200x9, 429x2; 502x2, rate 2 | Nemotron 7; Gemma 0 | 5/0/1/2 | 5/8 / 5/8 |
| cfg3 Nemotron, effort none, 8192 | 8 | stop 8 | 8/8 | 15,393 / 26,292 | 8/416/734/984/0 | 8/0/0/0/0 | 200x8; success 8 | Nemotron 8 | 6/1/0/1 | 6/8 / 6/8 |
| cfg4 Gemma primary, 8192 | 16 | no finish 16 | 0/8 | 9,328 / 11,891 | no usage | no usage | 429x16; rate 16 | Gemma 0 | 2/1/4/1* | 1/8 / 1/8 |

`*` cfg4's final answers were deterministic product fallbacks after Gemma was
rate-limited; they are not Gemma outputs. cfg2 issued two Gemma fallback
requests after two embedded Nemotron 502 envelopes; both were 429 and no Gemma
answer served. cfg4 issued no fallback because the repaired rate-limit policy
correctly retries the same Gemma model and does not switch models on 429.

The full per-answer hand reading is recorded compactly as:

| Config | ID order in the frozen probe | Hand labels (C/P/W/R) |
|---|---|---|
| cfg1 | `dev_q003, dev_q006, dev_q012, credit_096, curriculum_006, manual_002, manual_003, training_068` | `C, R, C, C, P, R, C, C` |
| cfg2 | same | `C, R, C, C, R, W, C, C` |
| cfg3 | same | `R, C, C, C, P, C, C, C` |
| cfg4 | same | `C, W, C, R, P, W, W, W` |

cfg3 won mechanically: cfg1 failed the direct truncation criterion; among the
zero-length configurations cfg3 had the highest hand correctness, complete
schema, zero reasoning usage, and the only p95 below 30 seconds. Gemma was
measured directly for the first time but had no served response, so it cannot be
selected on answer quality.

## G4 — Fallback-policy repair

The old `_client_fallback_eligible()` treated rate limits, timeouts, network
failures, and provider errors alike. That policy is now replaced by an explicit
`fallback_eligible` classification:

1. A typed upstream provider error—HTTP 5xx or HTTP-200 embedded upstream error
   such as the observed `{"error":{"message":"Upstream error from Nvidia: Service temporarily overloaded","code":502}}`
   with no `choices`—may issue the other free model request.
2. HTTP 429 and `Retry-After`/`X-RateLimit-*` signals are account-rate-limit
   outcomes. The client waits and retries the same model; it never fires a
   model fallback for that class.
3. Timeout, network, authentication, malformed-response, invalid-request, and
   `finish_reason=length` outcomes do not switch models.
4. `RequestRateGovernor` is process-global, enforces a 3.1-second minimum
   interval (strictly under 20 RPM), and counts every primary, fallback, and
   retry POST. `DailyRequestLedger` counts every dispatched POST regardless of
   HTTP outcome.

The offline focused provider slice passed **35 passed, 1 warning**. It uses the
exact 200/502 envelope, exact 429 + Retry-After shape, asserts same-model retry
and no fallback, asserts governor counts across fallback/retry, and refuses a
non-free fallback slug. Existing tests missed the policy question: they proved
that fallback could be called and that Retry-After could be slept, but never
asserted that a rate-limit must not trigger model fallback.

## G5 — Frozen 40-question re-run

The exact Gate 12-V sample was reused (`40` total, `36` answerable, `4`
unanswerable; question-ID SHA-256
`sha256:170d3201cf97f796732d8d462367d224033b08bdf45bc3cd4036c853dcd79c49`).
G5 issued 38 generation POSTs because two unanswerable rows were stopped by
guardrails before provider transport. Total Gate 16 accounting was 45 G3 plus
38 G5 = **83/200**.

| Metric | Gate 15-B B4 | Gate 16 G5 | Threshold / interpretation |
|---|---:|---:|---|
| First-attempt schema | 24/36 = 66.7% | 38/38 = 100.0% | pass >=90%; denominators are provider-attempted rows |
| Citation validity, all answerable rows | 40/40 = 100% | 36/36 = 100% | pass; 30/30 non-refusal also valid |
| Grounding precision | 13/49 = 26.5% | 15/51 = 29.4% | fail >=90% |
| Grounding recall | 13/37 = 35.1% | 15/37 = 40.5% | fail >=75% |
| Frozen token-F1 mean | 0.283374 | 0.353517 | diagnostic |
| Frozen answer correctness | 11/36 = 30.6% | 13/36 = 36.1% | fail >=70% |
| Corrected normalized F1 mean | 0.283374 | 0.353705 | diagnostic |
| Corrected binary correctness | 11/36 = 30.6% | 13/36 = 36.1% | fail >=70% |
| Corrected containment mean | 0.578505 | 0.571149 | diagnostic only |
| Hand answer correctness | 20/36 = 55.6% | 26/36 = 72.2% | pass >=70% |
| Hand categories | 20/3/2/11 C/P/W/R | 26/0/4/6 C/P/W/R | refusal is separate from provider failure |
| Hand disagreement, frozen metric | 13/36 = 36.1% | 15/36 = 41.7% | metric remains a poor proxy |
| Hand disagreement, corrected metric | 13/36 = 36.1% | 15/36 = 41.7% | no binary change on this sample |
| Latency p50 | 35,495.694 ms | 11,624.887 ms | informational |
| Latency p95 | 122,820.192 ms | 30,508.479 ms | fail by 508.479 ms at <=30,000 |
| Finish length | 17/64 = 26.6% | 0/38 = 0% | pass <=5% |
| Raw embedded 502 | 2 | 0 | availability observation |
| Raw 429 | 16 fallback 429s | 0 | availability observation |
| Fallback requests | 16 | 0 | no G5 error needed fallback |
| Fallback requests rate-limited | 16 | 0 | policy was not asked to recover in G5 |
| Actual Gemma served | 0 | 0 | Gemma remains unmeasured as a served answerer |
| Actual Nemotron served | 46 | 38 | healthy G5 pool |
| `max_tokens` present/value | 64/64 = 2048 | 38/38 = 8192 | direct G1 wire test |
| Reasoning tokens p95 | 2,451 | 0 | direct G2 observation |

All 36 answerable rows received final citation-valid responses or safe
refusals. Six answerable rows refused for evidence/guardrail reasons; zero
refusals were caused by provider unavailability. All four unanswerable rows
were refused correctly (two before transport and two by a served Nemotron
response stating that the requested information was not in context). There
were no provider-availability refusals in G5.

The G5 hand-adjudication ledger is:

| Question IDs | Label | Reason |
|---|---|---|
| `dev_q002`, `dev_q003`, `dev_q006`, `dev_q008`, `dev_q012`, `dev_q014` | correct | Exact requested policy facts, with harmless extra detail. |
| `dev_q016`, `dev_q017`, `dev_q018`, `gold_academic_schedule_007` | refused | Answerable rows refused despite retrieved/evaluable context. |
| `gold_credit_requirement_001` | correct | Requested title appears exactly; extra header detail is not contradictory. |
| `gold_credit_requirement_023` | wrong | Answers general program information, not the requested English-course table. |
| `gold_credit_requirement_058`, `gold_credit_requirement_096` | correct | Requested phrase/rule is reproduced accurately. |
| `gold_credit_requirement_085` | refused | Answerable row refused. |
| `gold_curriculum_structure_006` | refused | Answerable row refused. |
| `gold_curriculum_structure_011` | correct | Substantive content from the requested program document is accurate. |
| `gold_curriculum_structure_013` | wrong | Gives general programme-structure material, not the requested training-objective section. |
| `gold_curriculum_structure_020`, `gold_curriculum_structure_049` | correct | Requested programme title/content is accurately stated. |
| `gold_manual_002`, `gold_manual_003` | correct | Correct procedure and correct preference for the newer 2021 rule. |
| `gold_policy_exception_012`, `gold_student_account_001` | correct | Accurate content from the named student-support/account documents. |
| `gold_training_regulation_052`, `067`, `068`, `070`, `071`, `104`, `153`, `197`, `222`, `237` | correct | Requested rule, heading, classification, or procedure is substantively answered. |
| `gold_training_regulation_163` | wrong | Confuses a prior course with a prerequisite and changes the pass/completion condition. |
| `gold_training_regulation_233` | wrong | Gives a different warning condition, not the requested b/c/d grounds. |

## G6 — Verdict and attribution

The unchanged Gate 12-V thresholds produce **NO-GO** for the OpenRouter product
lane: grounding precision, grounding recall, frozen automated correctness, and
p95 latency still fail. Hand correctness passes, schema passes, truncation is
fixed, and G5 had no provider errors, but those improvements do not waive the
failed registered thresholds.

Attribution is deliberately split:

- The zero length-finish rate and the `8192` value on every G5 POST are directly
  attributable to the output-budget resize; B4's 2048 boundary regression is
  gone.
- G3 cfg2 versus cfg3 supports the reasoning-control attribution: cfg3 reduced
  observed reasoning to zero and p95 latency from 39,294ms to 26,292ms on the
  probe without a hand-quality loss. G5's p95 was 30,508ms, so the 30-second
  latency bar was narrowly missed; the small probe does not establish a stable
  latency guarantee.
- No answer-quality gain is attributable to model fallback in G5: no fallback
  was needed, and Gemma served zero. G3 did exercise the policy boundary: 429s
  stayed on the same model; the two cfg2 upstream 502s attempted Gemma, whose
  requests were rate-limited.
- The G5 pool was healthier than B4 (`0` versus `2` embedded 502 and `0` versus
  `16` 429). The hand-quality and latency deltas are therefore confounded by
  provider availability variance. They cannot be credited solely to reasoning
  control or the resized cap.
- Retrieval was held at ONNX E5-small int8, hybrid RRF `k=60`, top_k=10. No
  retrieval or dataset change is credited to the generation delta.

Because the frozen automated correctness remains below 0.70, the hand gap
decomposes as **6 refusals**, **4 wrong**, **0 partial**, and **0 typed
truncated** answerable rows. The largest remaining product contributor is
evidence/guardrail refusal (`6/36`); separately, the largest measurement
contributor is metric disagreement: 14 hand-correct rows are below the frozen
0.45 token-F1 threshold while one wrong row is above it.

The critical-path blocker remains **RISK-0026**: even a future GO cannot deploy
until the owner approves the least-privilege
`roles/iam.serviceAccountTokenCreator` grant on
`vietragops-web-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com`.
This gate did not and must not resolve that IAM decision.

Still unmeasured: multi-turn behavior, concurrency, cloud mode, MCP, the agent
path, authenticated API access, the `88 -> 110` retrieval-ranking gap, and the
exhaustiveness of `relevant_chunk_ids` (RISK-0040).

## Decisions and risks

- `DEC-0041` records the measured generation candidate: Nemotron free primary,
  `reasoning.effort=none`, `max_tokens=8192`. It is not deployment approval.
- `DEC-0042` records the fallback policy: model fallback does not rescue account
  rate limits; only upstream provider errors may switch models.
- `RISK-0030` is updated as partially mitigated: wire propagation is proven and
  8192/effort-none removed the observed truncation, but the lane remains NO-GO.
- A new truncation-regression risk records the lesson that the B1 repair created
  a new defect by ignoring the already-observed completion distribution.
- RISK-0033 is updated: policy distinction and accounting are offline-proven;
  live G5 did not need fallback, and Gemma remains unserved.
- RISK-0039 is updated with the fresh 15/36 metric disagreement and remains open.

## Closure boundaries

The research lane, golden QA fields, corpus, manifest, chunk store, retrieval
settings, and `.env` were not modified. Raw provider artifacts remain outside
the tracked tree. No deployment or push occurred.

