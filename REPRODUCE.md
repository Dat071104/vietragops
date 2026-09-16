# Independent Reproduction Guide (REPRODUCE.md)

**Paper:** *Unreachable Oracles: Auditing Ground-Truth Derivability in a Synthetic Tool-Drift Benchmark for LLM Agents*
**Section reference:** §8 (*Reproducibility and Traceability*)
**Manuscript artifact tag:** `gate22-paper-v31-20260916`
**Measurement evidence freeze:** `gate10-paper-v1-20260911`
**Evidence ledger:** `gates/baselines/GATE_10_EVIDENCE_LEDGER.json` (commit `653aa81`)

---

## 1. What this reproduces, and what it does not

The auditor is offline and deterministic. It needs no network, no API key, no
GPU, no virtual environment, and no third-party package — only the Python
standard library and this repository's own modules.

Read this section before running anything, because a clone of this repository
cannot check everything the harness names.

| Stage | Reproduces from a bare clone? |
|---|---|
| 1 — auditor unit tests | **Yes**, all 10 pass |
| 2 — frozen input manifest | **Partially.** 47 of 134 entries; see below |
| 3 — 310-item synthetic audit | **Yes**, byte-identical |
| 4 — 20-pair external sample | **Yes**, byte-identical |
| 5 — four-configuration rule ablation | **Yes**, structurally identical |

**The stage 2 limitation.** The frozen manifest
`gates/results/GATE_19_FROZEN_SOURCE_HASHES.json` has 134 entries. 87 of them
are the raw Gate 07 and Gate 08 measurement archive under `gates/artifacts/` —
roughly 107 MB of request ledgers, per-item traces, offline retrieval runs, and
router state. `gates/artifacts/.gitignore` excludes that directory, so it has
never been committed and is carried by no tag. A clone holds the other 47
entries and not those.

The harness does not paper over this. It verifies the 47, reports the 87 as
`NOT VERIFIED` with the reason, and prints `PASS (PARTIAL)` for stage 2 and
`ALL AVAILABLE CHECKS PASSED` in the summary. Pass `--require-full-manifest` to
turn the absence into a failure instead; that is the mode to use in a working
tree that does hold the archive.

**No reachability number depends on the undistributed archive.** The 310-item
register is rebuilt by the committed generator (`build_gate07_items()`), not
read from `gates/artifacts/`. Stages 3, 4, and 5 are therefore fully
reproducible from a bare clone, and those are the stages that carry the
paper's results. The archive matters only if you want the frozen *input*
manifest checked end to end. It is available from the authors on request.

---

## 2. Quick start

```bash
git clone https://github.com/Dat071104/vietragops.git
cd vietragops
git checkout gate22-paper-v31-20260916
python scripts/reproduce.py
```

`scripts/reproduce.py` and `scripts/reproduce_audit.py` are the same entry
point. Expect roughly 15 seconds and **exit code 0**.

```bash
python scripts/reproduce_audit.py --require-full-manifest   # strict stage 2
```

---

## 3. Byte-exactness and line endings

Several artifacts have their SHA-256 asserted inside another committed
artifact. If a checkout rewrites their line endings, a published hash stops
matching and the harness fails through no fault of the reader. This bit the
repository in practice: before `.gitattributes` existed, cloning on Windows
with the Git-for-Windows default `core.autocrlf=true` broke stage 2 and the
stage 4 `register_sha256` comparison, and the repository verified only on the
machine that produced it.

`.gitattributes` (commit `773d54b`) therefore pins exactly 48 paths with
`-text`, disabling end-of-line conversion in both directions:

- the 47 tracked entries of the frozen input manifest, and
- `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json`, whose SHA-256 is recorded
  as `register_sha256` inside `gates/results/GATE_19_EXTERNAL_AUDIT.json`.

Nothing else in the repository changes handling. A blanket policy was rejected:
191 of 602 tracked files hold CRLF on disk against an LF blob and would all
have been rewritten by one.

