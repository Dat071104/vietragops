# Gate 02 Execution Prompt

Copy everything below into one new Luna implementation session. This session
executes Gate 02 only and stops after its result.

## Mission

Add a narrow, local, validated-document-to-canonical-Markdown path using
MarkItDown for candidate documents. Preserve original artifacts, preserve the
existing pypdf loader as an explicit fallback, and keep candidate content out of
live RAG until the existing review/publish transition.

Working directory:

    D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps

Gate 01 was recorded as PASS at commit df5d84c. This is historical context, not
permission to skip verification. Re-check all prerequisites before editing.

## Non-negotiable boundaries

- Execute Gate 02 only. Write the result, then STOP. Do not start Gate 03.
- Preserve the Gate 01 lifecycle: validated intake, immutable originals,
  registry, candidate-only processing, review, atomic publish/retire/rollback.
- Do not read, print, copy, log, commit, or request values from .env or any
  credential handoff file.
- Do not call Firecrawl, Groq, any live provider, OCR/cloud service, URL
  conversion, or network-dependent feature.
- Do not expose a MarkItDown MCP server, a public conversion endpoint, or an
  arbitrary file://, http://, or https:// conversion input.
- Do not let caller-provided filenames or paths reach MarkItDown as a path.
- Do not silently import MarkItDown from external_tools, mutate that checkout,
  or stage it as application code.
- Do not enable OCR, plugins, LLM clients, cloud/document-intelligence
  endpoints, or optional remote converters.
- Do not reset, restore, clean, stash, amend, rebase, or absorb pre-existing
  dirty files. Do not use git add .
- Do not add Qdrant, Postgres, a queue, a worker system, Docker redesign, or a
  parser framework. This is a small local adapter-and-pipeline gate.
- Use ordinary descriptive commit messages with no tool or agent branding.
  Never push.

## Gate 02 success definition

PASS requires current evidence that:

1. validated PDF candidates can follow:

       immutable original
       -> MarkItDown local conversion
       -> canonical Markdown
       -> existing Markdown loader/section builder/chunker
       -> isolated candidate artifacts/index

2. the original and canonical Markdown are linked by checksums and durable
   extraction telemetry;
3. malformed, scanned/no-text, empty, or conversion-failed candidates cannot
   be reviewed or published;
4. the legacy PDF loader remains available through an explicit fallback policy;
5. DOCX is enabled only if its fixture passes. PPTX and XLSX remain unsupported
   in this Gate unless each is separately validated, integrated, and tested;
6. existing-corpus RAG regression remains unchanged; and
7. gates/results/GATE_02_RESULT.md is written, then the session stops.

Do not claim visual or layout fidelity. Record factual extraction measures and
warnings only.

## Start-up and prerequisite verification

1. Run:

       .\.venv\Scripts\python.exe _agent_ops/tools/session_start.py --root .

2. Read, in this order:

       AGENTS.md
       PROJECT_STATE.md
       _agent_ops/SESSION_BRIEF.md
       _agent_ops/OPERATING_RULES.md
       _agent_ops/CURRENT_TASK.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/README.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/EVOLVE_MASTER_CONTEXT.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_02.md
       gates/results/GATE_00_RESULT.md
       gates/results/GATE_01_RESULT.md
       gates/baselines/GATE_00_BASELINE.json
       gates/baselines/GATE_01_RETRIEVAL_SMOKE.json
       _agent_ops/THIRD_PARTY_TOOLING.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\gates\GATE_02_MARKITDOWN_FAST_MODE.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\03_AGENT_OPERATING_CONTRACT.md

3. Before editing, independently prove:

   - Gate 00 and Gate 01 result files explicitly say PASS.
   - The Gate 01 result commit df5d84c is reachable.
   - Any commits after that point are understood, non-behavioral handoff
     documents, or explicitly scoped Gate 02 work. Do not treat HEAD alone as
     the Gate 01 baseline.
   - The documented pre-existing dirty overlay is still present and unchanged.
     Compare status inventory and the recorded safe SHA-256 of the modified
     tracked file. Do not normalize it or stage it.
   - The Git index is empty before your first edit.

   If any prerequisite or overlay identity is ambiguous, write a BLOCKED Gate
   02 result with evidence and stop. Do not repair Gate 00 or Gate 01 inside
   this session.

