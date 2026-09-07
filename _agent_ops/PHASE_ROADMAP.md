# Phase Roadmap / Lo trinh giai doan

## Program State

`GATE_09R_MAINTENANCE_ARC_COMPLETE — product-only release and documentation
closure; C0 local governance baseline 17059a6; validated runtime source
2d775ee. The last pushed Gate 09R closure is 3ceba47; no push was authorized
for the maintenance commits.`
Gates 00-06 are PASS and pushed to origin/main. Gate 07 remains a narrow V4.1
`GO` for `argument_split` and `tool_replacement`. Gate 08 is closed NEGATIVE:
its proposed method is not adopted (DEC-0023). Gate 09R closed PASS as a
product-only release (DEC-0027); its maintenance-only follow-up is recorded in
`gates/results/GATE_09RM_RESULT.md`.
The 09R-M, 09R-V, and 09R-C maintenance records are complete. No further
observation or action is authorized by this arc. The original Gate 09 full
evaluation and Gate 10 remain unavailable.
The source Evolve pack was adapted into compact cards under
`phase_context_cards/evolve_2026_08_26/`; this roadmap is the execution-order
authority for future tasks.

## Ordered Gates

| Gate | Goal | Prerequisite | Status | Next artifact |
| --- | --- | --- | --- | --- |
| 00 | Baseline freeze and safe restructure | User starts baseline slice | PASS — committed, pushed | `GATE_00_RESULT.md` |
| 01 | Governed document lifecycle | Gate 00 PASS | PASS — committed, pushed | `GATE_01_RESULT.md` |
| 02 | MarkItDown local fast mode | Gate 01 result | PASS — committed, pushed | `GATE_02_RESULT.md` |
| 03 | Firecrawl candidate import | Gate 02 result + explicit secret handoff | PASS — committed, pushed | `GATE_03_RESULT.md` |
| 04 | Version-aware RAGOps | Gate 03 result | PASS — committed, pushed | `GATE_04_RESULT.md` |
| 05 | Provider modes and secure MCP | Gate 04 result | PASS — committed, pushed | `GATE_05_RESULT.md` |
| 06 | Versioned tool registry + sandbox | Gate 05 result | PASS — committed, pushed | `GATE_06_RESULT.md` |
| 07 | Falsification-first scientific Gate-0 | Gate 06 result and frozen protocol | GO (narrow V4.1: `argument_split`, `tool_replacement`) | `GATE_07_RESULT.md` |
| 08 | Alignment method | Gate 07 `GO` only | NEGATIVE — method not adopted | `GATE_08_RESULT.md` (written) |
| 09 | Full evaluation and approved GCP deployment | Gate 08 + frozen evidence | Unavailable — original full evaluation not authorized | `GATE_09_RESULT.md` |
| 09R | Product-only release and observation | Gate 09R product-only authorization | PASS — product-only release | `GATE_09RM_RESULT.md` |
| 09R-M | Bounded observation and ops-memory reconciliation | Gate 09R PASS | COMPLETE — read-only observation | `GATE_09RM_RESULT.md` |
| 09R-V | Verification gap closure and web availability triage | Gate 09R-M result | COMPLETE — CAPACITY | `GATE_09RV_RESULT.md` |
| 10 | Final freeze, technical report and arXiv | Gate 09 PASS | Unavailable — Gate 09R does not authorize Gate 10 | `GATE_10_RESULT.md` |

## Hard Rules

- A prepared tool or environment never satisfies its implementation gate.
- Each gate records evidence and then stops. No silent gate jump.
- Preserve baseline behavior and keep candidate sources separate from live RAG.
- Product/demo fallback cannot contaminate research results; research fallback is
  disabled when Gate 07 starts.
- `STOP` and `REFORMULATE` are valid scientific outcomes. Gate 08 is negative
  and must not be rerun, tuned, rescored, or revived. That result does not
  authorize the original Gate 09; Gate 09R was a separately approved
  product-only lane and does not authorize Gate 10.
- Cloud/paper work is late-stage and cannot be used to backfill missing evidence.

## Prepared, But Not Integrated

- MarkItDown: Gate 02 tool prerequisite only.
- Firecrawl: Gate 03 completed one bounded candidate-only call; no new call is
  permitted in Gate 09R-M.
- See `_agent_ops/THIRD_PARTY_TOOLING.md` for revisions and safe update rules.

## Consistency Audits

- Before Gate 00: current runtime/data/test proof.
- Before Gate 02: candidate/live lifecycle separation.
- Before Gate 03: secret handoff and SSRF/budget design.
- Before Gate 07: exact frozen research protocol and information rights.
- Before Gate 09/10: deployment/reproducibility evidence and live policy refresh;
  the original Gate 09 and Gate 10 remain unavailable after Gate 09R.
- Before any follow-on method gate: resolve RISK-0021 (unreachable
  `tool_replacement` oracle pairs) and RISK-0022 (unobservable merge separator),
  and fix the development/calibration split before design begins (RISK-0023).

## Historical

The superseded pre-09R snapshot recorded the program state as
`GATE_08_CLOSED_NEGATIVE — alignment method not adopted; ops HEAD e43c932.`
Its then-current table said Gate 00 `Next / not started`, Gate 01 `Blocked`,
Gate 02 `Tool prepared only`, Gate 03 `Tool prepared only`, and Gates 04-06
`Blocked`. Those values are retained here as historical context only.