**A defect this exposed.** Eight frozen Gate 07 and Gate 08 protocol artifacts
had been normalised to LF by Git at an earlier commit, so their committed blob
no longer hashed to the value the frozen manifest records for them. For
`GATE_07_PROTOCOL_V2.json` the original mixed endings (389 CRLF and 4 bare LF)
cannot be reconstructed from the blob by any `eol` setting. Their bytes were
restored to the form the manifest was taken over. The measurement content is
untouched: for each of the eight, the parsed JSON before and after is identical
and the only difference is line endings. **The manifest itself was not edited** —
the artifacts were moved back to it, not it to them.

---

## 4. What each stage checks

### Stage 1 — auditor unit tests
`research/gate19/tests.py`, 10 offline tests. Beyond the original six
classification tests, four were added for manuscript version 3: rights
instantiation controls the visible surface; the headline is invariant under
rule ablation; `visible_literal` and `visible_split` are co-extensive on this
register; and the external sample is mostly hand-adjudicated.

### Stage 2 — frozen input manifest
`gates/results/GATE_19_FROZEN_SOURCE_HASHES.json`, SHA-256
`e2e7ed915e55e8d2eb57378a3b53ebf106bc8d3c4141c7b6791d652c5c86e115`.
Re-hashes every entry present in the working tree. Expected from a clone:
`{'MISSING': 87, 'UNCHANGED': 47}` and a partial pass. Expected in a tree that
holds the archive: `{'UNCHANGED': 134}`.

A file that is **present but altered** is always a failure, as is a file
missing from anywhere other than `gates/artifacts/`. Only the undistributed
archive is treated as partial.

### Stage 3 — synthetic oracle reachability audit (310 items)
Engine `research/gate19/auditor.py` (commit `6adf136`), rights
`research/gate19/information_rights.json` (commit `b2fd2c0`).

- Total items: **310**
- `REACHABLE`: **260**
- `UNREACHABLE-TARGET-ABSENT`: **10**
- `UNREACHABLE-CONVENTION-UNOBSERVABLE`: **40**
- Unreachability rate: **16.1 %** (50 / 310)
- `argument_merge` 0/30 reachable · `tool_replacement` 15/35 · `argument_split` 40/40

Compared against `gates/results/GATE_19_AUDIT.json` (commit `7410bc7`)
structurally and by SHA-256:

- file SHA-256 `4ff5db197eb995ce0ec00de4e4c1a3f82cc7ad3193fa9785259bbc6e289c7d22`
- LF-normalised `8035322329d129621786f6cbcad7940bca9df2cbf86126ff0e78441942917c69`

### Stage 4 — external MCP version pairs (20 pairs)
Engine `research/gate19/external_audit.py`, register
`gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json` (commit `0c73b17`).

20 REACHABLE, 0 UNREACHABLE — but read this as a **hand-adjudicated sample,
not a negative control**. 15 of the 20 are admitted by a hand-supplied
observability annotation produced by the same adjudication pass; only 5 pass
mechanically, and three of those have the new tool's own registered name as the
target value. With the annotation withheld the result is 5 REACHABLE and 15
fail-closed. Manuscript version 2 described this as a negative control and
version 3 withdrew that reading.

Compared against `gates/results/GATE_19_EXTERNAL_AUDIT.json` (commit `c720ff2`),
SHA-256 `412ec8edf0aac7cfcd1c54041068baa0cfa72461f0fe8eceb159f5d35a972b0a`.

### Stage 5 — rule-ablation invariance
`research/gate19/ablation.py`, compared against
`gates/results/GATE_22_RULE_ABLATION.json`.

Four grammar configurations — baseline, `visible_literal` removed,
`visible_split` evaluated first, and `visible_literal` scoped to source values
only — all return **260 / 10 / 40** with identical per-family counts. The
headline 50/310 does not depend on the rule the frozen rights file failed to
declare. The complete operative grammar is declared in
`research/gate19/derivation_grammar.json`; the frozen
`information_rights.json` was deliberately not edited.

