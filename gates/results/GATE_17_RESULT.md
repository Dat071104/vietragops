# Gate 17 — Audit the last two metrics (zero provider calls)

**Status:** CONDITIONAL-GO for the corrected, hand-audited measurement surface;
deployment remains blocked. The original Gate 12-V mechanical result remains
NO-GO when its frozen all-36 annotation-bound metrics are left unchanged.

This gate read the existing Gate 16 G5 artifact only. It made zero provider
calls, zero GCP calls, no deployment, no secret access, and no change to
production source, retrieval, generation, prompts, corpus, manifest, chunk
store, golden data, or thresholds.

## Protocol and entry receipts

| Item | Receipt |
|---|---|
| Gate 17 protocol | `gates/baselines/GATE_17_PROTOCOL.json`, commit `1f4c695a7e16869eb11d7814f96eca9a2046bedd` |
| Protocol SHA-256 | `sha256:0a0eb13e5334c8ff6c1327171c3846e94041a29cde118b7235d6194e2a7b1c2f` |
| Entry HEAD | `9b47b20f69f6a2f696442e7355226363c75b1747` |
| Entry `origin/main` | `9b47b20f69f6a2f696442e7355226363c75b1747` |
| Pre-existing overlay | 25 paths, unstaged; index empty |
| Interpreter | `.venv\Scripts\python.exe` |
| Suite command | `.venv\Scripts\python.exe -m pytest --basetemp D:\GRADUATION_THESIS\gate17_pytest_basetemp_05f3767841cc45c4821e0454c7fba1f5` |
| Suite receipt | `607 passed, 3 warnings` in `334.04s` |
| Gate 16 G5 artifact | `C:/Users/ADMIN/AppData/Local/Temp/vietragops-gate16-g5-20260910/cfg3.json` |
| Gate 16 G5 artifact SHA-256 | `sha256:c6739dee88cf27c16f14368cb3302de0bd221e184a5e272bcb9d2125a9ff7193` |

The three warnings are the two known `websockets` deprecations and the known
host `.pytest_cache` ACL warning (`WinError 5`). The pytest basetemp was
external to the Git root; the cache warning was not converted into a test
failure.

## A1 — Grounding precision audit

### Exact implementation

The implementation is `evals/metrics/gate12v_metrics.py:137-147`:

```python
relevant = {str(value) for value in row.get("relevant_chunk_ids", [])}
cited = {str(citation.get("chunk_id"))
         for citation in _citations(row) if citation.get("chunk_id")}
grounding_precision_numerator += len(cited & relevant)
grounding_precision_denominator += len(cited)
grounding_recall_numerator += len(cited & relevant)
grounding_recall_denominator += len(relevant)
```

Therefore:

- the numerator for both metrics is the number of cited chunk IDs that are in
  `relevant_chunk_ids`;
- the precision denominator is the sum of unique cited IDs per answerable row;
- the recall denominator is the sum of `relevant_chunk_ids` per answerable row;
- uniqueness is per row, not global across the sample;
- neither chunk text nor `quoted_evidence` is read by this metric;
- every row marked `is_answerable=true` enters the grounding loop, including a
  product response later marked as a refusal.

The frozen Gate 16 all-36 result was `15/51 = 29.4%` precision and
`15/37 = 40.5%` recall. On the 26 hand-correct rows alone, the same membership
rule gives `15/47 = 31.9%` precision and `15/27 = 55.6%` recall.

### Hand audit of the 26 hand-correct rows

`OUT/SUPPORT` means the ID is absent from the annotation but the stored chunk
text supports at least one material claim in the answer. `OUT/FAIL` means the
chunk is topically related but does not support the answer's material claim.
`IN` records annotation membership; the 15 annotated hits were retained as
grounded for this correction.