4. Read the current candidate pipeline, lifecycle service/registry, intake
   allowlist, PDF/DOCX loaders, and relevant tests. Read _agent_ops/REPO_MAP.md
   first; it may be stale after Gate 01, so use it only as a lead. Confirm code
   paths by reading the actual files before concluding.

5. Use the project interpreter for every application command:

       .\.venv\Scripts\python.exe

   Do not use the global Python interpreter for test claims.

6. Maintain _agent_ops/CURRENT_TASK.md throughout the task. Record files,
   commands, failed attempts, decision points, and evidence; never put secrets
   or raw document contents in it.

## Team use

Use one writer and work sequentially. Adapter setup, candidate integration,
quality evidence, and final regression share one state model.

At most two read-only audits are allowed:

- after Phase 2.2: inspect the adapter boundary for path/URI/plugin/network
  escape and candidate/live isolation; and
- before the result: inspect fallback semantics, failure-to-publish proof, and
  acceptance-test coverage.

If an Antigravity review is available and project-context transfer is explicitly
approved by the platform, give it a two-turn read-only audit. It must not read
.env, credentials, raw corpus content, or private documents; edit files; call
network/provider tools; modify Git; or write result/ops files. Its output is
advisory only. Independently verify every load-bearing claim locally. If the
tool is unavailable, blocked, or unauthenticated, record AGY_UNAVAILABLE once
and continue without retries.

## Phase 2.0 — Freeze the handoff and complete the minimal runtime setup

Facts to verify:

- External MarkItDown provenance is revision
  9dc0d6579b8739c9d0671ff205e071e3053c7df1, version 0.1.7.
- Its isolated external venv is a preparation/provenance environment only.
- At prompt creation, the application .venv does not import markitdown and
  requirements.txt does not list it. Treat this as a setup task for Gate 02.

Checklist:

- [ ] Verify the external checkout revision and clean status without modifying
      it or reading any secret file.
- [ ] Add one explicit, pinned application dependency for version 0.1.7 with
      only the PDF and DOCX extras required by the enabled Gate 02 scope.
      Do not install PPTX/XLSX extras or reformat/upgrade unrelated requirements
      unless this Gate explicitly expands to those formats with full evidence.
- [ ] Install that exact dependency into the application .venv using normal,
      reproducible dependency handling. Do not solve it by adding external_tools
      to PYTHONPATH or by invoking its venv from production code.
- [ ] If a network install is unavailable, use a locally available distribution
      only when its pin/provenance exactly match the recorded external revision.
      Otherwise record BLOCKED; never silently bind runtime code to an arbitrary
      checkout path.
- [ ] Verify in the application .venv: import succeeds, installed version is
      0.1.7, the local conversion API is available, and pip check passes.
- [ ] Instantiate MarkItDown with plugins disabled. Do not configure an LLM
      client, endpoint, OCR plugin, or URL converter.
- [ ] Run the pre-edit compile and focused lifecycle test baseline using the
      project .venv, recording actual outcomes.

The dependency line and app-runtime validation are a small, legitimate Gate 02
setup change. Commit only after validation, for example:

    build(gate-02): add local markitdown runtime

Do not commit external_tools or generated package caches.

## Phase 2.1 — Add the narrow local adapter

Add one small adapter under the existing rag ownership, normally:

    rag/ingestion/markitdown.py

Create the minimal package marker only if required. Do not create a new
top-level ingestion tree or a generic conversion service.

The adapter must:

- accept a Path or binary stream only from a server-owned, already-validated
  original; never accept a raw URL, URI, caller path string, or file:// input;
- resolve and verify that a Path is a regular file under the configured
  lifecycle originals directory before conversion, rejecting symlink/path
  escape deterministically;
- call the narrow local or stream MarkItDown API only, with plugins disabled;
- never pass a URL argument or enable a remote/cloud conversion mode;
- return canonical Markdown text plus parser name/version and deterministic,
  non-secret warning/error information;