---

## 5. Expected console output from a bare clone

```text
[1/5] Running Gate 19 offline unit tests (research/gate19/tests.py)...
      -> PASS: All 10 offline unit tests passed successfully.

[2/5] Verifying frozen source hash manifest (134 files)...
      -> Files evaluated: 134
      -> Status counts: {'MISSING': 87, 'UNCHANGED': 47}
      -> PASS (PARTIAL): 47/47 distributed frozen input files UNCHANGED (bit-exact).
      -> NOT VERIFIED: 87 manifest entries under gates/artifacts/ are not present in this working tree.
      -> Those are the raw Gate 07/08 measurement archive (~107 MB),
      -> excluded from the repository by gates/artifacts/.gitignore
      -> and not carried by any tag, so a clone cannot check them.

[3/5] Running Oracle Reachability Auditor on 310 synthetic pair items...
      -> PASS: BIT-IDENTICAL with committed GATE_19_AUDIT.json (310/310 items).

[4/5] Running External MCP Version Pairs Audit (Path B hand-adjudicated sample, 20 pairs)...
      -> PASS: BIT-IDENTICAL with committed GATE_19_EXTERNAL_AUDIT.json (20/20 reachable).

[5/5] Running rule-ablation invariance check (4 variants over 310 items)...
      -> PASS: 50/310 invariant across all four rule configurations.

REPRODUCIBILITY SUMMARY: ALL AVAILABLE CHECKS PASSED (exit code 0)
  - stage 2 was PARTIAL: the measurement archive is not in this tree
  - frozen input manifest: 47/134 present, all UNCHANGED; 87 not distributed
```

In a working tree holding the archive, stage 2 instead reports
`PASS: 134/134 frozen input files UNCHANGED (bit-exact)` and the summary reads
`ALL CHECKS PASSED`.

---

## 6. Artifact provenance

| Artifact | Role | Commit | SHA-256 (prefix) |
|---|---|---|---|
| `research/gate19/auditor.py` | auditor engine | `6adf136` | `4be5a726dce0b881` |
| `research/gate19/information_rights.json` | frozen rights declaration | `b2fd2c0` | `a6dedc5211fc4a2a` |
| `research/gate19/derivation_grammar.json` | complete operative grammar | `cfba18c` | `c41647b1da1be2a1` |
| `research/gate19/ablation.py` | rule-ablation harness | `cfba18c` | `4c392d4d614fbc3c` |
| `gates/results/GATE_19_AUDIT.json` | 310 synthetic receipts | `7410bc7` | `4ff5db197eb995ce` |
| `gates/results/GATE_19_FROZEN_SOURCE_HASHES.json` | 134-entry input manifest | `a434d53` | `e2e7ed915e55e8d2` |
| `gates/baselines/GATE_19_EXTERNAL_MCP_PAIRS.json` | 20-pair register | `0c73b17` | `bcb05f2f2c1d08a6` |
| `gates/results/GATE_19_EXTERNAL_AUDIT.json` | external receipts | `c720ff2` | `412ec8edf0aac7cf` |
| `gates/results/GATE_22_RULE_ABLATION.json` | ablation result | `cfba18c` | `6df91859eb6bd57c` |
| `gates/baselines/GATE_10_EVIDENCE_LEDGER.json` | claim ledger | `653aa81` | `d9ec96bedcd28c1b` |

---

## 7. Interpreting a failure

| Symptom | Meaning |
|---|---|
| Stage 2 `CHANGED` on any path | A distributed frozen input was altered. Real failure. |
| Stage 2 `MISSING` outside `gates/artifacts/` | A distributed file is absent. Real failure. |
| Stage 2 partial, 87 missing under `gates/artifacts/` | Expected in any clone. Not a failure. |
| Stage 3 or 4 byte mismatch | Check for a line-ending rewrite first: confirm `.gitattributes` is present and re-clone. |
| Stage 5 mismatch | The auditor or the ablation harness changed behaviour. Real failure. |
