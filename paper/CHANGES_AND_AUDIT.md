# Version 2: defect log and pre-submission audit

Prepared 2026-09-12 against manuscript version 1
(`paper/main.tex`, repository tag `gate10-paper-v1-20260911`).

This file records (1) every defect found in version 1 and what was done about
it, and (2) the audit of version 2 against the twelve failure categories the
owner specified. It is part of the provenance trail: a reviewer who wants to
know what was checked, and what was found, should be able to read it here
rather than take the manuscript's word for it.

---

## Part 1 — Defects found in version 1

Each item states the defect, the evidence that established it, and the fix.

### D1 — Citation error: missing co-author (severity: high)

**Defect.** Reference `dig2006api` was listed with a single author, Danny Dig.

**Evidence.** The published article's title page, read from the author-hosted
copy at `dig.cs.illinois.edu/papers/JSME_API_Evolution.pdf`, lists
**Danny Dig and Ralph Johnson**, both at the Department of Computer Science,
University of Illinois at Urbana-Champaign. The publisher DOI returned HTTP
403 to automated retrieval, which is why version 1's metadata check — which
resolved the DOI but could not read the record — did not catch it.

**Fix.** Author list corrected in the bibliography and in
`REFERENCES_VERIFIED.json`. The correction is also stated in the manuscript's
Appendix E, because a paper whose thesis is traceability should not silently
repair its own citation record.

**Related near-miss.** A web search for the same article surfaced two
conflicting figures for the share of breaking changes that are refactorings:
"over 80%" and "94%". The primary source states **over 80%**. The manuscript
quotes only that figure. Had the 94% been taken from the search summary, this
would have been a fabricated statistic with a real citation attached — the
exact failure mode of category 2.

### D2 — Unverified content claims about a cited work (severity: high)

**Defect.** Version 1 described `assidiqi2026referencefree` as injecting
controlled drift "using a known bijective inversion manifest" and as
"explicitly separating adaptation after the drift mapping is available from
autonomous detection plus adaptation". Version 1's Figure 2 additionally
placed an "IEEE normalization" row in the information-rights comparison,
asserting specific values for that system's old-trace, migration-map, and
probing rights.

**Evidence.** `REFERENCES_VERIFIED.json` v1 recorded only that the DOI
resolved and the indexed metadata matched. No primary reading of the abstract
or full text is recorded anywhere. Retrieval was attempted again during this
revision: IEEE Xplore returned no content to automated fetch, and a targeted
search surfaced no accessible primary copy.

**Fix.** Both prose claims removed. The figure row removed rather than kept
with a hedge — an unverified row in a comparison table is load-bearing whether
or not a caveat sits beneath it. The work is now cited at the level its title
and indexed metadata support. The verification limit is stated in
Appendix E of the manuscript, not buried in a JSON file.

### D3 — Mixed denominators in a single clause (severity: medium)

**Defect.** Version 1's Contribution 1 read: "independently reproduces the
10/35 target-absent and 5/15 hidden-convention findings." The two fractions
have different units. 10/35 counts **argument-pair items**; 5/15 counts
**graded cases**. A reader could reasonably infer that 15 of something was the
denominator for both, or that 5/15 was a subset of 35.

**Evidence.** Ledger claims C043 ("10/35 target-absent *tool_replacement pair
findings*") and C044 ("5/15 graded *tool_replacement cases*"). The C2 family
table in `GATE_19C_RESULT.md` records 10 convention-unobservable **pair items**
in that family, not 5 — a third number that the same sentence could be
mistaken for.

**Fix.** Section 3.1 of version 2 defines graded case, argument-pair item, and
required-field item explicitly before any result appears, and every count in
the manuscript names its unit. The two findings are now stated separately.

### D4 — Broken internal promise (severity: medium)

**Defect.** Version 1's body read "commit `653aa81` (full SHA in the
reproducibility appendix)", but the appendix listed short SHAs only. The
promised full hashes appeared nowhere in the document.

**Fix.** Appendix C of version 2 gives the full 40-character commit hash for
every cited artifact.

### D5 — Inconsistent commit identifier (severity: low)

**Defect.** `research/gate19/auditor.py` was cited as commit `6adf136b` in the
body and `6adf136` in the appendix table — 8 hex characters in one place, 7 in
the other, for the same object.