| Question ID | Cited chunk IDs and audit status |
|---|---|
| `dev_q002` | `ug_student_notes_s001_c002` (OUT/SUPPORT); `ug_student_portal_guide_s001_c001` (IN) |
| `dev_q003` | `ug_student_email_guide_s001_c001` (IN); `ug_student_notes_s001_c003` (OUT/SUPPORT); `ug_student_notes_s001_c002` (OUT/SUPPORT) |
| `dev_q006` | `ug_academic_year_plan_guide_s001_c001` (IN) |
| `dev_q008` | `ug_study_plan_registration_guide_s001_c001` (OUT/SUPPORT); `ug_study_plan_registration_guide_s001_c002` (IN) |
| `dev_q012` | `ug_course_registration_guide_s001_c001` (OUT/SUPPORT); `ug_course_registration_guide_s001_c002` (IN) |
| `dev_q014` | `ug_training_reg_k2021_html_s032_c001` (OUT/SUPPORT); `ug_moet_undergrad_regulation_s025_c001` (OUT/SUPPORT); `ug_training_reg_k2021_pdf_s038_c001` (IN) |
| `gold_credit_requirement_001` | `admission_handbook_2025_s077_c003` (OUT/SUPPORT) |
| `gold_credit_requirement_058` | `admission_handbook_2025_s041_c001` (OUT/SUPPORT); `admission_handbook_2025_s043_c001` (OUT/SUPPORT); `admission_handbook_2025_s042_c001` (OUT/SUPPORT) |
| `gold_credit_requirement_096` | `admission_handbook_2025_s070_c001` (IN) |
| `gold_curriculum_structure_011` | `it_cs_program_overview_s001_c004` (OUT/SUPPORT) |
| `gold_curriculum_structure_020` | `it_cs_elo_2015_s001_c002` (OUT/SUPPORT); `it_cs_elo_2015_s001_c004` (OUT/SUPPORT); `it_cs_elo_2015_s001_c005` (OUT/SUPPORT); `it_cs_elo_2015_s001_c007` (OUT/SUPPORT) |
| `gold_curriculum_structure_049` | `it_cs_curriculum_2015_s001_c021` (OUT/SUPPORT); `it_cs_curriculum_2015_s001_c010` (OUT/SUPPORT) |
| `gold_manual_002` | `ug_study_plan_registration_guide_s001_c001` (OUT/SUPPORT) |
| `gold_manual_003` | `ug_training_reg_k2021_html_s009_c001` (OUT/FAIL); `ug_training_reg_k2021_pdf_s016_c001` (IN) |
| `gold_policy_exception_012` | `ug_student_support_s001_c003` (OUT/SUPPORT); `ug_student_support_s001_c001` (OUT/SUPPORT) |
| `gold_student_account_001` | `ug_student_portal_guide_s001_c001` (IN) |
| `gold_training_regulation_052` | `ug_training_reg_k2020_html_s038_c001` (OUT/SUPPORT) |
| `gold_training_regulation_067` | `ug_training_reg_k2020_html_s019_c001` (IN); `ug_training_reg_k2020_pdf_s023_c001` (OUT/SUPPORT) |
| `gold_training_regulation_068` | `ug_training_reg_k2020_html_s020_c001` (IN); `ug_training_reg_k2020_pdf_s023_c001` (OUT/SUPPORT) |
| `gold_training_regulation_070` | `ug_training_reg_k2021_html_s018_c001` (OUT/SUPPORT) |
| `gold_training_regulation_071` | `ug_training_reg_k2020_html_s023_c001` (IN); `ug_training_reg_k2021_pdf_s028_c001` (OUT/SUPPORT); `ug_training_reg_k2021_html_s019_c001` (OUT/SUPPORT) |
| `gold_training_regulation_104` | `ug_training_reg_k2021_html_s006_c001` (OUT/SUPPORT); `ug_training_reg_k2021_html_s006_c003` (OUT/SUPPORT) |
| `gold_training_regulation_153` | `ug_training_reg_k2020_html_s005_c001` (OUT/SUPPORT); `ug_training_reg_k2021_html_s007_c001` (OUT/SUPPORT) |
| `gold_training_regulation_197` | `ug_training_reg_k2020_pdf_s036_c001` (IN) |
| `gold_training_regulation_222` | `ug_training_reg_k2021_pdf_s013_c001` (IN) |
| `gold_training_regulation_237` | `ug_training_reg_k2021_pdf_s025_c001` (IN) |

The raw audit counts are:

| Count | Raw value |
|---|---:|
| Hand-correct answers | 26 |
| Unique cited IDs, summed per row | 47 |
| Cited IDs in `relevant_chunk_ids` | 15 |
| Cited IDs outside `relevant_chunk_ids` | 32 |
| Outside IDs that support the answer | 31 |
| Outside IDs that are genuine grounding failures | 1 |
| Correct answers with at least one outside citation | 20/26 |
| Correct answers with no outside citation | 6/26 |

