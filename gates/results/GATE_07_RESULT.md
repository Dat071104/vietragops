# Gate 07 Result — Scientific Gate-0

Status: **BLOCKED**

## Blocking reason

The pre-headline seed-leakage correction was represented by
`gates/baselines/GATE_07_PROTOCOL_V2.json`, but that amendment was not
committed before the v2 offline and LLM runs began. The last committed
protocol was v1 at `355daf0`; the v2 headline run started from
`3b6770f673523f093e9e3ff54c0133a2f24c7413` plus an uncommitted amendment.
The execution prompt requires the protocol freeze commit to precede every
Phase 7.4/7.5 headline run. A commit after the fact cannot repair that proof.

Therefore the v2 results are preserved as **DISQUALIFIED** audit artifacts.
This gate makes no scientific `GO`, `REFORMULATE`, or `STOP` decision.

## Entry-gate verification

- `HEAD`: `0561d54d5f623c0a913f222007f86a7f08ea3d66` at Phase 7.0; branch
  `main`; `git ls-remote origin main` matched exactly.
- `git merge-base --is-ancestor fed31c3 HEAD`: exit 0.
- The complete pre-existing 21-entry dirty overlay remained untouched and
  unstaged; the index was empty; `git diff --check` was clean.
- Gate 06 result existed with `Status: PASS`.
- Required baseline: **430 passed, 2 warnings** after rerunning the exact
  command with filesystem access; compileall exit 0.
- Ollama `/api/tags` succeeded. Groq configuration was inspected by variable
  names only at entry; no secret value is in this file.

## Commit / tree state

Valid preceding Gate 07 commits:

- `44be141` — extended sandbox and 216-case generator.
- `355daf0` — protocol v1 freeze.
- `bcdaca5` — rights-enforced baseline harness and raw artifact boundary.
- `3b6770f` — offline baseline code and metric support.

The v2 amendment and Phase 7.5 runner changes were present in the working tree
but not committed at headline start. No push was performed. Raw artifacts and
ledgers remain under ignored `gates/artifacts/gate07/`.

## Protocol freeze and amendment

Protocol v1:

- File: `gates/baselines/GATE_07_PROTOCOL.json`.
- Freeze commit: `355daf0`.
- It preceded the original v1 offline run, but its dataset was later found to
  expose generator seed text in public task material before any scientific
  result was accepted.

Protocol v2 amendment:

- File: `gates/baselines/GATE_07_PROTOCOL_V2.json`.
- Graded manifest digest: `sha256:32f0d29279dbbeb28ea7c3db1d076334242c7b2c092f4ac09cc32f8fb927890e`.
- Held-out manifest digest: `sha256:b4bee8ef70e14bec1d0c814394348e217bbaca9270d047ff13fc4a2da85e94a9`.
- Graded ground-truth digest: `sha256:859823d52068e4cd9f54dcb95674ba941c04794b2d7f269a6f6a5c7068614856`.
- Amendment reason: remove direct seed-bearing task/trace text; public audit
  confirmed no `20260827`, `family`, `operator`, `lineage_key`, or `tool_id`.
- Required freeze status at headline start: **NOT_COMMITTED**. This is the
  protocol violation; v2 is not an admissible freeze for the results below.

## Dataset summary

- Total generated: 216 cases.
- Graded: 180 cases.
- Held-out: 36 cases, 3 per family; not run.
- Family balance: all 12 families have 15 graded and 3 held-out cases.
- Sandbox surface: 39 synthetic tools per version; state is in-memory only.
- D9 one-old-to-multiple-new and D10 multiple-old-to-one-new shapes were
  represented explicitly before scoring.

## Baseline arms and runs

The v2 public task file contained only method-facing contracts/traces and no
oracle, family, operator, lineage, seed, or tool ID fields.

- Offline v2: lexical-name, lexical-serialized, BGE-M3 name/description,
  BGE-M3 serialized-schema, and BGE reranker cross-encoder.
- LLM v2: `llm_new_schema_only`, `llm_old_new_direct`,
  `llm_old_new_history`, and `llm_reasoning`, each on
  `openai/gpt-oss-120b` and `openai/gpt-oss-20b`.
- LLM runner used `ProviderRouter(mode="research")`, one sequential process,
  existing Groq client/key pool, frozen prompt IDs, cache keys, and ledger.
- No proposed intent/alignment method was implemented or run.

## Run inventory and provider accounting

These counts are factual run inventory only; they are not admissible scientific
metrics because the v2 amendment was uncommitted.

| Artifact | Records | Success | Parse failure | Provider error |
|---|---:|---:|---:|---:|
| Offline v2 predictions | 900 | 900 | 0 | 0 |
| Offline v2 raw records | 900 | 900 | 0 | 0 |
| LLM v2 results | 1,440 | 1,379 | 24 | 37 |
| LLM v2 raw records | 1,440 | 1,379 | 24 | 37 |

