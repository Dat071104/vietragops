# Gate 10 paper source

The portable source is `main.tex`. It contains the bibliography inline and uses
only standard LaTeX packages plus the three PNG figures in `figures/`.

The figures are generated from the committed Gate 10 evidence ledger by:

```powershell
.venv\Scripts\python.exe make_figures.py
```

For a local PDF check, run from this directory:

```powershell
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The Gate 10 workflow does not require a local LaTeX build. The source is the
authoritative paper artifact; generated auxiliary files and PDFs should remain
outside the repository unless the owner separately requests a release PDF.

`REFERENCES_VERIFIED.json` records the related-work metadata and URL checks.
`ADVERSARIAL_REVIEW.md` records the hostile self-review and its resolutions.
`ARXIV_CHECKLIST.md` prepares submission metadata and explicitly does not submit.
