# Gate 07 — Scientific Gate-0

**Status:** `GO — narrow V4.1 regions: argument_split and tool_replacement`  
**Source:** `gates/GATE_07_SCIENTIFIC_GATE0.md`

## Objective

Try to falsify the need for a new cross-version alignment method before building it.

## Freeze Before Evidence

Freeze dataset/case balance and checksum, hidden ground truth, baseline prompts,
model IDs, retry/timeout policy, metrics and exclusions. Retain raw outputs;
treat provider failures separately from wrong answers.

## Decision Rule

Run strong embedding, cross-encoder and direct-LLM baselines under identical
information rights. Outcomes are `GO`, `REFORMULATE`, or `STOP`. `GO` requires a
stable, practically meaningful failure region that survives baselines and maps to
first-attempt consequences. A negative result is success for the gate.

## V4.1 Closure

The original V4 headline was operationally invalid because four collection and
accounting defects left the strongest forced `argument_split` carrier at
`n=8 < family_minimum=15`. The committed V4.1 addendum remediated client
throttling/cache semantics, HTTP error-body retention, output-token usage,
`max_tokens=1536`, deterministic arm/model order, hard cost protection, and
latest-attempt resolution. It recollected only non-success logical keys on the
unchanged cases, prompts, candidate order, and pinned models.

The final result has 1,800 logical keys, 784 fresh attempts, recorded cost
`$0.23893425 <= $1.20`, and two deterministic metric regenerations with the
same SHA. The narrow GO regions are `argument_split` and `tool_replacement`;
the base V4 protocol and freeze ledger were not changed. See
`gates/results/GATE_07_RESULT.md`, DEC-0021, DEC-0022, and
`gates/results/GATE_07_V4_CLOSURE_RECEIPT.md`.

## Exit

`gates/results/GATE_07_RESULT.md` records the authoritative V4.1 narrow `GO`.
Historical v2 evidence remains disqualified and no Gate 08 work is allowed;
the current task explicitly ends after Gate 07.
