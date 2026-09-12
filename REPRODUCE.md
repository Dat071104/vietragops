# Independent Reproduction Guide (REPRODUCE.md)

**Paper:** *Unreachable Oracles: Ground-Truth Derivability in Synthetic Tool-Drift Benchmarks for LLM Agents*  
**Section Reference:** §8 (*Reproducibility and Traceability*)  
**Canonical Git Tag:** `gate10-paper-v1-20260911`  
**Evidence Ledger:** `gates/baselines/GATE_10_EVIDENCE_LEDGER.json` (commit `653aa81`)  
**Audit Protocol:** `gates/baselines/GATE_19_PROTOCOL.json` / `gates/baselines/GATE_19C_PROTOCOL.json`  

---

## 1. Overview & Objective

This repository contains the machine-readable evidence, offline auditor, and frozen datasets supporting the measurement paper *Unreachable Oracles*.

This document provides a single-command procedure for an independent researcher or external AI agent to reproduce and verify the load-bearing empirical claims of the paper in **under 5 minutes** (typically **< 10 seconds** on standard commodity hardware), with **zero external API calls**, **no GPU requirements**, and **deterministic bit-identical outputs**.

---

## 2. Quick Start (One-Command Reproduction)

From the `VietRagOps` repository root, activate your Python virtual environment and run:

```bash
python scripts/reproduce.py
```

*(Alternative direct script path)*:
```bash
python scripts/reproduce_audit.py
```

### Expected Execution Time
- **~7 to 10 seconds** total execution time.
- Returns **exit code 0** on complete pass.

---

## 3. What the Reproduction Script Verifies

The script executes 4 sequential validation stages corresponding to the core claims of the paper:

### Stage 1: Auditor Unit Test Suite
- **File:** `research/gate19/tests.py`
- **Checks:** 6 offline unit tests verifying classification rules:
  - Identity derivations pass as `REACHABLE`
  - Target-absent fields fail as `UNREACHABLE-TARGET-ABSENT`
  - Delimiters absent from method-visible text fail as `UNREACHABLE-CONVENTION-UNOBSERVABLE`
  - Delimiter-observability and required-field scans operate deterministically
- **Expected:** `6 passed`.

### Stage 2: Frozen Source Integrity Manifest
- **Manifest:** `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json`
- **Checks:** Re-hashes 134 frozen source code files, protocol descriptors, and evaluation assets.
- **Expected:** `file_count=134`, `UNCHANGED=134`, `CHANGED=0`, `MISSING=0`.

### Stage 3: Synthetic Oracle Reachability Audit (310 items)
- **Engine:** `research/gate19/auditor.py`
- **Information Rights:** `research/gate19/information_rights.json`
- **Dataset:** 310 synthetic argument-pair items across 12 drift families from the frozen V4/V4.1 benchmark generator.
- **Audited Metrics:**
  - Total items: **310**
  - `REACHABLE`: **260**
  - `UNREACHABLE-TARGET-ABSENT`: **10**
  - `UNREACHABLE-CONVENTION-UNOBSERVABLE`: **40** (30 in `argument_merge`, 10 in `tool_replacement`)
  - Overall unreachability rate: **16.1%** (50 / 310)
- **Key Drift Family Breakdowns:**
  - `argument_merge`: 0/30 reachable (100% unobservable convention failure)
  - `tool_replacement`: 15/35 reachable (10 target-absent, 10 unobservable convention)
  - `argument_split`: 40/40 reachable (100% reachable clean control)
- **Bit-Identical Check:**
  - Generated audit JSON is compared structurally and byte-for-byte against committed `gates/results/GATE_19_AUDIT.json`.
  - Windows CRLF SHA-256: `4ff5db197eb995ce0ec00de4e4c1a3f82cc7ad3193fa9785259bbc6e289c7d22`
  - Normalized LF SHA-256: `8035322329d129621786f6cbcad7940bca9df2cbf86126ff0e78441942917c69`
  - Result: **Bit-identical match on all 310 items**.

### Stage 4: Real-Version MCP Negative Control (Path B, 20 pairs)
- **Engine:** `research/gate19/external_audit.py`
- **Register:** `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json`
- **Checks:** 20 hand-verified parent/new MCP version pairs from official MCP servers.
- **Audited Metrics:**
  - Total pairs: **20**
  - `REACHABLE`: **20** (100%)
  - `UNREACHABLE`: **0**
