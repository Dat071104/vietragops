# Gate 08 Result — Cross-Version Alignment Method

Status: **NEGATIVE — the proposed method is not adopted. Gate 09 is not authorized.**

## Headline

The Gate 08 method was built, frozen, run, and ablated exactly as specified, and
it **does not beat the frozen Gate 07 baselines on any compared metric in any of
the three evaluated families**. On the two regions Gate 07 granted, the strongest
Gate 08 cell loses to the strongest frozen Gate 07 cell as follows:

| Family | Metric | Gate 08 best | Gate 07 frozen best | Delta |
|---|---|---|---|---|
| `argument_split` | Argument F1 | 0.6000 (`ablate_no_history` / 20b) | 0.6889 (`llm_old_new_history` / 120b) | **-0.0889** |
| `argument_split` | First-attempt | 0.5333 (`ablate_no_intent_abstraction`) | 0.7333 (`llm_old_new_history` / 120b) | **-0.2000** |
| `argument_split` | Tool@1 | 1.0000 (`ablate_no_history` / 20b) | 1.0000 (`lexical_name` / offline) | 0.0000 |
| `tool_replacement` | Argument F1 | 0.1333 (`gate08_method`) | 0.3867 (`llm_old_new_history` / 20b) | **-0.2533** |
| `tool_replacement` | First-attempt | 0.0000 (all arms) | 0.5333 (`llm_reasoning` / 20b) | **-0.5333** |
| `tool_replacement` | Tool@1 | 0.9333 (`ablate_schema_only` / 120b) | 1.0000 (`lexical_name` / offline) | -0.0667 |
| `no_equivalent` | No-equivalent accuracy | 0.8000 (`gate08_method` / 120b) | 1.0000 (every V4 LLM arm) | **-0.2000** |

False alignment rate is 0.0000 for the best cell on both sides in both claim
families, so the method is not trading accuracy for recklessness — it is simply
weaker.

This is a valid Gate 08. The gate exists to find out whether the proposed
mechanism is justified by the Gate-0 failure. It is not. Nothing was tuned after
seeing these numbers, and no case, family, arm, or metric was dropped.

## What Gate 07 authorized, and what this gate did with it

`gates/results/GATE_07_RESULT.md` closed with a **narrow V4.1 GO** for
`argument_split` and `tool_replacement` only, and named "a separately approved
follow-on research plan" as the sole allowed next step. The user approved that
plan on 2026-08-29 and authorized execution to the end of Gate 08.

The evaluation surface was therefore pre-registered, before any Gate 08 number
existed, as the 15 graded cases of each granted family plus the 15 graded
`no_equivalent` cases as an abstention and false-alignment safety control. The
control family carries no claim. Calibration used the 36 held-out cases Gate 07
never scored. No graded case was ever moved into calibration.

## The method

One principal mechanism, deliberately two-sided:

1. **Phase 8.1 — intent signature.** An LLM abstracts the *old* operation from
   its contract, its verified past calls, and the task description into a fixed
   vocabulary: operation, primary/target entity, preconditions, effects, one
   semantic concept per argument, and output semantics. A second, independent
   LLM call abstracts *each new candidate contract* the same way. **Neither call
   ever sees the other side.** Observed argument values and separators are
   attached deterministically from the traces, never transcribed by the model.
2. **Phase 8.2 — candidate retrieval.** Every candidate is scored against the old
   signature. Retrieval may return an empty set; it never forces a match, and
   ranking is by score then name, never by position.
3. **Phase 8.3 — correspondence scoring.** Five named dimensions — operation,
   entity, effect, precondition, output — with frozen weights summing to 1.
4. **Phase 8.4 — argument alignment.** Five ordered passes: exact concept match,
   declared part-of, declared components, a value the new contract states for
   itself, and finally a residual conservation-of-information pass that recovers
   an unannounced split or merge from the arithmetic of what is left over.
5. **Phase 8.5 — confidence and abstention.** `ALIGN` / `NO_EQUIVALENT` /
   `ABSTAIN`, from thresholds fitted only on the held-out split.