For the corrected reference on this audited surface, the 27 annotated relevant
IDs are unioned with the 31 manually confirmed unannotated supporting IDs. The
corrected counts are therefore:

- precision: `46/47 = 97.8723%` (Wilson 95%: `88.8868%–99.6234%`);
- recall: `46/58 = 79.3103%` (Wilson 95%: `67.2305%–87.7486%`).

This is a 26-row audited-surface correction, not an invented all-36 rescore.
The ten non-correct rows were not used to claim an extrapolated corrected
grounding rate.

### Three concrete examples

1. **Annotation false negative, `dev_q002`.** The annotation lists only
   `ug_student_portal_guide_s001_c001`, but the cited
   `ug_student_notes_s001_c002` contains the password rule
   “TDTU + 4 số cuối CMND/căn cước” and the `TDTU0000` default. It directly
   supports the answer and is therefore a real annotation false negative.
2. **Annotation false negative, `gold_training_regulation_104`.** The answer
   lists mandatory, elective, equivalent/replacement, and parallel courses.
   The two outside chunks contain the corresponding headings “Môn học bắt
   buộc”, “Môn học ... tự chọn”, “Môn học thay thế, môn học tương đương”, and
   “Môn học song hành”. Both are supporting citations despite not being the
   single annotated ID.
3. **Genuine failure, `gold_manual_003`.** The outside
   `ug_training_reg_k2021_html_s009_c001` chunk discusses the 2021 maximum-load
   rule, but it does not support the answer's material version-preference claim
   that 2021 should be preferred over 2020 because it is newer. It is topical
   evidence, not evidence for that comparison. The in-set
   `ug_training_reg_k2021_pdf_s016_c001` citation remains the supporting one.

## A2 — Correctness-metric discrepancy

### Code path

The production scoring path imports `token_f1` in
`evals/metrics/gate12v_metrics.py:15` and calls it for every answerable row at
lines 171-174. `evals/metrics/generation_metrics.py:15-33` tokenizes with
`rag.retrieval.base.tokenize`, computes multiset overlap, and uses symmetric
precision/recall to form F1. The binary threshold is `token_f1 >= 0.45`.
`evals/gate12v_runner.py:995-1009` uses the same function for the persisted
provider comparison records before calling `compute_gate12v_metrics` at
lines 1043-1050.

Gate 15-B0's proposed correction (numeric-run canonicalization, removal of the
observed boilerplate prefix, and containment reporting) is not wired into that
production path. Gate 16 nevertheless applied the correction as a separate
offline diagnostic re-score of the existing G5 strings. It did not replace the
headline binary scorer. This is why the Gate 16 report contains both frozen and
corrected columns while the binary result is unchanged.

### Re-score and disagreement

| Measure | Frozen metric | Gate 15-B0 correction | Hand reference |
|---|---:|---:|---:|
| Mean symmetric token-F1 | `0.353517` | `0.353705` | not applicable |
| Mean expected-token containment | not reported | `0.571149` | not applicable |
| Binary correctness at `.45` | `13/36 = 36.1%` | `13/36 = 36.1%` | `26/36 = 72.2%` |

Only `gold_training_regulation_070` changes materially in the G5 binary
comparison: `0.243243 -> 0.250000`; it remains below `.45`. Numeric
normalization and prefix removal therefore do not resolve the binary gap.

Against the frozen hand labels, the corrected binary metric has:

- 14 false negatives (`14/36` hand-correct rows below `.45`);
- 1 false positive (`gold_training_regulation_163`, hand-wrong but above `.45`);
- 15 disagreements total: `15/36 = 41.7%`;
- the bias is **not** false-negative-only on G5. Gate 15-B0's zero-false-positive
  pattern did not repeat.

The remaining defect is mainly symmetric token-F1's verbosity/length penalty
and its inability to judge semantic correctness. Numeric padding is a small
factor, not the root cause. A metric that marks 14 human-correct answers as
wrong and one human-wrong answer as correct is not viable as the reference for
this corpus. Hand adjudication remains the reference; automated F1 and
containment are diagnostic until a separately validated semantic metric exists.

