# Gate 12-V — Live validation of the OpenRouter product lane

**Date:** 2026-09-08
**Working directory:** `D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps`
**Verdict:** **NO-GO** — do not deploy the OpenRouter lane

## 1. Decision summary

The frozen thresholds produce NO-GO mechanically. OpenRouter passed safe
unanswerable refusal, final citation validity, and `must_cite` compliance, but
failed first-attempt schema validity, citation grounding, answer correctness,
answer token-F1, and the product-path p95 latency cap. Its configured Gemma
fallback was not observed as an actual serving model: 26 raw responses had
Nemotron model metadata and 32 HTTP-200 error envelopes had no actual serving
model metadata.

No production source, dependency, `.env`, GCP resource, deployment, or research
lane was changed. OpenRouter paid spend was zero. DEC-0034 records the decision.

## 2. Freeze and scope

- Protocol: `gates/baselines/GATE_12V_PROTOCOL.json`
- Protocol SHA-256: `sha256:f6c2993b9f437095e7d65a69bac9997a66a515f1ec8cee25f557b3f81b3344f9`
- Protocol freeze commit: `1b7d88cee5078db64802e0278127da489b4ab85e`
- V0 HEAD and `origin/main`: `a6d50cb1a2349d8820de904dcc9ac842f2dc8d47`
- Product QA: `evals/datasets/golden_qa.jsonl`, 120 records, SHA-256
  `71f66f3fd39143f2f918d654306918fcf92424e3b51fb008446dd03fe2152ab4`
- Corpus: 37 manifest documents; `data/chunks/chunks_500.jsonl`, 695 chunks,
  SHA-256 `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`

`golden_qa.jsonl` is the product evaluation set over the real 37-document
academic-policy corpus. It is distinct from the Gate 07/08 research corpus:
those gates use `research/gate07/dataset/generator.py build_v4_cases` and their
own frozen research manifests/protocols. No research runner, protocol,
baseline, metric, or dataset was invoked or modified here.

## 3. V0 entry receipts

- Git status at V0: exactly 25 pre-existing paths; index empty. The overlay was
  not staged. The first artifact-directory attempt later stopped before a
  provider request on the known Windows `WinError 5`; one bounded escalated
  retry created only the ignored evidence directory.
- Baseline command: `.venv\Scripts\python.exe -m pytest -q --basetemp=<external dir>`
- Baseline result: **591 passed, 3 warnings** in **456.01s**. The warnings were
  the existing websockets deprecations and `.pytest_cache` ACL warning.
- Count-only `.env` presence checks: `OPENROUTER_API_KEY=1`,
  `OPENROUTER_MODEL=1`, `OPENROUTER_MODEL_FALLBACK=1`, `GROQ_API_KEY=1`.
  No value was printed or recorded.
- OpenRouter credit preflight: `GET /api/v1/key` HTTP 200,
  `limit_remaining=0.2`, `usage=0`, `usage_daily=0`; no key value recorded.
- New per-process OpenRouter ledger before generation: used `0`, reserved `0`,
  remaining `1000` for UTC day `2026-09-08`. The adapter ledger is not durable
  across processes; the account-level credit receipt above is the separate
  preflight evidence.
- Local retrieval smoke: `HybridRetriever` over `chunks_500.jsonl`, query
  `Điều kiện tốt nghiệp là gì?`, top-5 returned 5 hits; first hit was
  `ug_graduation_conditions_s001_c001`.

## 4. V1 harness and product contract

The new gate runner reused the real product route function
`app.api.routes_query.ask`, with `AskRequest(question, top_k=5, debug=true,
use_guardrail=true)`. The path was:

`routes_query.ask -> get_answer_generator -> ContextBuilder -> HybridRetriever -> GuardrailEngine -> PromptBuilder -> ProviderRouter -> AnswerGenerator -> CitationVerifier/evidence_state`.

The existing offline evaluation harness was not sufficient because it uses
`validation_qa.jsonl`, does not issue provider calls, and does not retain raw
responses, first-attempt schema state, usage, finish reason, serving-model
metadata, or typed provider errors. Gate-owned additions were limited to:

- `evals/gate12v_runner.py`
- `evals/metrics/gate12v_metrics.py`

