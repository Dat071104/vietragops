# Unreachable Oracles — manuscript package, version 2

Rewritten 2026-09-12 from version 1 (`paper/main.tex` at repository tag
`gate10-paper-v1-20260911`).

## Contents

| File | What it is |
|---|---|
| `main.tex` | The manuscript. Single file, self-contained. |
| `CHANGES_AND_AUDIT.md` | Every defect found in version 1 and what was done about it, plus the audit of version 2 against twelve failure categories. Read this first if you want to know what was checked. |
| `EVIDENCE_LEDGER_ADDENDUM.json` | The seven numbers in this version that are not in the frozen Gate 10 ledger, each with source artifact, commit, SHA-256, and locator. Also five verification notes, including one integrity correction. |
| `REFERENCES_VERIFIED.json` | Per-reference verification record at two levels: bibliographic metadata, and the specific content claim the manuscript makes. Records one corrected author list and one reference whose content could not be verified. |
| `ARXIV_CHECKLIST.md` | Submission metadata and the owner decisions that remain open. |
| `main.pdf` | A reference build, so you can read the paper without compiling. **Not a source file** — do not upload it to arXiv or TeXpage; upload `main.tex`. |

## Building

`main.tex` is the top-level file. It needs no `.bib` file (the bibliography is
inline) and **no image files** — both figures are drawn in TikZ.

```
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Three passes resolve the `longtable` column widths and the cross-references.
Packages used are all standard: `geometry`, `fontenc`, `inputenc`, `lmodern`,
`microtype`, `amsmath`, `amssymb`, `array`, `booktabs`, `longtable`,
`tabularx`, `enumitem`, `xcolor`, `url`, `tikz` (with `arrows.meta` and
`positioning`), and `hyperref`.

Last verified build: 0 errors, 0 LaTeX warnings, 18 pages, pdfTeX via MiKTeX.

## What changed from version 1

Substantively, not cosmetically. The short version:

- **Six real defects fixed**, including a missing co-author on a citation, a
  set of content claims about a cited work that no primary source supported,
  and a hash that two repository artifacts disagree about.
- **Two omissions repaired**: a limitation that existed in the source artifact
  but not in the paper, and a probe statistic that was dropped because the
  frozen ledger had no record for it.
- **A whole measurement surface reported** that version 1 mentioned only
  through its consequence: the 45-item required-field audit, 20 of which are
  unreachable.
- **Figures moved from PNG to TikZ**, which removes the external dependency and
  makes every plotted value readable in the source. Version 1's third figure,
  the information-rights comparison, became a typeset table — and lost the row
  that asserted unverified properties of a cited system.
- **Three appendices added**: the full 35-row register so the counts can be
  checked by hand, the claim ledger, and an AI-use disclosure.

`CHANGES_AND_AUDIT.md` has the detail, with evidence for each.

## Before submitting

Five things are the owner's, not the manuscript's:

1. **Author block.** `main.tex` carries a placeholder that names itself as
   such. Names, affiliations, ORCIDs, and a corresponding author are needed.
   No AI system may be listed as an author.
2. **Licence.** The arXiv licence choice is irrevocable for that version.
3. **Categories.** `cs.SE` primary with `cs.CL` and `cs.AI` cross-lists is the
   recommendation; see `ARXIV_CHECKLIST.md` for the reasoning and the
   alternative.
4. **Endorsement**, if arXiv asks for it on a first submission.
5. **Submission itself.** Nothing in this package submits anything.

## A note on the numbers

Every numeric claim in the manuscript carries a superscript key into a ledger
record that names the artifact, its commit, its SHA-256, and the locator inside
it. During this revision, no number was carried over from version 1's prose;
each was re-read from the artifact. Where two repository artifacts disagreed
about a value, the file was hashed directly and the discrepancy recorded rather
than resolved silently — see `V02` in the addendum.

This is deliberate. A paper arguing that benchmark authors should audit their
own ground truth has no standing if its own figures are taken on trust.