6. **Phase 8.6 — first adapted execution.** Exactly one call per case, through
   the unchanged Gate 07 executor, after the decision was already recorded.

The mechanism's claim to novelty over the Gate 07 baselines was the independent
two-sided abstraction: no single model call is ever shown an old tool and a new
tool together, so a correspondence has to be *computed* rather than *recalled*.
That is precisely the property the results below fail to reward.

## Freeze and preflight

- Protocol: `gates/baselines/GATE_08_PROTOCOL.json`, SHA-256
  `ee5bfadfb1fd863ba9ccfdb050df1eea282491c0b81739cc9efd854e8279a036`.
- Method interface digest
  `sha256:c4d6ae2941b76b241072e375fa50ec94f21c80e4fee9e01cd94a52284e9f8b0e`,
  pinned before collection and re-verified at every run.
- Freeze commits, all before any provider call: `cd311ac` (protocol and
  interface), `b02fa79` (surface correction), `0e2aab7` (prompt correction and
  refreeze). `c419bca` added the no-equivalent comparison and the reachability
  diagnostic after collection; it changes reporting, not collection.
- The Gate 08 surface is byte-identical to Gate 07 V4.1's. Both protocols record
  `graded_manifest_sha256`
  `sha256:435d91e1d5c97f1a484eee4f2934c7b97d328d4437a04d51970aec30b7c41983`,
  `held_out_manifest_sha256`
  `sha256:c8c39d23fe28b19ff73c12fe8c578554fc6b8918151fb25bfe4a2468208ed546`,
  and candidate-order oracle
  `sha256:bb8f18a1d8a84f3c25726bc87fa2cde863bb4cdaa57f7c4c2480b9d27a008265`
  under `candidate_order = v4_seeded_permutation`. A test asserts this equality.
- Preflight receipt for the headline run:

```json
{"candidate_order_oracle_sha256":"sha256:bb8f18a1d8a84f3c25726bc87fa2cde863bb4cdaa57f7c4c2480b9d27a008265","current_head":"b02fa7994b56e064a45cc32ba581f2f2c35fa165","dataset_digests":{"graded_manifest_sha256":"sha256:435d91e1d5c97f1a484eee4f2934c7b97d328d4437a04d51970aec30b7c41983","held_out_manifest_sha256":"sha256:c8c39d23fe28b19ff73c12fe8c578554fc6b8918151fb25bfe4a2468208ed546"},"method_interface_digest":"sha256:c4d6ae2941b76b241072e375fa50ec94f21c80e4fee9e01cd94a52284e9f8b0e","protocol_git_head_at_freeze":"cd311ac6c13f4901c1c2253fe9082e10b15bee0a","protocol_path":"gates/baselines/GATE_08_PROTOCOL.json","status":"passed"}
```

Two defects were caught and corrected **before** any provider call, and are
recorded here rather than quietly repaired:

1. The first surface was built from the unpermuted case generator. Its dataset
   digests did not match Gate 07 V4's, which would have compared the method
   against baselines that saw different candidate lists. Fixed in `b02fa79`.
2. The first prompt let the model return free-text sentences as output
   semantics, which are not comparable across two independent abstractions. Fixed
   in `0e2aab7`; the connectivity-probe artifacts collected under the old prompt
   were deleted, not reused.

## Collection receipts

