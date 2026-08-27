# Gate 06 — Versioned Tool Registry and Education Drift Sandbox

**Status:** `PASS` (see `gates/results/GATE_06_RESULT.md`; not yet
committed -- awaiting user authorization)

**Source:** `gates/GATE_06_TOOL_REGISTRY_AND_EDUCATION_SANDBOX.md`

## Objective

Build a deterministic sandbox with versioned tool contracts, v1/v2/v3 education
APIs, hidden migration ground truth, old traces, and realistic drift/no-equivalent
families for later research evaluation.

## Non-Negotiables

- All writes affect sandbox data only; reset/evaluator must be deterministic.
- Include at least eight drift families, semantic near-collisions and no-equivalent
  cases; keep mappings inaccessible to tested methods.
- Do not design cases to make a planned method win, and do not implement a final
  method here.

## Exit

Write `GATE_06_RESULT.md`; STOP.