**Fix.** All commit identifiers in version 2 are full 40-character hashes,
verified with `git log -1 --format=%H -- <path>` for each file.

### D6 — A propagated hash transcription error (severity: medium)

**Defect.** `GATE_19_RESULT.md` section O0 records the SHA-256 of
`GATE_19_FROZEN_SOURCE_HASHES.json` as `...5e55b8e2eb...`. The committed file
digests to `...5e55e8d2eb...`. Two characters are transposed in the prose
summary. The ledger record C045 and `GATE_19C_RESULT.md` both carry the
correct value, so the repository contains two different digests for one file.

**Evidence.** Digest computed directly over the committed file:
`e2e7ed915e55e8d2eb57378a3b53ebf106bc8d3c4141c7b6791d652c5c86e115`.

**Fix.** The manuscript cites the verified digest and records the discrepancy
explicitly in Appendix C. A traceability scheme that tolerates an unexplained
hash mismatch is not doing the job it claims to do, so this is stated rather
than quietly resolved. Recorded as `V02` in `EVIDENCE_LEDGER_ADDENDUM.json`.

### D7 — A caveat lost between artifact and manuscript (severity: medium)

**Defect.** `GATE_19C_RESULT.md` states under Limitations: "The power
calculation is a planning analysis over retained argument-pair item counts,
while first-attempt execution is case-level; this mismatch is reported
explicitly." Version 1 of the manuscript did not carry that limitation.

**Why it matters.** This is the classic multi-agent summarisation failure: a
caveat present in the source artifact is dropped when the result is written up,
and the write-up then reads as more confident than the evidence. Here the
omission was in the paper's favour in one direction and against it in another,
which is precisely why it needed stating rather than judging.

**Fix.** Section 7.2 of version 2 states the unit mismatch, and states which
way it cuts: because case-level retention is strictly lower than item-level
retention on the affected families, the mismatch makes the cancellation
decision more conservative, not less.

### D8 — Under-reported second measurement surface (severity: medium)

**Defect.** Version 1 mentioned the required-field audit only through its
consequence (0/15 strict complete-call retention) and never gave its totals.
The audit covers 45 items and finds 20 of them unreachable — a second,
independent defect surface with its own denominator.

**Fix.** Section 5.2 of version 2 reports the required-field audit in full,
with per-family figures and the literal values involved. Recorded as `A01` in
`EVIDENCE_LEDGER_ADDENDUM.json`.

### D9 — Reproducibility detail omitted (severity: low)

**Defect.** Version 1 described the diagnostic probe without naming the model,
and described the power anchors without naming the baseline arms. Neither could
be reproduced or challenged from the manuscript alone.

**Fix.** Version 2 names the probe model
(`nvidia/nemotron-3-super-120b-a12b:free`), its rate governor (3.2 s minimum
interval, 19 rpm, no fallback, reasoning effort disabled, 60-request budget),
and the four baseline arms with their model identifiers
(`llm_old_new_history` on `openai/gpt-oss-120b`, `llm_reasoning` on
`openai/gpt-oss-20b`, `lexical_name` deterministic offline). Recorded as `A04`
and `A05`.

### D10 — Selective omission of an inconvenient number (severity: medium)

**Defect.** The diagnostic probe has two strata. Version 1 reported the
`::` emission rate for both (0/28 and 0/29) and omitted the exact-gold rate,
which is 0.0000 in the hidden-sandbox stratum but **0.1379 (4 of 29)** in the
arbitrary-separator stratum. The omitted number is the only figure in the
probe that complicates a clean null reading.

**Why it was omitted.** Not, as far as we can tell, deliberately: the frozen
Gate 10 ledger has no record for it, and the ledger's own policy says any
number without a record must be removed before commit. The rule designed to
prevent fabrication also, in this one case, removed a true and relevant
observation.

**Fix.** Version 2 reports it, notes that 0.1379 sits close to the
pre-registered chance baseline of 1/9 = 0.1111, and states that n = 29 cannot
distinguish the two. The ledger is extended rather than the number dropped.
Recorded as `A02`.

### D11 — Bitmap figures with unreadable provenance (severity: low)

**Defect.** Version 1 shipped three PNG figures generated by a script. The
values inside them could not be read from the manuscript source, the
information-rights figure contained the unverified row described in D2, and a
raster figure in a preprint is a known submission hazard.