The LLM sweep had 720 records per model and 360 per arm. The 24 parse failures
and 37 provider errors never entered accuracy numerators or denominators.
Existing Groq 429 cooldown events were handled by the existing client; no
terminal rate-limited row was coerced into a wrong answer. Preflight was 8/8
successful. The `/models` verification request itself returned HTTP 403 and
was recorded as unverified provider model availability.

## Preliminary diagnostics — disqualified

An evaluator-only metric preview was generated after the v2 runs, before the
freeze-order violation was recognized. It is retained only to make the failure
lineage complete; it must not be cited as Gate 07 evidence. No official
`GATE_07_METRICS.json`, ambiguity result, or scientific decision was produced.

The disqualified preview showed Tool Alignment@1 / Argument F1:

| Arm/model | Tool@1 | Argument F1 | First-attempt success |
|---|---:|---:|---:|
| lexical_name | 0.7278 | 0.6139 | 0.4500 |
| lexical_serialized | 0.6833 | 0.5537 | 0.3944 |
| embed_name_desc | 0.8167 | 0.6463 | 0.4667 |
| embed_serialized_schema | 0.6556 | 0.5454 | 0.3944 |
| cross_encoder | 0.6389 | 0.5194 | 0.3667 |
| llm_new_schema_only / 120b | 0.1676 | 0.1676 | 0.1676 |
| llm_old_new_direct / 120b | 0.4911 | 0.5108 | 0.4911 |
| llm_old_new_history / 120b | 0.4727 | 0.4929 | 0.4727 |
| llm_reasoning / 120b | 0.5143 | 0.5333 | 0.5143 |

These numbers are not used to support any claim. History ablation is therefore
**not reportable**, and no conclusion about the history signal is allowed.

## Ambiguity audit

Not run. AGY-3 was unavailable, and no stratified blind annotation or oracle
adjudication was performed after the protocol violation. The absence of this
audit is another reason no scientific decision is made.

## Raw artifact checksums

All files below are ignored, retained locally, and not committed:

- `offline/lexical_v2.jsonl`: `1D8B043D95A91B6E0FDFC8353976603F395F0F770686357851096163DD2CCA4A`
- `offline/embedding_v2.jsonl`: `B13D46C2CC6F828B97A2CB5F0A3F552889B36183E31937ABCD742B8DD9289FA6`
- `offline/cross_encoder_v2.jsonl`: `D45CA52187CEA9B8BDC24BA730E7B0B511DFB2F8D45049C8877C572E4664CE78`
- `llm/results_v2.jsonl`: `EB715F9DE50A207D3745B319C8C7F885FE73F5D9F7A445789FB020DABBC54946`
- `raw/phase74_lexical_v2.jsonl`: `0B78FBEEC97B739821BE632F6EB95FE58D8CE8A7FDC8AB12AF741FA790101189`
- `raw/phase74_embedding_v2.jsonl`: `39236C695197E8E6ACBD9C4E9053B3C56D7E5D08DA699DB14DCEFD088C7F048C`
- `raw/phase74_cross_encoder_v2.jsonl`: `A604CFA2F7C59A571F1597BED4BA31C93FB7138FE105BF9B6D10AE4C79586E6E`
- `raw/phase75_llm_v2.jsonl`: `728E5C19CA1F95213E90B8F2E67D2D3CD251BE7A875A884D0E3895DA07144E4D`

## Result-consistency audit

AGY-4 was unavailable as a callable worker. A local read-only consistency
check reproduced all eight listed line counts and SHA-256 values exactly, and
reproduced the LLM totals (1,440 unique cache keys; 1,379 success, 24 parse
failure, 37 provider error). This validates artifact bookkeeping only; it does
not repair the missing pre-run protocol commit or make the v2 numbers
scientifically admissible.

## Acceptance checklist

- [ ] Protocol frozen before headline run — **failed**: v2 was uncommitted.
- [x] Dataset checksum recorded — v2 digest recorded above, but its run is
  disqualified by the freeze-order failure.
- [x] Baseline prompts versioned — `gate07-llm-*-v1`.
- [x] Research fallback disabled — runner asserted `mode="research"`; no
  Ollama fallback occurred.
- [x] Raw outputs retained — counts and checksums recorded above.
- [ ] Ambiguous cases audited — not run; AGY-3 unavailable.
- [ ] Decision written with quantitative scientific evidence — intentionally
  not possible from disqualified runs.
- [x] `GATE_07_RESULT.md` written.
- [x] No paper prose written.
- [x] Claims blacklist respected — no novelty claim over ToolEVO, ContDa, or
  MCPEvol-Bench; schema similarity was not treated as behavioral equivalence.
- [ ] AGY-4 independent result-consistency audit — unavailable; local
  count/hash reproduction is recorded above and is not claimed independent.

## Decision and next allowed action

Gate 07 is **BLOCKED**, not scientifically `STOP`. The only next allowed
action is a newly approved Gate 07 protocol repair/re-run plan that commits a
valid freeze before any new headline run and explicitly accounts for the
already-spent v2 budget. Gate 08 is not allowed. No next-Gate work was
performed.

STOP: No Gate 08 work performed.