- **Bit-Identical Check:**
  - Matched against committed `gates/results/GATE_19_EXTERNAL_AUDIT.json`.
  - Windows CRLF SHA-256: `412ec8edf0aac7cfcd1c54041068baa0cfa72461f0fe8eceb159f5d35a972b0a`
  - Normalized LF SHA-256: `4bf62df3273e970b8a1c97a8e2cb927bb17454228fe13904dd30a7d5b43da49b`
  - Result: **Bit-identical match on all 20 pairs**.

---

## 4. Expected Console Output

When running `python scripts/reproduce.py`, you should observe output similar to:

```text
========================================================================
VIETRAGOPS / GATE 19 — INDEPENDENT REPRODUCIBILITY AUDIT
Paper: Unreachable Oracles: Ground-Truth Derivability in Synthetic
       Tool-Drift Benchmarks for LLM Agents (§8 Reproducibility)
========================================================================

[1/4] Running Gate 19 offline unit tests (research/gate19/tests.py)...
      -> PASS: All 6 offline unit tests passed successfully.

[2/4] Verifying frozen source hash manifest (134 files)...
      -> Files evaluated: 134
      -> Status counts: {'UNCHANGED': 134}
      -> PASS: 134/134 frozen input files UNCHANGED (bit-exact).

[3/4] Running Oracle Reachability Auditor on 310 synthetic pair items...
      -> Total items evaluated: 310
      -> REACHABLE: 260
      -> UNREACHABLE-TARGET-ABSENT: 10
      -> UNREACHABLE-CONVENTION-UNOBSERVABLE: 40
      -> argument_merge: 0/30 reachable, 30 convention-unobservable
      -> tool_replacement: 15/35 reachable, 10 target-absent, 10 convention-unobservable
      -> argument_split: 40/40 reachable (0 unreachable)
      -> PASS: Structural match — all 310 items and family metrics identical.
      -> Generated file SHA-256:  4ff5db197eb995ce0ec00de4e4c1a3f82cc7ad3193fa9785259bbc6e289c7d22
      -> Committed file SHA-256:  4ff5db197eb995ce0ec00de4e4c1a3f82cc7ad3193fa9785259bbc6e289c7d22
      -> Normalized LF SHA-256:  8035322329d129621786f6cbcad7940bca9df2cbf86126ff0e78441942917c69
      -> PASS: BIT-IDENTICAL with committed GATE_19_AUDIT.json (310/310 items).

[4/4] Running External MCP Version Pairs Audit (Path B negative control, 20 pairs)...
      -> PASS: Structural match — all 20 external MCP control pairs identical.
      -> External pairs evaluated: 20
      -> REACHABLE: 20
      -> UNREACHABLE: 0
      -> Generated file SHA-256:  412ec8edf0aac7cfcd1c54041068baa0cfa72461f0fe8eceb159f5d35a972b0a
      -> Committed file SHA-256:  412ec8edf0aac7cfcd1c54041068baa0cfa72461f0fe8eceb159f5d35a972b0a
      -> PASS: BIT-IDENTICAL with committed GATE_19_EXTERNAL_AUDIT.json (20/20 reachable).

========================================================================
REPRODUCIBILITY SUMMARY: ALL CHECKS PASSED (exit code 0)
  - 310 items: 260 reachable · 10 target-absent · 40 convention
  - 20 external MCP control pairs: 20 reachable · 0 unreachable
  - 134 frozen source files: 134 UNCHANGED
  - Bit-identical match: TRUE (both synthetic & external audits)
  - Total execution time: 7.49 seconds (< 5 minutes requirement)
========================================================================
```

---

## 5. Artifact Provenance Matrix

| Artifact | Role | Generating Gate | Commit SHA |
|---|---|---|---|
| `research/gate19/auditor.py` | Auditor engine | Gate 19 | `6adf136` |
| `research/gate19/information_rights.json` | Rights specification | Gate 19 | `b2fd2c0` |
| `gates/results/GATE_19_AUDIT.json` | 310 synthetic audit receipts | Gate 19 | `7410bc7` |
| `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json` | 134-file input manifest | Gate 19 | `a434d53` |
| `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json` | Path B 20-pair register | Gate 19 | `0c73b17` |
| `gates/results/GATE_19_EXTERNAL_AUDIT.json` | Path B audit receipts | Gate 19 | `c720ff2` |
| `gates/baselines/GATE_10_EVIDENCE_LEDGER.json` | Machine-readable claim ledger | Gate 10 | `653aa81` |