**Fix.** Version 2 renders every figure natively in LaTeX/TikZ. The source has
no external image dependency, and every value in every figure is readable as
text in `main.tex`. Recorded as `V05`.

---

## Part 2 — Version 2 audit against the twelve failure categories

### 1. Factual errors

Every numeric claim was read from its committed artifact during this revision
rather than carried over from version 1's prose. The per-family reachability
table was re-derived independently from the machine-readable auditor output
(`GATE_19_AUDIT.json`) and cross-checked against the prose table in
`GATE_19C_RESULT.md`; all figures match (`V01`). Arithmetic checks performed:
310 designed pairs sum across families; 260 reachable sum across families;
50 = 10 target-absent + 40 convention-unobservable; 50/310 = 16.1%;
45 = 15 + 5 + 25 required-field items; 146 = 99 + 30 + 17 hash inventory;
85 = 17 baseline arms x 5 affected cases; 57 = 28 + 29 valid JSON outputs;
p_bar values reproduce from the arm rates; the pooled p_bar reproduces as a
retained-n weighted mean.

No date, dataset name, or sample size is stated that is not in a cited
artifact. No third-party result is restated as our own.

### 2. Citation not supporting the claim

Every reference was re-checked at two levels: bibliographic metadata, and the
specific statement the manuscript makes about it. Seven of nine were verified
at both levels by reading the primary abstract or full text. Two carry a
narrower status and say so. One author list was corrected (D1). One set of
content claims was removed as unverified (D2).

Where the manuscript draws its own inference from a cited result — the
BigBag 78.6%-vs-33.3% transfer argument, and the observation about effect
scoring in DynamicMCPBench — the text marks it as the authors' analysis rather
than attributing it to the source.

### 3. Weak evidence synthesis

Related Work is organised by what each literature grants the evaluated system,
not by paper. Each subsection ends with the specific relationship to this
work: probing methods hold different rights (§2.1); schema-hiding relocates
the rights boundary rather than removing it (§2.2); effect scoring loosens the
path while reachability auditing validates the target (§2.3); source migration
holds information an agent scored before its first call does not (§2.4).
Disagreements are not manufactured; no cited work is described as wrong.

### 4. False novelty

The manuscript states in a boxed paragraph on page 1 what it does not claim.
MCPEvol-Bench is cited explicitly as preceding this work. The criterion is
described as adjacent to test-set validity, not as a replacement for it, and
what is claimed as new is narrowed to the operational parts: a declared rights
object, per-item derivability auditing, typed failure classes, a fail-closed
rule, and a committed implementation. The words "first", "novel",
"state-of-the-art" and "outperforms" do not appear as claims anywhere in the
manuscript.

### 5. Logic and argumentation

The central negative result is stated as a design decision, not a null
finding: no comparison ran, so no equivalence is claimed. The three-way
distinction between derivability, semantic correctness, and capability is
stated explicitly in §3.3, and the criterion is described as necessary but not
sufficient. The asymmetry between `argument_split` (clean) and
`argument_merge` (wholly unreachable) is explained by a mechanism — the
delimiter is present in the observed value for splitting and absent for
joining — rather than reported as a bare contrast.

The one place where a causal story was previously asserted (the RISK-0022
mechanism claim) is now the subject of §5.5, which shows the story was wrong
and replaces it with the scorer-granularity explanation the raw rows support.

### 6. Methodology and reproducibility

The manuscript states: the declared information rights and their four granted
artifacts; the eight excluded artifact classes; the three derivation rules; the
fail-closed rule; the three auditor statuses and the order in which checks are
applied; the exclusion policy and its additive nature; the probe's model, rate
governor, budget, and reasoning setting; the four baseline arms and their model
identifiers; the frozen statistical decision rule with alpha, target power,
and effect size; and the hash-manifest verification at both gate closures.

Pre-registration is documented: the criterion and exclusion policy were frozen
in one gate, the power rule in the next, before any power number was computed.

### 7. Statistics

MDE is defined where it first appears (smallest absolute arm difference
detectable at alpha = 0.05 with power 0.80 at the stated n). Absolute
differences are never described as relative. Wilson intervals are reported with
their full widths, and the observation that the zero-success interval at n = 15
is already wider than the entire pre-registered effect band is stated as the
decisive fact rather than the MDE table alone. The unit mismatch between the
pair-level power analysis and case-level execution scoring is disclosed (D7),
with its direction stated. No p-value is reported anywhere, and no result is
called "significant".