The measured contract rules were unchanged:

- `CitationVerifier`: refusal is valid; otherwise every citation chunk must be
  retrieved, quoted evidence is required, and normalized quoted evidence must
  occur in the retrieved chunk text.
- `GuardrailEngine`: refuses private-data patterns, citation failures at or
  above two, or insufficient context/support/lexical/bigram scores. `/ask`
  rejects requests that disable guardrails.

## 5. V2 frozen sample and policy

The fixed seed was `20260908`. Sampling used only `category`, `difficulty`, and
`is_answerable`; all 4/4 unanswerable records were included. `expected_answer`
was not loaded until both provider runs completed.

Frozen question IDs:

```text
dev_q002, dev_q003, dev_q006, dev_q008, dev_q012, dev_q014, dev_q016,
dev_q017, dev_q018, dev_q019, dev_q020, gold_academic_schedule_007,
gold_credit_requirement_001, gold_credit_requirement_023,
gold_credit_requirement_058, gold_credit_requirement_085,
gold_credit_requirement_096, gold_curriculum_structure_006,
gold_curriculum_structure_011, gold_curriculum_structure_013,
gold_curriculum_structure_020, gold_curriculum_structure_049, gold_manual_002,
gold_manual_003, gold_manual_004, gold_manual_005, gold_policy_exception_012,
gold_student_account_001, gold_training_regulation_052,
gold_training_regulation_067, gold_training_regulation_068,
gold_training_regulation_070, gold_training_regulation_071,
gold_training_regulation_104, gold_training_regulation_153,
gold_training_regulation_163, gold_training_regulation_197,
gold_training_regulation_222, gold_training_regulation_233,
gold_training_regulation_237
```

Retry and budget policy was frozen as follows: zero runner-level question
retries; one transport retry in each client; unchanged product citation retry
behavior; later retries never count as first-attempt success; maximum 200 total
generation POSTs; OpenRouter minimum inter-POST interval 3.1 seconds.

The numerical GO thresholds were:

| Metric | Frozen requirement |
| --- | ---: |
| First-attempt schema validity | >= 0.90 |
| Citation validity | >= 0.90 |
| Citation-grounding precision | >= 0.90 |
| Citation-grounding recall | >= 0.75 |
| False-answer rate on unanswerable | <= 0.05 |
| `must_cite` compliance | >= 0.90 |
| Answer correctness (`token_f1 >= 0.45`) | >= 0.70 |
| Mean answer token-F1 | >= 0.45 |
| End-to-end p95 latency | <= 30,000 ms |
| `finish_reason=length` rate | <= 0.05 |
| OpenRouter Gemma fallback activation | <= 0.50 |
| OpenRouter quality gap vs Groq | no lower than -0.10 |

## 6. V3/V4 run accounting

| Run | Questions | Generation POSTs | Raw artifact |
| --- | ---: | ---: | --- |
| Groq control, development mode | 40/40 | 108 | `gates/artifacts/gate12v/groq/raw_responses.jsonl` |
| OpenRouter, development mode | 40/40 | 58 | `gates/artifacts/gate12v/openrouter/raw_responses.jsonl` |
| Total | 80 question executions | **166/200** | ignored by `gates/artifacts/.gitignore` |

OpenRouter’s final per-process ledger was used `58`, remaining `942`. The run
receipt reports 10.384 seconds of pacing sleep; responses were generally slower
than the 3.1-second minimum interval. Paid spend was **0**.

Evidence hashes:

```text
groq/raw_responses.jsonl       a54efd9ea807a6c5350a01374d8e8b01d99f63ab252ffc0e17b057f635637605
groq/records.jsonl             c6334f5911ca7ac307a7b2575a61698871b422236c26a11abe32e6918dd2d9e4
groq/run_receipt.json          5aa235fbff0d3f5127dade8d8b34ddba8285c56b1857aa08e35e5443661d3f2c
openrouter/raw_responses.jsonl 1a32f496b08d29e056fad62323d0339ac0723290180a0fea35cc10286659b48a
openrouter/records.jsonl       7870301d1e5ba388903868f368bcc48d846a881e8c8b98adab511d3064ff7343
openrouter/run_receipt.json    eb6746b0be66cd12bfba2d1eaad12857d64470f1427bd2e2ec3905dff7d346eb
metrics_report.json            4a4067cfa42da8c3db6cf4f0c576a64af5948801affdc563f1b068b7ee2938ec
```

