# Gate 08 — Cross-Version Alignment Method

**Status:** `CLOSED 2026-08-29 — NEGATIVE. Method not adopted. Gate 09 forbidden.`
**Source:** `gates/GATE_08_ALIGNMENT_METHOD.md` (pack copy)
**Result:** `gates/results/GATE_08_RESULT.md`
**Protocol:** `gates/baselines/GATE_08_PROTOCOL.json`
**Execution prompt:** `GATE_08_EXECUTION_PROMPT.md` (this folder)

## Objective

Implement the one mechanism justified by Gate-0 — intent signature, candidate
retrieval, correspondence/argument alignment, abstention/no-equivalent, one
first adapted execution — and test it against the frozen Gate 07 baselines.

## Scope actually run

Bounded by Gate 07's narrow V4.1 GO, pre-registered before any Gate 08 number:
graded `argument_split` (15) and `tool_replacement` (15) as the claim surface,
graded `no_equivalent` (15) as an abstention safety control, and the 36 held-out
cases as the calibration split. Gate 07 baselines were re-scored on this surface,
never re-run.

## Outcome

The method loses to the frozen Gate 07 baselines on every compared metric in
every evaluated family. The decisive ablation is `no_intent_abstraction`: a
deterministic pipeline with no LLM matches or beats the full method on
`argument_split`, so the two-sided intent abstraction — the mechanism's whole
claim to novelty — is not earning its place.

Two dataset findings qualify Gate 07 itself: 28.6% of `tool_replacement`
ground-truth argument pairs name a field absent from the new contract (maximum
attainable recall 0.7143), and the `::` merge separator is not in any method's
information rights.

## Controls held

Gate-0 baselines and Gate 07 dataset, oracle, and sandbox unmodified — enforced
by test. Information rights declared per arm. No migration ground truth in the
method. No pre-first-call trial and error. No case moved into calibration.

## Exit

`GATE_08_RESULT.md` written; STOP. Gate 09 requires a separately approved plan.