### 8. Internal inconsistency

Checked mechanically and by reading: the abstract's figures against the
results sections; the four contributions in §1.3 against the four objects in
the conclusion; every denominator against §3.1's definitions; every table
caption against its table; every figure caption against the values inside the
figure; every `\ref` resolved (final compile reports zero LaTeX warnings, so
no undefined or multiply-defined labels and no unresolved citations); every
`\cite` key present in the bibliography and every bibliography entry cited.

Acronyms and names are stable: the three statuses, the three item units, and
the family names use one spelling throughout.

### 9. Multi-agent error propagation

This was the most productive category. Four of the eleven defects above are
propagation failures rather than authoring failures: a caveat dropped between
artifact and write-up (D7); a hash transcribed wrongly in one artifact and
correctly in two others, with the manuscript free to pick either (D6); a
mechanism claim that survived in a risk register for weeks because nobody
re-read the rows (§5.5 of the manuscript); and a number omitted because a
well-intentioned rule required it (D10).

The countermeasure applied here is that no number was accepted from version 1's
prose. Each was re-read from the artifact the ledger names, and where two
artifacts disagreed, the file itself was hashed and the discrepancy recorded.

### 10. Writing

Every section opens on specific content. The manuscript opens on a concrete
register item with real values rather than on the state of the field. No
paragraph consists only of source summary. Filler transitions were removed.
Claims of the form "plays a crucial role" or "performs excellently" do not
appear. Hedging is calibrated: "we claim", "we do not claim", "this shows",
and "this does not show" are used deliberately and differently.

The conclusion does not paraphrase the abstract; it states what the audit cost
and what a benchmark author should do about it.

### 11. Scope and claims

Generalisation boundaries are stated four times: in the boxed paragraph on
page 1, in Contribution 3, in §5.3 on the control, and in §7.1. The
self-authored provenance of the benchmark is named as the central limitation
rather than listed among others. The self-audit problem — auditor, benchmark,
and corrected register all originating with the same authors — is stated in
§7.3, along with the observation that pre-registration and hash freezing do not
substitute for a second party running the auditor.

### 12. Document integrity

Compiled clean: 0 errors, 0 LaTeX warnings, 18 pages. All figures and tables
are referenced in the text. No placeholder text (`[REF]`, `[X%]`, `TODO`,
"insert figure here") remains; the one intentional placeholder is the author
block, which names itself as the owner's to supply. No meta-text from the
drafting process survives. No Markdown syntax leaked into the LaTeX. Citation
style is uniform. The bibliography has no duplicates. The one non-ASCII author
name is encoded as a LaTeX accent macro rather than a raw byte.

An AI-use disclosure appears as Appendix F, consistent with ICMJE and COPE
guidance that AI cannot be an author and that generative-AI use in manuscript
preparation should be disclosed.

---

## Part 2b — Hostile pre-submission self-audit of version 2

Version 2 was then audited again, this time against an arXiv-oriented hostile
review protocol rather than the twelve-category list. It found five further
defects in version 2 itself. They are recorded here because a paper arguing
for self-auditing should show what its own self-audit caught.

### S1 — Unearned "independently" (severity: high)

**Defect.** Contribution 1 read "Running the auditor independently reproduces
the two findings that originally motivated it", then gave both the 10/35
target-absent count and the 5/15 convention count.

**Evidence.** `research/gate08/metrics/diagnostics.py` contains an earlier
`oracle_reachability()` whose entire test is
`new_arg not in fields.get(new_tool, set())`. It detects the target-absent
class and nothing else. So two independent implementations do agree on 10/35 —
but the manuscript never told the reader that a prior implementation existed,
leaving "independently" with nothing to refer to. For the convention class the
word was simply wrong: the earlier diagnostic cannot detect it, and the 5/15
had been established by reading the sandbox source, not by an independent
check.

**Fix.** Contribution 1 now names the earlier diagnostic, states what it can
and cannot detect, and separates the two claims: agreement between two
implementations on the first class, mechanisation of the second. Recorded as
`A09`.

### S2 — The generator was never described (severity: high)