## A3 — Latency

The registered Gate 16 report includes all 40 end-to-end answer rows, while
38 rows made a provider POST. Both views are reported to avoid changing the
sample definition silently:

| Surface | n | min | p50 | p90 | p95 | p99 | max | mean (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All Gate 16 G5 answer rows | 40 | 756.264 | 11,624.887 | 18,004.007 | 30,508.479 | 34,978.698 | 37,275.189 | 12,931.286 |
| Provider-attempted rows | 38 | 5,538.242 | 11,641.421 | 18,004.007 | 30,508.479 | 34,978.698 | 37,275.189 | 13,563.089 |

Using the pre-registered 38-row bootstrap (`20,000` resamples,
`seed=20260910`, the registered floor-index p95), the observed p95 is
`30,508.479 ms` and the percentile 95% interval is
`16,672.136–37,275.189 ms`. The 30,000 ms bar lies inside that interval. The
three rows above the bar are `3/38 = 7.89%` (Wilson 95%:
`2.72%–20.80%`). The 508.479 ms miss is therefore **noise-compatible at n=38**,
not evidence that a tuning change is justified.

The named tail cause is slow provider response time, not a local test defect:

| Question ID | End-to-end | Provider POST | Local/context remainder |
|---|---:|---:|---:|
| `gold_training_regulation_070` | 37,275.189 ms | 31,533.960 ms | 5,741.229 ms |
| `gold_curriculum_structure_020` | 34,978.698 ms | 32,356.983 ms | 2,621.715 ms |
| `gold_policy_exception_012` | 30,508.479 ms | 28,154.800 ms | 2,353.679 ms |

No latency tuning was made or is recommended for this 508 ms observation.

## A4 — Threshold re-application and verdict

The Gate 12-V thresholds were not changed:

| Metric | Gate 17 corrected/audited value | Threshold | Result |
|---|---:|---:|---|
| Hand answer correctness | `26/36 = 72.2%` | `>=70%` | PASS |
| Grounding precision, audited 26-row surface | `46/47 = 97.9%` | `>=90%` | PASS |
| Grounding recall, audited 26-row surface | `46/58 = 79.3%` | `>=75%` | PASS |
| Automated correctness | `13/36 = 36.1%` | `>=70%` | Diagnostic fail; not a trusted reference |
| End-to-end p95 latency | `30,508.479 ms` nominal; noise-compatible by A3 | `<=30,000 ms` | CONDITIONAL under the frozen noise rule |

**Gate 17 verdict: CONDITIONAL-GO for the corrected, hand-audited measurement
surface; not a deployment GO.** The flip from Gate 16's measurement NO-GO is
caused by three explicit corrections: (1) treating hand adjudication as the
correctness reference, (2) replacing annotation-only grounding with the
hand-audited support set, and (3) treating the 508 ms p95 miss as
noise-compatible at `n=38`. No threshold, prompt, model, retrieval setting,
or production behavior was changed.

This must not be read as a full all-36 mechanical Gate 12-V pass. The corrected
grounding counts are explicitly scoped to the 26 rows audited here, and the
automated correctness metric remains invalid as a reference. Under the
original frozen all-36 mechanical columns, Gate 12-V remains NO-GO.

The deployment blocker is unchanged and independent of this measurement
verdict: **RISK-0026 remains open.** The owner must decide whether to approve
the least-privilege `roles/iam.serviceAccountTokenCreator` grant on
`vietragops-web-runtime@vietragops-evolve-20260831.iam.gserviceaccount.com`.
Nothing deploys until the owner makes that IAM decision.

## A5 — Closure boundary

- `gates/baselines/GATE_17_PROTOCOL.json` was committed before metric
  implementation analysis.
- The Gate 16 and Gate 12-V result files were not rewritten; addenda are
  appended separately where the corrected interpretation matters.
- No provider, GCP, deployment, secret, source, test, corpus, manifest, golden
  set, or chunk-store action occurred.
- The pre-existing 25-path overlay was not staged, reset, stashed, cleaned, or
  pushed.

See the appended Gate 16/Gate 12-V addenda and DEC-0043/RISK-0040 updates for
the durable cross-gate record.