The Groq control itself was degraded: 2 raw Groq responses succeeded, 67 raw
calls were rate-limited, and 38 raw calls were other provider/JSON errors. The
final product trace reported `groq` for 2 questions, `ollama` fallback metadata
for 36, and no provider trace for 2 guardrail/no-provider cases. This is a
product-path control result, not a healthy standalone-Groq benchmark.

## 7. V5 metrics

Percentages below include numerator/denominator and Wilson 95% intervals. The
answer-token-F1 row is a distribution mean over 36 answerable rows, not a rate.

| Metric | Groq control | OpenRouter | Frozen decision |
| --- | --- | --- | --- |
| First-attempt schema validity | 2/38 = 5.3% [1.5%, 17.3%] | 18/38 = 47.4% [32.5%, 62.7%] | **FAIL** OpenRouter <90% |
| Citation validity, all rows | 40/40 = 100.0% [91.2%, 100%] | 40/40 = 100.0% [91.2%, 100%] | Pass |
| Citation validity, non-refusal | 15/15 = 100.0% [79.6%, 100%] | 24/24 = 100.0% [86.2%, 100%] | Informational |
| Citation-grounding precision | 8/29 = 27.6% [14.7%, 45.7%] | 11/46 = 23.9% [13.9%, 37.9%] | **FAIL** OpenRouter <90% |
| Citation-grounding recall | 8/37 = 21.6% [11.4%, 37.2%] | 11/37 = 29.7% [17.5%, 45.8%] | **FAIL** OpenRouter <75% |
| Refusal correctness | 19/40 = 47.5% [32.9%, 62.5%] | 28/40 = 70.0% [54.6%, 81.9%] | Informational |
| False-answer rate, unanswerable | 0/4 = 0.0% [0%, 49.0%] | 0/4 = 0.0% [0%, 49.0%] | Pass <=5%; CI is wide at n=4 |
| `must_cite` compliance | 36/36 = 100.0% [90.4%, 100%] | 36/36 = 100.0% [90.4%, 100%] | Pass |
| Answer correctness | 2/36 = 5.6% [1.5%, 18.1%] | 7/36 = 19.4% [9.8%, 35.0%] | **FAIL** OpenRouter <70% |
| Mean answer token-F1 | 0.103078, n=36 | 0.223210, n=36 | **FAIL** OpenRouter <0.45 |
| End-to-end latency p50 / p95 | 44,869.683 / 90,189.468 ms | 23,262.021 / 90,590.011 ms | **FAIL** OpenRouter p95 >30,000 ms |
| `finish_reason=length` | 0/108 = 0.0% | 0/58 = 0.0% | Pass <=5% |
| Gemma fallback activation | N/A (Groq control) | 0/38 = 0.0%; Gemma actual served = 0 | Numerically below cap, but fallback unobserved |

Quality gaps, OpenRouter minus Groq, were: schema +42.1 points; citation
validity 0.0; grounding precision -3.7; grounding recall +8.1; refusal
correctness +22.5; `must_cite` 0.0; answer correctness +13.9; token-F1
+0.120132. The parity guard passed, but the individual OpenRouter thresholds
did not.

### Token behavior and errors

| Observation | Groq control | OpenRouter |
| --- | --- | --- |
| Reasoning tokens | 2 observed / 106 missing; p50 1,346; p95 1,346 | 26 observed / 32 missing; p50 711; p95 2,382 |
| Completion tokens | 2 observed / 106 missing; p50 1,419; p95 1,419 | 26 observed / 32 missing; p50 1,151; p95 5,407 |
| Completion values >1024 | 2/2 observed | 16/26 observed |
| Raw error taxonomy | 67 `rate_limited`; 38 `provider_error` (including JSON errors) | 32 `provider_error`, all HTTP-200 `code=502` overload envelopes |
| Per-POST latency artifact | 106 observed / 2 missing | 0 observed / 58 missing; successful-response end timestamps were not retained |