**Defect.** The paper's central argument is that a *generator* produced
unreachable oracles, yet Section 4.2 described the sandbox only as
"self-authored and deterministic". A reader could not tell whether the 50
failures were systematic generator behaviour or scattered authoring slips —
which is exactly what determines how much the result means.

**Evidence.** `research/gate07/dataset/operators.py` is a 291-line operator
library with `GENERATOR_SEED = 20260827`, `GRADED_PER_FAMILY = 15`, and
`HELD_OUT_PER_FAMILY = 3`. The held-out split existed and was never mentioned,
despite train/test separation being a standard methodology checkpoint.

**Fix.** Section 4.2 now states the generator, the seed, the per-family counts,
the held-out split, and quotes the sandbox code path that produces the `::`
separator. This strengthens the result rather than weakening it: the failures
are the systematic output of two mutation operators, which is why they cluster
perfectly instead of appearing at low rates everywhere. Recorded as `A08`.

### S3 — "Perfectly clean" contradicted by a table on the same page (severity: medium)

**Defect.** Section 5.1 said "nine of eleven families are perfectly clean"
while Table 2's rightmost column, directly above, showed
`added_required_field` retaining 0 of 15 strict cases.

**Fix.** The sentence now says "on this surface nine of eleven families are
clean", states explicitly that clean-on-this-surface is not clean, and
forward-references Section 5.2.

### S4 — The total row mixed denominators (severity: medium)

**Defect.** Table 2's total row gave 180 graded cases (12 families) alongside
310 pair items (11 families). In a paper whose stated thesis includes unit
discipline, that is an unforced error.

**Fix.** The row is now labelled "Total (11 pair families)" with 165 cases, so
every column in it refers to the same population; the caption states the
12-family, 180-case totals separately.

### S5 — A recommendation presented as a finding (severity: low)

**Defect.** Section 5.4 called the suggestion that benchmarks publish their
correspondence register "a small, concrete finding". It is a recommendation
derived from one failed attempt on two releases.

**Fix.** It is now labelled a recommendation, with the basis stated.

### Also added, not defects

- **Statistical honesty about the power model.** Section 7.2 now states that a
  two-sample normal approximation is untrustworthy at $n=15$ with an observed
  rate of zero, and that the decision rests on the interval width rather than
  the MDE. The MDE table is presented as what the frozen rule computed, not as
  a valid approximation at these counts.
- **A re-run command.** Section 8 now gives the exact invocation of the
  auditor, which the manuscript previously described as re-runnable without
  saying how.
- **Three source files added to the provenance table**:
  `research/gate08/metrics/diagnostics.py`,
  `research/gate07/dataset/operators.py`, and
  `research/gate07/sandbox/operations.py`.

### Checked and found sound

Repository public and browsable; tag `gate10-paper-v1-20260911` present on the
remote and resolving to `ff5e2b15…`, matching the manuscript. Abstract 244
words / 1649 characters, inside arXiv's 1920-character metadata limit. Every
abstract and conclusion claim traced to a Results subsection; none stronger
than its evidence. Citations and bibliography match in both directions. No
undefined references, no orphaned labels. Sentence-length distribution varied
(median 18, range 4–68). No `Moreover`/`Furthermore`/`Additionally` filler. No
"novel", "unique", "SOTA", or "outperforms" used as a claim. arXiv's current
policy — significant text-to-text generative AI use must be reported, and AI
cannot be an author — is satisfied by Appendix F.

## Part 3 — What remains open

These are not defects; they are limits a reviewer should know about.

1. **`assidiqi2026referencefree` content is unverified.** If the full text
   becomes available, §2.2 and Table 1 can be extended. Until then no content
   claim should be reinstated.
2. **No independent reproduction.** The auditor has not been run by anyone
   outside the project. This is stated in §7.3 and is the single most valuable
   thing a reader could do with the artifact.
3. **Author block is a placeholder.** Names, affiliations, ORCIDs, and the
   corresponding author must be supplied before submission.
4. **No licence is asserted in the source.** The arXiv licence choice is
   irrevocable per version and is the owner's decision; see
   `ARXIV_CHECKLIST.md`.
5. **Two references were verified from abstracts, not full text**
   (`chen2025toolevo`, `wu2026contda`). The manuscript's claims about them are
   confined to what those abstracts state directly.
