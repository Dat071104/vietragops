# Gate 07 V4.1 Closure Receipt

Status: **GO — narrow `argument_split` and `tool_replacement` regions only**

- Stage 1: offline verification reproduced the 31.00-minute tail collapse,
  180/180 HTTP-400 null bodies, the 56 exact missing-verdict key-set rows, and
  1,800/1,800 missing output usage fields; current V4 carrier was `n=8`.
- Stage 2: V4.1 fixed bounded client throttling, HTTP error-body retention,
  `max_tokens=1536`, provider usage accounting, and deterministic arm/model
  order. Full suite after the final code was **498 passed, 2 warnings, 0
  failed**; compileall exited 0.
- Stage 3: addendum
  `gates/baselines/GATE_07_PROTOCOL_V4_1_ADDENDUM.json` and DEC-0021 were
  committed before provider recollection; preflight returned `status=passed`.
- Stage 4: 784 missing logical keys were recollected with
  `759 success, 13 parse_failure, 12 provider_error, 0 client_throttled`;
  recorded cost was `$0.23893425` under the `$1.20` cap; zero held-out cases.
- Stage 5: append-only rows resolve to 1,800 unique keys; metrics run 1 and
  run 2 both have SHA-256
  `71aa32cf654814e9492caaded8dcd9895bb1a4712a001885731be366981c9dfc`.
- Final predicate: `argument_split` carrier F1 `0.6889`, `n=15`, CI upper
  `0.8889 < 0.90`; `tool_replacement` F1 `0.3867`, `n=15`, CI upper
  `0.5333 < 0.90`; `one_old_to_multiple_new` remains excluded by `3/3`
  ambiguity.
- Base V4 protocol and freeze ledger were not edited. No Gate 08 work was
  performed or authorized. No push was performed.

## Closure Receipt

- CURRENT_TASK.md      : updated with authoritative V4.1 state, files touched, ruled-out attempts, and next step
- IMPLEMENTATION_LOG.md: appended 2026-08-29 Gate 07 V4.1 evidence
- SESSION_BRIEF.md     : updated state + Last Verified Commit -> `234e852fa81a0f25abdbe47862e63f063222576e`
- PROJECT_CONTEXT_CARD : not needed (protected pre-existing dirty overlay; Gate 07 state is recorded in result/project state)
- DECISION_LOG.md      : DEC-0022 added
- RISK_REGISTER.md     : not needed (protected pre-existing dirty overlay; residual risk is recorded in DEC-0022 and this receipt)
- REPO_MAP.md          : not needed (protected pre-existing dirty overlay; no map refresh was allowed)
- PHASE_ROADMAP.md     : updated with the final narrow V4.1 Gate 07 state; preserved as the pre-existing untracked overlay and left unstaged

## Artifact hashes

- `llm_results.jsonl`: `c25e760841574ffa0eac2abb5fe7717e71f91533d2ab5be146f0c0794c17f599`
- `raw/llm.jsonl`: `b324e50a8428ff3c684226341584276470197b4cd24a725d73bd513895959200`
- `request_ledger.jsonl`: `fd1d53158f10e25bcd039e7546e9425ef4d12933101adbc68f6faa9deb117a52`
- Addendum: `df13ee0791222fdf19f456bae09fc6f4d338b549a45de09ed2b4edff0f1e3d0a`