- distinguish conversion failure from successful empty/whitespace-only output;
  both are unusable conversion outcomes; and
- make no writes outside the caller-supplied candidate version directory.

Add focused tests for:

- allowed server-owned local input;
- outside-root and symlink/path escape rejection;
- file:// and URL-like input rejection;
- plugins disabled and no remote arguments;
- converter exception; and
- deterministic version/parser metadata.

Run compileall and focused tests. Commit only this adapter/setup phase, for
example:

    feat(gate-02): add local markdown adapter

## Phase 2.2 — Implement the canonical PDF candidate path

Integrate the adapter into the existing candidate pipeline without changing the
live retrieval path:

    validated PDF original
      -> MarkItDown local conversion
      -> candidate/version_id/canonical.md
      -> existing Markdown loader
      -> existing section builder
      -> existing chunker
      -> candidate/version_id/processed.jsonl and chunks_500.jsonl

Checklist:

- [ ] Preserve the Gate 01 immutable original unchanged.
- [ ] Write canonical.md atomically only under the candidate version directory.
- [ ] Compute SHA-256 for the original and canonical Markdown.
- [ ] Write a durable extraction record, linked from the version registry or
      another unambiguous durable registry-owned path. It must contain:
      parser name/version, pinned provenance, conversion duration, original and
      canonical checksums, character count, section count, deterministic table
      count, warnings, and conversion status.
- [ ] Do not overload an existing field ambiguously. Add the smallest
      backwards-compatible registry migration/field needed to locate canonical
      Markdown and its extraction record after restart.
- [ ] Reuse the existing Markdown loader, section detector, and chunker rather
      than duplicating Markdown parsing or chunking.
- [ ] A converter exception, empty/whitespace Markdown, scanned/no-text result,
      malformed input, no sections, or corrupt extraction record sets
      parse_status=failed and records a safe warning.
- [ ] Existing review and publish guards must reject that failed candidate.
- [ ] Candidate artifacts remain structurally unreachable from the live
      manifest/chunks/store before reviewed publish.

Fallback rule:

- Keep the pypdf loader implemented and testable.
- Keep one server-owned parser policy; do not expose parser choice to the
  caller. It may retain legacy pypdf during implementation, then select
  MarkItDown as the default PDF candidate parser only after Phase 2.4 comparison
  passes.
- Do not silently switch a failed MarkItDown candidate to pypdf and label it a
  MarkItDown success. A selected MarkItDown conversion failure is failed and
  cannot publish.
- The legacy loader remains an explicit, recorded fallback/parser policy for a
  separately processed candidate or configuration-controlled path. Every use of
  fallback must identify the actual parser and warnings in its extraction record.

Add integration tests for normal PDF conversion, malformed PDF, scanned/no-text
PDF, table-heavy PDF, canonical checksum linkage, candidate isolation, and
failed-candidate review/publish rejection.

Run focused tests plus the relevant Gate 01 lifecycle tests. Commit only this
validated phase, for example:

    feat(gate-02): convert pdf candidates to markdown

## Phase 2.3 — Bounded additional format support

PDF is mandatory. The only additional format to target in this Gate is DOCX,
because it is already validated by intake and has an existing local loader.

Checklist:

- [ ] Add a real, small DOCX fixture with local provenance and checksum.
      The application test suite must not require an untracked external checkout
      merely to locate a fixture.
- [ ] Convert it through the same local adapter to canonical Markdown, then the
      existing Markdown-to-sections/chunks path.
- [ ] Record the same checksum and extraction telemetry fields as PDF.
- [ ] Test a valid DOCX success case and one malformed/unusable DOCX failure
      case; failure must remain unreviewable/unpublishable.
- [ ] Compare its factual output measures with the existing DOCX loader where
      applicable. Do not claim formatting/layout equivalence.

Do not enable PPTX or XLSX merely because their extras are installed. Keep them
unsupported/rejected unless all of intake validation, fixture provenance,
conversion, candidate isolation, fallback policy, and tests are completed in
this same Gate. State exactly which formats are enabled in the result.