The product payload inspection found `max_tokens_present=false` in all 108
Groq and all 58 OpenRouter generation requests. This is recorded as RISK-0030;
the gate did not repair it. The 1024 comparison therefore measures the shipped
wire behavior, not a claimed enforced cap.

### Actual serving-model breakdown

Serving-model attribution uses only response `model` metadata. A provider error
body with no `model` is `unserved`, not Nemotron or Gemma.

| Actual serving class | Questions | Provider-attempted | Schema first attempt | Answer correctness | Mean token-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nemotron | 26 | 26 | 18/26 = 69.2% | 6/25 = 24.0% | 0.243985, n=25 |
| Gemma | 0 | 0 | N/A | N/A | N/A |
| Unserved: provider error | 12 | 12 | 0/12 = 0% | 1/11 = 9.1% | 0.175993, n=11 |
| Unserved: guardrail before provider | 2 | 0 | N/A | N/A | N/A |

The configured `models=[Nemotron, Gemma]` array was transmitted, but no raw
response proved that Gemma served. The headline OpenRouter result is therefore
Nemotron-plus-unserved/error behavior, not a measured Nemotron-versus-Gemma
fallback system.

## 8. V6 failure and regression analysis

At question level, 20 OpenRouter cases had provider-caused upstream-502
evidence; those cases contained 32 raw HTTP-200 error envelopes. Seven cases
were classified as retrieval misses affecting both providers. No OpenRouter
case was classified as `finish=length`, hallucinated citation, or false answer
on an unanswerable row.

The eight answer-quality regressions where OpenRouter token-F1 was below Groq
were classified before the verdict:

| Question | Cause | OpenRouter F1 | Groq F1 |
| --- | --- | ---: | ---: |
| `gold_curriculum_structure_006` | prompt-contract mismatch | 0.213 | 0.285 |
| `gold_curriculum_structure_011` | upstream 502 | 0.057 | 0.095 |
| `gold_curriculum_structure_013` | retrieval miss affecting both | 0.000 | 0.055 |
| `gold_curriculum_structure_020` | upstream 502 | 0.000 | 0.274 |
| `gold_curriculum_structure_049` | upstream 502 | 0.143 | 0.217 |
| `gold_training_regulation_070` | upstream 502 | 0.236 | 0.451 |
| `gold_training_regulation_197` | wrong refusal | 0.000 | 0.130 |
| `gold_training_regulation_237` | wrong refusal | 0.000 | 0.142 |

Concrete verbatim examples:

1. `dev_q002` — OpenRouter raw failure: `{"message":"Upstream error from Nvidia: Service temporarily overloaded","code":502}`. The final product response was `refusal=true`; this is provider-caused overload, not evidence that retrieval failed.
2. `dev_q003` — OpenRouter answer: `Cấu trúc email sinh viên TDTU là MSSV@student.tdtu.edu.vn.` The Groq control final answer was empty with `refusal=true` after its rate-limit/fallback chain.
3. `dev_q006` — OpenRouter answer: `Học kỳ Hè kéo dài 9 tuần (bao gồm 7 tuần thực học và 2 tuần thi tập trung).` The Groq control instead began: `Theo ngữ cảnh đã truy xuất, 1. Kế hoạch giảng dạy và học tập chi tiết hóa việc tổ chức thực hiện...`; this is a product-output difference, not a provider error on the OpenRouter response.
4. `gold_curriculum_structure_013` — both providers missed the relevant chunk set. OpenRouter returned an empty answer with `refusal=true`; retrieved IDs began `ug_training_reg_k2021_html_s017_c001`, `ug_training_reg_k2021_pdf_s003_c001`, while the relevant product chunk was not retrieved. This is a retriever-caused shared miss.

## 9. V7 verdict and boundaries

Applying the frozen thresholds produces **NO-GO**. The lane must not be
deployed. This is not a judgment that a paid or differently configured model
could never work; it is the result for the shipped free product path under the
frozen run.

This gate did not measure multi-turn behavior, concurrency, cost at scale,
agent/tool behavior, MCP, Cloud Run/cloud-mode behavior, authenticated API
access, deployment readiness, or the full 120-question set. RISK-0026 remains
open; no Cloud Run or GCP call was made. Gate 09 and Gate 10 were not started.