- Models, pinned: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`.
  `ProviderRouter(mode="research")`, no fallback, `temperature=0`,
  `max_tokens=900`.
- 582 signature units (39 distinct new contracts plus 84 old-tool units across
  three old-side variants, per model). **563 collected, 19 not.** Four resume
  passes at the frozen parameters; passes 2-4 recovered 8, 2, and 0 keys, so the
  remaining 19 are stable failures, not transient ones.
- Every one of the 19 is `HTTP 400 json_validate_failed` with an empty
  `failed_generation`, all on `openai/gpt-oss-20b`, 17 of them on the
  `task_only` (schema-only) variant. The model exhausted the frozen token budget
  before emitting valid JSON. `max_tokens` was **not** raised to chase them:
  changing a frozen protocol parameter mid-run is the exact defect that blocked
  Gate 07 v2. They are excluded as typed provider failures and never became
  wrong answers.
- Recorded spend `$0.20574795` against the `$1.20` hard cap. No abort, no
  checkpoint, no daily-quota stop, no `client_throttled` row.
- 540 decision rows (6 arms x 2 models x 45 cases): 527 scored, 13
  `signature_unavailable` — all in `ablate_schema_only`, all downstream of the
  19 missing signatures.
- Artifact SHA-256: `signatures.jsonl`
  `5a7f27314432c833711bbc06b15a81ad333a9e246d2a4a693d5084e9ca66df34`;
  `raw/signatures.jsonl`
  `e1740b3519b856efa47fe6b6559e5d077dc4284a7eb0702b326a267c80e713f3`;
  `decisions.jsonl`
  `ddbd0a43e50c492a570c28982d32d44cb1a04d102918969bf17edce79eb96d35`;
  `thresholds.json`
  `71b0b5d724f1ea1949bdd27b8d4f79c74f45b9d0a86fb1b262ca661ac030f7ed`;
  `request_ledger.jsonl`
  `7be305af91e2baca7f1b7e60d0323d5f875a5f6cfe3ae18514e58a29fd947094`.
- The metric report was built twice from the same inputs. Both runs exited `0`
  and both files have SHA-256
  `7fd06b63dbc79a9bf79e7c9ed064f55af53c069ef0be1b455e76ad9637394b09`.

## Calibration

Thresholds were fitted on the 36 held-out cases only. `retrieval_floor` was
grid-searched against held-out labels; `abstain_floor` is a label-free coverage
quantile at a 0.30 target, so the abstention rule could not be tuned toward a
score. Fitted values for `gate08_method`: floor `0.55` on both models, abstain
`0.6432` (120b) and `0.6225` (20b), with held-out balanced accuracy `0.970` and
`0.955` for the equivalent/no-equivalent split.

That balanced accuracy rests on **3 negative cases**. It is a weak calibration
signal and it did not transfer: the target abstention rate was 0.30, and the
observed rate on graded `argument_split` was 0.60 (120b). The method
over-declines on exactly the family it was meant to help.

## Full results

### `argument_split` -- Gate 08 arms

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `gate08_method` / 120b | 0.6000 [0.3575,0.8018] n=15 | 0.2000 [0.0000,0.4000] n=15 | N/A | 0.6000 [0.3575,0.8018] n=15 | 0.2000 [0.0000,0.4000] n=15 |
| `gate08_method` / 20b | 0.8667 [0.6212,0.9626] n=15 | 0.5333 [0.3067,0.7467] n=15 | N/A | 0.6667 [0.4171,0.8482] n=15 | 0.2667 [0.0667,0.4667] n=15 |
| `ablate_no_history` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.2667 [0.0667,0.4667] n=15 | N/A | 0.7333 [0.4805,0.8910] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_history` / 20b | 1.0000 [0.7961,1.0000] n=15 | 0.6000 [0.3733,0.8000] n=15 | N/A | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_schema_only` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.9333 [0.7018,0.9881] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_schema_only` / 20b | 0.9333 [0.7018,0.9881] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.8000 [0.5481,0.9295] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_intent_abstraction` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.5333 [0.2667,0.7333] n=15 | N/A | 0.3333 [0.1518,0.5829] n=15 | 0.5333 [0.2667,0.8000] n=15 |
| `ablate_no_intent_abstraction` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.5333 [0.2667,0.7333] n=15 | N/A | 0.3333 [0.1518,0.5829] n=15 | 0.5333 [0.2667,0.8000] n=15 |
| `ablate_no_preconditions_effects` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.3333 [0.1333,0.5333] n=15 | N/A | 0.6000 [0.3575,0.8018] n=15 | 0.3333 [0.1333,0.6000] n=15 |
| `ablate_no_preconditions_effects` / 20b | 0.9333 [0.7018,0.9881] n=15 | 0.6000 [0.3733,0.8000] n=15 | N/A | 0.6000 [0.3575,0.8018] n=15 | 0.3333 [0.1333,0.6000] n=15 |
| `ablate_no_calibration` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.2000 [0.0000,0.4000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.2000 [0.0000,0.4000] n=15 |
| `ablate_no_calibration` / 20b | 0.8667 [0.6212,0.9626] n=15 | 0.5333 [0.3067,0.7467] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.2667 [0.0667,0.4667] n=15 |

### `argument_split` -- frozen Gate 07 arms rescored on the same 15 cases

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `lexical_name` / offline | 1.0000 [0.7961,1.0000] n=15 | 0.1667 [0.0667,0.3000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `lexical_serialized` / offline | 0.8000 [0.5481,0.9295] n=15 | 0.1667 [0.0667,0.3000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_name_desc` / offline | 1.0000 [0.7961,1.0000] n=15 | 0.1667 [0.0667,0.3000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_serialized_schema` / offline | 0.6000 [0.3575,0.8018] n=15 | 0.0333 [0.0000,0.1000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `cross_encoder` / offline | 0.6000 [0.3575,0.8018] n=15 | 0.0333 [0.0000,0.1000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `positional_prior` / control | 0.4000 [0.1982,0.6425] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `random_choice` / control | 0.2000 [0.0705,0.4519] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `llm_new_schema_only` / 120b | 0.9333 [0.7018,0.9881] n=15 | N/A | N/A | 0.0000 [0.0000,0.2039] n=15 | N/A |
| `llm_new_schema_only` / 20b | 0.8462 [0.5777,0.9567] n=13 | N/A | N/A | 0.0000 [0.0000,0.2281] n=13 | N/A |
| `llm_old_new_direct` / 120b | 0.5000 [0.2538,0.7462] n=12 | 0.4444 [0.1944,0.7222] n=12 | N/A | 0.0000 [0.0000,0.2425] n=12 | 0.5000 [0.2500,0.7500] n=12 |
| `llm_old_new_direct` / 20b | 0.3000 [0.1078,0.6032] n=10 | 0.3000 [0.0000,0.6000] n=10 | N/A | 0.0000 [0.0000,0.2775] n=10 | 0.0000 [0.0000,0.0000] n=10 |
| `llm_old_new_history` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.6889 [0.4667,0.8889] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.7333 [0.4667,0.9333] n=15 |
| `llm_old_new_history` / 20b | 0.5714 [0.3259,0.7862] n=14 | 0.5476 [0.2857,0.7857] n=14 | N/A | 0.0000 [0.0000,0.2153] n=14 | 0.5714 [0.2857,0.8571] n=14 |
| `llm_reasoning` / 120b | 0.1429 [0.0401,0.3994] n=14 | 0.1190 [0.0000,0.3095] n=14 | N/A | 0.0000 [0.0000,0.2153] n=14 | 0.0000 [0.0000,0.0000] n=14 |
| `llm_reasoning` / 20b | 0.5385 [0.2914,0.7679] n=13 | 0.4026 [0.1897,0.6333] n=13 | N/A | 0.0000 [0.0000,0.2281] n=13 | 0.3077 [0.0769,0.5385] n=13 |
| `llm_old_new_direct_v3_legacy` / 120b | 0.2000 [0.0705,0.4519] n=15 | 0.2267 [0.0533,0.4533] n=15 | N/A | 0.6667 [0.4171,0.8482] n=15 | N/A |
| `llm_old_new_direct_v3_legacy` / 20b | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.9333 [0.7018,0.9881] n=15 | N/A |

### `tool_replacement` -- Gate 08 arms

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `gate08_method` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.1333 [0.0374,0.3788] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `gate08_method` / 20b | 0.6667 [0.4171,0.8482] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.1333 [0.0374,0.3788] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_history` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.2000 [0.0705,0.4519] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_history` / 20b | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.2000 [0.0705,0.4519] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_schema_only` / 120b | 0.9333 [0.7018,0.9881] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.4667 [0.2481,0.6988] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_schema_only` / 20b | 0.5833 [0.3195,0.8067] n=12 | 0.0000 [0.0000,0.0000] n=12 | N/A | 0.1667 [0.0470,0.4480] n=12 | 0.0000 [0.0000,0.0000] n=12 |
| `ablate_no_intent_abstraction` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_intent_abstraction` / 20b | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.6667 [0.4171,0.8482] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_preconditions_effects` / 120b | 0.6667 [0.4171,0.8482] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.1333 [0.0374,0.3788] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_preconditions_effects` / 20b | 0.6667 [0.4171,0.8482] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.1333 [0.0374,0.3788] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_calibration` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_calibration` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.1333 [0.0533,0.2400] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |

### `tool_replacement` -- frozen Gate 07 arms rescored on the same 15 cases

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `lexical_name` / offline | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `lexical_serialized` / offline | 0.7333 [0.4805,0.8910] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_name_desc` / offline | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_serialized_schema` / offline | 0.7333 [0.4805,0.8910] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `cross_encoder` / offline | 0.9333 [0.7018,0.9881] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `positional_prior` / control | 0.2667 [0.1090,0.5195] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `random_choice` / control | 0.2000 [0.0705,0.4519] n=15 | 0.0000 [0.0000,0.0000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `llm_new_schema_only` / 120b | 1.0000 [0.7961,1.0000] n=15 | N/A | N/A | 0.0000 [0.0000,0.2039] n=15 | N/A |
| `llm_new_schema_only` / 20b | 1.0000 [0.7961,1.0000] n=15 | N/A | N/A | 0.0000 [0.0000,0.2039] n=15 | N/A |
| `llm_old_new_direct` / 120b | 0.2667 [0.1090,0.5195] n=15 | 0.1333 [0.0333,0.2667] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.2667 [0.0667,0.4667] n=15 |
| `llm_old_new_direct` / 20b | 0.4000 [0.1982,0.6425] n=15 | 0.2200 [0.0867,0.3667] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.3333 [0.1333,0.6000] n=15 |
| `llm_old_new_history` / 120b | 0.3333 [0.1518,0.5829] n=15 | 0.1667 [0.0667,0.2667] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.3333 [0.1333,0.6000] n=15 |
| `llm_old_new_history` / 20b | 0.6667 [0.4171,0.8482] n=15 | 0.3867 [0.2333,0.5333] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.4000 [0.2000,0.6667] n=15 |
| `llm_reasoning` / 120b | 0.1333 [0.0374,0.3788] n=15 | 0.0667 [0.0000,0.1667] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.1333 [0.0000,0.3333] n=15 |
| `llm_reasoning` / 20b | 0.6000 [0.3575,0.8018] n=15 | 0.3000 [0.1667,0.4000] n=15 | N/A | 0.0000 [0.0000,0.2039] n=15 | 0.5333 [0.2667,0.8000] n=15 |
| `llm_old_new_direct_v3_legacy` / 120b | 0.0667 [0.0119,0.2982] n=15 | 0.0333 [0.0000,0.1000] n=15 | N/A | 0.9333 [0.7018,0.9881] n=15 | N/A |
| `llm_old_new_direct_v3_legacy` / 20b | 0.1333 [0.0374,0.3788] n=15 | 0.0667 [0.0000,0.1667] n=15 | N/A | 0.8667 [0.6212,0.9626] n=15 | N/A |

### `no_equivalent` -- Gate 08 arms

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `gate08_method` / 120b | 0.8000 [0.5481,0.9295] n=15 | 0.8000 [0.6000,1.0000] n=15 | 0.8000 [0.5481,0.9295] n=15 | 0.1333 [0.0374,0.3788] n=15 | 0.8000 [0.6000,1.0000] n=15 |
| `gate08_method` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2000 [0.0705,0.4519] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_no_history` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2667 [0.1090,0.5195] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_no_history` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2000 [0.0705,0.4519] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_schema_only` / 120b | 0.4667 [0.2481,0.6988] n=15 | 0.6000 [0.3333,0.8667] n=15 | 0.4667 [0.2481,0.6988] n=15 | 0.3333 [0.1518,0.5829] n=15 | 0.4667 [0.2000,0.7333] n=15 |
| `ablate_schema_only` / 20b | 0.8000 [0.3755,0.9638] n=5 | 0.8000 [0.4000,1.0000] n=5 | 0.8000 [0.3755,0.9638] n=5 | 0.0000 [0.0000,0.4345] n=5 | 0.8000 [0.4000,1.0000] n=5 |
| `ablate_no_intent_abstraction` / 120b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2000 [0.0705,0.4519] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_no_intent_abstraction` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2000 [0.0705,0.4519] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_no_preconditions_effects` / 120b | 0.8000 [0.5481,0.9295] n=15 | 0.8000 [0.6000,1.0000] n=15 | 0.8000 [0.5481,0.9295] n=15 | 0.1333 [0.0374,0.3788] n=15 | 0.8000 [0.6000,1.0000] n=15 |
| `ablate_no_preconditions_effects` / 20b | 0.7333 [0.4805,0.8910] n=15 | 0.7333 [0.4667,0.9333] n=15 | 0.7333 [0.4805,0.8910] n=15 | 0.2000 [0.0705,0.4519] n=15 | 0.7333 [0.5333,0.9333] n=15 |
| `ablate_no_calibration` / 120b | 0.0000 [0.0000,0.2039] n=15 | 0.3333 [0.1333,0.5333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `ablate_no_calibration` / 20b | 0.0000 [0.0000,0.2039] n=15 | 0.3333 [0.1333,0.5333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |

### `no_equivalent` -- frozen Gate 07 arms rescored on the same 15 cases

| Arm / model | Tool@1 | Arg F1 | No-equivalent | Abstention | First-attempt |
|---|---|---|---|---|---|
| `lexical_name` / offline | 0.0000 [0.0000,0.2039] n=15 | 0.1333 [0.0000,0.3333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `lexical_serialized` / offline | 0.0000 [0.0000,0.2039] n=15 | 0.3333 [0.1333,0.5333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_name_desc` / offline | 0.0000 [0.0000,0.2039] n=15 | 0.2667 [0.0667,0.5333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `embed_serialized_schema` / offline | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `cross_encoder` / offline | 0.0000 [0.0000,0.2039] n=15 | 0.4667 [0.2000,0.7333] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `positional_prior` / control | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `random_choice` / control | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.2039] n=15 | 0.0000 [0.0000,0.0000] n=15 |
| `llm_new_schema_only` / 120b | 0.9333 [0.7018,0.9881] n=15 | N/A | 0.9333 [0.7018,0.9881] n=15 | 0.0000 [0.0000,0.2039] n=15 | N/A |
| `llm_new_schema_only` / 20b | 1.0000 [0.7961,1.0000] n=15 | N/A | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | N/A |
| `llm_old_new_direct` / 120b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_old_new_direct` / 20b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_old_new_history` / 120b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_old_new_history` / 20b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_reasoning` / 120b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_reasoning` / 20b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 0.0000 [0.0000,0.2039] n=15 | 1.0000 [1.0000,1.0000] n=15 |
| `llm_old_new_direct_v3_legacy` / 120b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | N/A |
| `llm_old_new_direct_v3_legacy` / 20b | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [1.0000,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | 1.0000 [0.7961,1.0000] n=15 | N/A |

## Required ablations

All six are runnable and were run. Five are Gate 08 arms; the sixth is the
frozen Gate 07 `llm_old_new_history` evidence, reused rather than re-collected
because it is already a single-shot frontier-LLM mapper with strictly *greater*
information rights than this method — it sees the old contract, the traces, and
every candidate in one call. Re-running it would have spent budget to reproduce
frozen evidence.

| Ablation | Implemented as | What it shows |
|---|---|---|
| no history | signature built without verified traces | On `argument_split` it **improves** Arg F1 (0.6000 vs 0.5333 on 20b) and destroys first-attempt (0.0000 vs 0.2667). Traces buy value construction, not correspondence. |
| schema only | new contracts and task description only | Collapses Arg F1 to 0.0000 in both claim families. Also the only arm with missing rows (13). |
| no intent abstraction | raw field names as their own concepts, no LLM at all | **Matches or beats the full method everywhere in `argument_split`** (Arg F1 0.5333 vs 0.2000/0.5333; first-attempt 0.5333 vs 0.2000/0.2667). |
| no preconditions/effects | those signature fields removed | Slightly *better* than the full method on `argument_split` 20b (Arg F1 0.6000 vs 0.5333). Those dimensions carry no weight here. |
| no calibration | forced `ALIGN`, abstention disabled | Drives `no_equivalent` accuracy from 0.8000 to 0.0000 and leaves the claim families unchanged. Calibration is the one component that does its job. |
| direct frontier-LLM mapper | frozen Gate 07 V4.1 `llm_old_new_history`, reused | The strongest cell in both claim families on Argument F1 and first-attempt. |

The third row is the decisive one. **The LLM intent abstraction is not earning
its place**: a purely deterministic pipeline that treats raw field names as
concepts, costing nothing per case, matches or beats it on the family Gate 07
authorized. The two-sided abstraction was the method's whole claim to novelty,
and the ablation says it subtracts value rather than adding it. The likely
mechanism is concept divergence — the two independent abstractions do not always
agree on a noun for the same real-world thing, and every disagreement silently
breaks the exact-concept pass that the rest of the pipeline is built on.

## Two dataset findings that qualify Gate 07's narrow GO

Both are post-hoc measurements of the frozen dataset. Neither removed a case,
numerator, or denominator from anything above.

**1. 28.6% of the `tool_replacement` ground-truth argument pairs are
unreachable.** 10 of 35 name a `new_arg` that is not a field of the new contract
the method is shown — for example a pair mapping onto `section_ref` in
`grant_completion_credential`, which has no such field. No arm can emit those
without inventing a field name, so the maximum attainable Argument Mapping
recall for that family is **0.7143**, not 1.0. `argument_split` is clean:
0 of 40 pairs unreachable, maximum recall 1.0.

This matters for reading Gate 07. Part of the `tool_replacement` Argument F1
"failure region" that Gate 07 identified is an artifact of its own oracle, not a
property of the models. The `tool_replacement` half of the narrow GO should be
treated as weaker than the `argument_split` half until the oracle pairs are
repaired. Recomputable via
`research/gate08/metrics/diagnostics.oracle_reachability`.

**2. The merge separator is not in anyone's information rights.** Five of the 15
`tool_replacement` cases require an argument value built by joining two old
values with `::`. That separator appears nowhere in any contract, description,
schema, or trace the method is allowed to see — only in the sandbox's internal
operations code. The method's pre-registered policy is to report the
correspondence and emit `join_unresolved` rather than invent a separator, which
produces an unconstructible call. The frozen Gate 07 baselines that succeeded on
those cases did so by guessing an unstated convention.

That policy is a real cost: it contributes 5 of the 15 `tool_replacement`
first-attempt failures. It does not explain the other 10, which are alignment
misses. The method's `tool_replacement` first-attempt outcome distribution
(`gate08_method` / 120b) is 10 `malformed_call` and 5 `precondition_failed`, and
0 succeeded. Reporting 0.0000 while a guessing baseline reports 0.5333 is the
honest comparison, and the policy stays.

## Where the method is not worthless

On `argument_split` Argument F1, `gate08_method` / 20b (0.5333) and
`ablate_no_history` / 20b (0.6000) beat every frozen *deterministic* baseline
(best 0.1667, `lexical_name` / `lexical_serialized` / `embed_name_desc`), both
controls (0.0000), `llm_old_new_direct` / 20b (0.3000), `llm_reasoning` / 120b
(0.1190), and the v3 legacy arm (0.2267). They lose only to
`llm_old_new_history` / 120b (0.6889) and `llm_old_new_history` / 20b (0.5476).

So the residual conservation-of-information pass does recover unannounced splits
that no deterministic baseline recovers. It is just not competitive with simply
handing one strong model both sides of the interface at once.

## Acceptance checklist

- [x] Method interface frozen — digest pinned in the protocol, re-verified at
      every run, enforced by preflight.
- [x] Information rights documented — per arm in the protocol and the report;
      the reduced-rights arms are proven strict subsets by test.
- [x] No-equivalent supported — a first-class verdict, end to end, scored at
      0.8000 on the control family.
- [x] Calibration/abstention implemented — fitted on held-out only; fitted values
      and diagnostics recorded.
- [x] Required ablations runnable — all six, five run here and one reused with
      its reuse declared.
- [x] First-attempt metric separate — its own metric, one execution per case,
      through the unchanged Gate 07 executor.
- [x] Raw decisions/traces retained — append-only signatures, raw prompts and
      responses, decisions, request ledger; all hashed above.
- [x] `GATE_08_RESULT.md` written — this file.
- [x] Gate-0 and Gate 07 preserved exactly — enforced by a test that fails if
      `research/gate0/`, `research/gate07/dataset/`, `research/gate07/oracle/`,
      or `research/gate07/sandbox/` is dirty. Gate 07 baselines were re-scored,
      never re-run.
- [x] No hidden migration ground truth — a test asserts `research/gate08/method/`
      never references the oracle, the evaluator capability, a case id, or a
      drift-family name.
- [x] No product-specific heuristics — same test.
- [x] Result states plainly whether the method beat the frozen baseline — it did
      not, and by how much is the first table in this file.
- [x] No paper prose written.

## Tests

`540 passed, 2 warnings` for the full suite at `c419bca`, and
`compileall` exit `0`. The Gate 08 additions are
`tests/test_gate08_method.py`, `tests/test_gate08_boundary.py`,
`tests/test_gate08_protocol.py`, and `tests/test_gate08_metrics.py`.

## Residual risks and honest limitations

- **Designer exposure to ground truth.** While scoping the method, the ground
  truth of three graded cases (`G07-G-0073`, `G07-G-0127`, `G07-G-0199`) was
  read before the development discipline was tightened to held-out cases only.
  No case id, family label, or oracle field is present in the method code, and a
  test enforces that. But the design was not authored in complete ignorance of
  three graded cases, and that is a residual design-time risk, not a clean room.
- **n = 15 per family.** Every interval above is wide. Several deltas that look
  decisive have overlapping intervals. The negative headline is supported by the
  *direction being consistent across every arm, model, and metric*, not by any
  single interval.
- **3 negative calibration cases.** The retrieval floor is fitted against three
  held-out no-equivalent examples. It transferred poorly, as the observed
  over-abstention shows.
- **19 uncollected signatures** concentrate in the weakest model's weakest
  ablation, so `ablate_schema_only` / 20b is measured on fewer cases than the
  others. The report's imputation-sensitivity block bounds every affected cell.
- **Single provider family.** Both pinned models are `openai/gpt-oss-*` on Groq.
  Nothing here establishes how the abstraction behaves on a different model
  family.

## Decision

The method specified by Gate 08 is **not justified by the Gate-0 failure it was
built to address**. It is not adopted. The specific finding that should drive any
follow-on plan is that the intent-abstraction stage — the mechanism's entire
claim to novelty — is beaten by its own no-abstraction ablation on the family
Gate 07 authorized.

## Next allowed action

No Gate 09 work was performed or authorized, and none is authorized by this
result. The only allowed next step is a separately approved plan, which should
address, before proposing another mechanism:

1. repairing or excluding the 10 unreachable `tool_replacement` oracle pairs and
   re-reading Gate 07's `tool_replacement` GO in that light;
2. deciding whether the merge separator belongs in the method's information
   rights at all, since no method can currently construct those values honestly;
3. whether a redesigned mechanism can make independent two-sided abstraction
   agree on concepts, given that the ablation shows raw field names currently do
   better.

STOP: No Gate 09 work performed.
