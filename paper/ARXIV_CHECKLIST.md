# arXiv Preparation Checklist

Prepared: 2026-09-11. Submission is not authorized by Gate 10 and must remain
the owner's separate action.

## Recommended metadata

- Title: `Unreachable Oracles: Ground-Truth Derivability in Synthetic Tool-Drift Benchmarks for LLM Agents`
- Abstract: the 183-word abstract in `main.tex`; copy it exactly into arXiv metadata.
- Authors: owner must supply the final author list, affiliations, email addresses, and ORCID identifiers. No author has been invented in the source.
- Primary category: `cs.SE` (Software Engineering), because the central claim is benchmark validity, testing/auditing, and API/software-evolution measurement.
- Cross-lists: `cs.CL` (Computation and Language) for LLM-agent/tool-use readership and `cs.AI` (Artificial Intelligence) for agent evaluation and planning context.
- Alternative: use `cs.CL` as primary if the owner wants NLP/LLM review context to dominate; this does not change the paper's scope or claims.
- ACM/MSC classification: not required for this paper; leave blank unless the owner has a venue-specific reason to add one.
- Comments field: `Measurement and benchmark-validity preprint; artifact commit 4da7371fe7d414ba0e4f0064983c71e8c458fa8a.`
- Artifact URL: `https://github.com/Dat071104/vietragops`
- License recommendation: `CC BY 4.0`, subject to the authors' funder and future-journal checks.

## Endorsement

arXiv's current endorsement page says endorsement is required before a user's
first paper or a submission to a new category. An institutional email can
expedite the process; without one, the submitting author may seek personal
endorsement from an established arXiv author. One positive endorsement is
required per endorsement category. The endorser checks topical appropriateness;
endorsement is not peer review.

Process:

1. Register/verify the submitting author account and select the intended primary category.
2. Start a new submission to trigger the endorsement request if arXiv asks for it.
3. Use a related arXiv paper to identify a qualified endorser, preferably someone known personally and working in the subject area.
4. Send the six-character endorsement code through the arXiv form; do not mass-contact potential endorsers.
5. Repeat for any additional category that requires a separate endorsement.

Official source: <https://info.arxiv.org/help/endorsement.html>.

## License rationale

CC BY 4.0 is recommended because the paper, figures, criterion description,
and auditor-facing documentation are intended to be reused with attribution.
It permits redistribution, adaptation, and commercial reuse. The submitting
author must own or control the rights, confirm funder/journal compatibility, and
understand that the arXiv license choice is irrevocable for that version. If
the owner wants to reserve commercial or derivative-work restrictions, select a
different arXiv option deliberately rather than assuming CC BY can later be
changed.

Official source: <https://info.arxiv.org/help/license/index.html>.

## Upload checklist

- [ ] Replace the author placeholder in `main.tex`.
- [ ] Confirm title and the 183-word abstract match the metadata exactly.
- [ ] Select `cs.SE` primary, `cs.CL` and `cs.AI` cross-lists, or record the owner's approved alternative.
- [x] Confirm the paper-package commit: `4da7371fe7d414ba0e4f0064983c71e8c458fa8a`.
- [ ] Confirm `CC BY 4.0` or record the owner's approved license.
- [ ] Upload `main.tex`, `figures/*.png`, and any required source files; do not upload private/raw artifacts.
- [ ] Use arXiv's `Check Files` step and verify the detected top-level TeX file is `main.tex`.
- [ ] Verify figure file names and case exactly; PDFLaTeX-compatible PNG files are present.
- [ ] Review the generated PDF, title, abstract, authors, categories, license, comments, and artifact URL.
- [ ] Complete endorsement if arXiv requests it.
- [ ] Submit only after a separate owner approval. Gate 10 does not submit.

Official submission guidance: <https://info.arxiv.org/help/submit/index.html>.
The taxonomy entries used for category selection are `cs.SE`, `cs.CL`, and
`cs.AI`: <https://arxiv.org/category_taxonomy>.