Recommended next gate: a separately authorized **Gate 12-V-R** should make the
smallest production-source changes needed for the token budget, OpenRouter
citation retry, and serving/fallback observability, then create a new committed
protocol and collect fresh paired evidence. It must not rescore this run.

## 10. V8 closure artifacts

- Tracked result: `gates/results/GATE_12V_RESULT.md`
- Decision: `DEC-0034` in `_agent_ops/DECISION_LOG.md`
- Risk updates: `RISK-0028`/`RISK-0029` addenda and `RISK-0030`/`RISK-0031` in
  `_agent_ops/RISK_REGISTER.md`
- Implementation log: dated Gate 12-V entry in
  `_agent_ops/IMPLEMENTATION_LOG.md`
- Ignored raw/run/metrics artifacts: `gates/artifacts/gate12v/`

Final unchanged-suite receipt after the gate-owned runner/metrics and records:
`.venv\Scripts\python.exe -m pytest -q --basetemp=<external dir>` returned
**591 passed, 3 warnings** in **658.03s**. Production behavior remained
unchanged.

## Addendum — Gate 15 B0 metric-validity audit (2026-09-10)

This addendum preserves the original Gate 12-V result and does not rescore or
rewrite its frozen run. The full audit is recorded in
`gates/results/GATE_15B_RESULT.md`, under Gate 15 protocol SHA-256
`6feb4d7cbd5bf38b44adde252bda9adc8075dcfd3efef51cd4c0e839c5f20c0e`.

The exact `token_f1` implementation is multiset F1 over NFKC-normalized,
whitespace-collapsed, casefolded Unicode `\w+` tokens. Vietnamese diacritics
are retained and numeric zero-padding is not normalized. On the 36 answerable
OpenRouter rows, 28 contain a number in the answer or expectation; `07` vs `7`
and `02` vs `2` score `0.0` under the frozen metric. Ten answers begin with
`Theo ngữ cảnh đã truy xuất,`; stripping that model-generated prefix improves
their mean F1 by `0.006638`. Among 24 non-empty answers, answer length and F1
have Pearson correlation `-0.686026`.

Hand adjudication of all 36 rows gives `18/36` correct, `2/36` partial, `4/36`
wrong, and `12/36` refused. The frozen automated threshold gives `7/36 =
19.4%`; all seven are human-correct, but it misses 11 human-correct answers.
Disagreement is `11/36 = 30.6%` (zero false positives). The corrected,
human-validated OpenRouter correctness is therefore `18/36 = 50.0%` (Wilson
95% `0.344741–0.655259`) versus the original `19.4%` (Wilson
`0.097530–0.350284`). This is a measurement correction, not a change to the
dataset or the original Gate 12-V decision.

The proposed automated follow-up metric canonicalizes digit runs and strips
the observed prefix, then reports symmetric normalized F1 alongside
expected-token containment recall. Containment is not accepted as ground truth
yet because it overcredits verbose wrong answers; human adjudication remains
the validation target. Gate 15 B0 therefore pauses before B4 and asks the owner
to resolve the threshold/generation-quality decision.

## Addendum — Gate 17 grounding audit (2026-09-10)

This addendum preserves the frozen Gate 12-V run and does not edit its original
all-40/all-36 metric values. Gate 17 audited the later Gate 16 G5 artifact,
which reused the same 40-question sample, because RISK-0040 made annotation
membership an unverified proxy for answer-supporting evidence.

On the 26 hand-correct Gate 16 answers, 31 of 32 cited IDs absent from
`relevant_chunk_ids` nevertheless had chunk text supporting the answer; one was
a genuine grounding failure. The corrected audited-surface counts are
`46/47 = 97.9%` precision and `46/58 = 79.3%` recall. These counts are scoped
to the audited 26-row surface and must not be substituted into this result's
frozen Gate 12-V tables without a new, full-sample protocol.

The original Gate 12-V NO-GO remains the historical mechanical verdict for its
frozen annotation-bound run. Gate 17 records a conditional corrected
measurement conclusion only; it changes no threshold, golden field, corpus,
retrieval setting, provider configuration, or deployment state.