Run focused tests and relevant lifecycle tests. Commit only this bounded format
phase, for example:

    feat(gate-02): support docx markdown candidates

## Phase 2.4 — Extraction QA, comparison, and regression proof

Use a small, representative, reproducible fixture set:

- one normal PDF;
- one malformed PDF;
- one scanned/no-text PDF;
- one table-heavy PDF; and
- one DOCX fixture if DOCX is enabled.

If an upstream fixture is copied, record its source revision, relative source
path, license/provenance, and SHA-256 in a small fixture manifest. Do not add
large arbitrary documents, user documents, or unrelated corpus files. A fixture
must be local and tracked or deterministically generated so tests are portable.

For each successful conversion, record factual values:

- original checksum and canonical Markdown checksum;
- parser/package version and source revision;
- duration measured with a monotonic clock;
- character count, section count, and a documented deterministic table-count
  rule;
- warnings and parse status; and
- legacy-loader comparison values for the representative PDF/DOCX subset.

Quality rule:

- Compare factual output measures and content/section presence against the
  existing loader. Do not invent a quality score or claim high-fidelity layout.
- Retain legacy pypdf fallback unless current evidence justifies selecting
  MarkItDown for the PDF candidate path.
- If comparison shows the MarkItDown path is unusable for the required PDF
  fixture set, record FAIL or BLOCKED honestly. Do not weaken the fixture or
  hide the difference.

Run:

    .\.venv\Scripts\python.exe -m compileall -q app rag scripts evals frontend tests
    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe scripts/validate_chunks.py --chunks-dir data/chunks
    .\.venv\Scripts\python.exe scripts/validate_processed_docs.py data/processed/processed_docs.jsonl
    .\.venv\Scripts\python.exe scripts/verify_manifest.py data/manifests/documents_manifest.csv
    .\.venv\Scripts\python.exe -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever bm25 --top_k 5 --output gates/baselines/GATE_02_RETRIEVAL_SMOKE.json

Compare the retrieval count and metrics against Gate 01's smoke. A difference
must be investigated and recorded; do not overwrite the Gate 01 baseline or
claim equality without exact current evidence.

Commit QA tests/evidence only after they pass, for example:

    test(gate-02): verify markdown extraction quality

## Phase 2.5 — Result, commits, and STOP

Write:

    gates/results/GATE_02_RESULT.md

Use the required format:

    Status: PASS | FAIL | BLOCKED | WAITING_FOR_USER_SECRET
    Commit / tree state
    Phases completed
    Files changed
    Commands/tests executed
    Acceptance checklist
    Evidence artifacts
    Known issues
    Next allowed Gate
    STOP: No next-Gate work performed.

The result must state:

- exact app and external MarkItDown versions/revisions and how app dependency
  setup was validated;
- enabled formats and explicitly unsupported formats;
- adapter path boundary and plugin/network-disabled policy;
- canonical Markdown/telemetry storage and checksum linkage;
- fallback selection and conversion-failure behavior;
- fixture provenance and exact QA/comparison results;
- current test and retrieval-regression evidence;
- every unchecked acceptance item, if any; and
- only the next allowed Gate.

Update only the smallest authoritative state/decision records established in
earlier Gates. Do not create duplicate ledgers. Commit result/state files in a
separate final commit, for example:

    docs(gate-02): record markdown conversion result

For every commit:

1. stage exact file paths only;
2. inspect staged file names and staged diff;
3. run git diff --cached --check;
4. commit only after the relevant validation; and
5. run git status.

Never push. Do not start Gate 03, Firecrawl, MCP exposure, deployment, provider
work, or research work after the result.

## Final response format

Return a compact handoff with:

1. Gate status and reason.
2. Gate 01 prerequisite and pre-edit baseline/dirty-overlay verification.
3. Commit IDs and exact files in each commit.
4. Runtime setup proof and exact parser/fallback policy.
5. Fixtures, checksums, QA/comparison results, and failure-path proof.
6. Full regression and retrieval-smoke outcomes.
7. Every unchecked acceptance item, known limitation, and only next allowed
   action.

Do not claim PASS from dependency installation, a successful converter call, a
helper audit, or historical results. STOP after the handoff.
