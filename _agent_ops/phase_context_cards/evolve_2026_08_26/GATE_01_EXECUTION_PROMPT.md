# Gate 01 Execution Prompt

Copy everything below into a separate Luna implementation session. Do not paste
it into the Gate 00 session.

## Mission and prerequisite

Execute Gate 01 only: turn the current upload-only behavior into a governed
local document lifecycle with validated intake, durable provenance/version
records, candidate isolation, reviewed publish/retire, and rollback.

Working directory:

    D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps

Before any implementation, inspect:

    gates/results/GATE_00_RESULT.md
    gates/baselines/GATE_00_BASELINE.json

Proceed only when the Gate 00 result is explicitly PASS and the current
pre-edit tree still matches its recorded baseline identity, including any
recorded dirty overlay. If either artifact is missing, non-PASS, or no longer
matches, do not edit code. Report BLOCKED, name the mismatch, and stop. The only
allowed next action is a Gate 00 repair/re-freeze.

## Non-negotiable boundaries

- Run Gate 01 and nothing after it. Stop immediately after its result artifact.
- Keep the existing live RAG behavior intact until an explicitly reviewed
  publish transition. Candidate material must never change live answers.
- Preserve each original accepted artifact and its provenance.
- Do not read, print, copy, log, commit, or request secret values. Do not open
  .env or local credential handoff files.
- Do not use Firecrawl, MarkItDown, Groq, a live provider, Google Cloud, or
  any network-dependent feature. Locally installed tools and keys are not
  authorization for this gate.
- No unreviewed auto-publish. No arbitrary caller-provided filesystem path.
- No Qdrant, Postgres, remote store, queue, microservice, broad framework
  rewrite, dependency migration, or Docker redesign for appearance.
- Do not reset, restore, clean, stash, amend, rebase, or silently commit
  pre-existing changes. Do not use git add .
- Use ordinary, descriptive commit messages with no tool or agent branding.
  Never push.

## Start-up and evidence rules

1. Run:

       python _agent_ops/tools/session_start.py --root .

2. Read, in this order:

       AGENTS.md
       _agent_ops/SESSION_BRIEF.md
       _agent_ops/OPERATING_RULES.md
       _agent_ops/CURRENT_TASK.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/README.md
       _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_01.md
       _agent_ops/THIRD_PARTY_TOOLING.md
       gates/results/GATE_00_RESULT.md
       gates/baselines/GATE_00_BASELINE.json
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\gates\GATE_01_DOCUMENT_LIFECYCLE.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\03_AGENT_OPERATING_CONTRACT.md

3. Read _agent_ops/REPO_MAP.md before source discovery. Use the supplied
   explore tool to trace the upload route, configuration, retrieval store,
   current chunk artifacts, and existing tests before broad searching.

4. Update _agent_ops/CURRENT_TASK.md throughout the work. Record files touched,
   decisions, exact commands, test outcomes, and rejected alternatives. Never
   include secrets or document contents.

5. Keep one primary writer. Treat every result from a helper as a lead until
   independently verified in the local repository.

## Team use

Gate 01 source changes are sequential because intake, registry, candidate
processing, and publish transitions share one state model.

At most one read-only helper may audit the implementation after Phase 1.3 or
Phase 1.4. Its narrow task is to inspect:

- whether candidate storage/index paths can reach the live retrieval path; and
- whether publish, retire, rollback, and cache-refresh tests prove the intended
  invariant.

It must not edit files, run providers, inspect credentials, modify Git, or
write result artifacts. An Antigravity review is optional only when it is
available, authenticated, and explicitly permitted to receive project context.
If it is unavailable, blocked, or unauthenticated, record AGY_UNAVAILABLE once
and continue. Do not spend time reconfiguring it during this gate.

## Phase 1.0 — Verify the Gate 00 handoff and scope the smallest design

Checklist:

- [ ] Verify the Gate 00 PASS result and baseline identity before editing.
- [ ] Record canonical Git root, branch, HEAD, working-tree state, and any
      pre-existing changes.
- [ ] Locate the current upload-only route, raw-upload directory, document
      manifest, chunk/index store, and live retrieval cache behavior.
- [ ] Identify the current test style and run the relevant baseline smoke
      before changing behavior.
- [ ] Write a compact lifecycle decision: storage owner, registry format,
      candidate/live boundary, review transitions, publish atomicity, rollback,
      and cache refresh.

Choose the smallest local durable design that follows existing project
conventions. Prefer a standard-library or already-present local persistence
mechanism when it meets the requirements. A new server, database product, or
library is out of scope unless it is the only way to preserve a required
invariant; if so, stop with BLOCKED and explain why.

Do not create empty architecture folders or speculative abstractions.

## Phase 1.1 — Secure intake

Implement only the minimum intake contract needed for the existing document
route.

Checklist:

- [ ] Derive storage names from a server-owned identifier and approved extension;
      never use the caller filename as a filesystem path.
- [ ] Normalize to a basename and reject traversal, separators, empty names,
      reserved/unsafe names, and malformed extensions deterministically.
- [ ] Enforce a narrow extension and MIME allowlist. Do not rely on a filename
      alone; validate declared content type and use a cheap deterministic format
      check where available. If a format cannot be safely validated with the
      existing surface, reject it rather than add an early parser integration.
- [ ] Enforce a configurable bounded maximum size while receiving the upload,
      not only through a caller-supplied header.
- [ ] Compute SHA-256 while handling the artifact.
- [ ] Store accepted originals only inside a configured, bounded application
      directory; preserve them immutably.
- [ ] Define deterministic duplicate behavior: the same accepted content is
      idempotent; same apparent filename with different content becomes an
      explicit version decision, never an accidental overwrite.

Add focused tests for traversal/path separators, unsupported extension/MIME,
oversized input, checksum behavior, bounded storage, and duplicate idempotence.
Use isolated temporary data locations and a local test client. Do not use a
real provider.

Run the affected tests before committing. Stage only Gate-01-owned files, review
the staged diff, then commit this validated phase, for example:

    feat(gate-01): validate document intake

## Phase 1.2 — Durable source and version registry

Add the smallest durable local registry that can reliably represent:

- source_id;
- document_id;
- version_id;
- source URL when known;
- publisher/authority when known;
- checksum;
- fetched, published, and effective dates when known;
- parse status and review status;
- supersedes and superseded-by relationships; and
- stable paths or identifiers for the immutable original and derived artifacts.

Checklist:

- [ ] Registry records survive a process restart.
- [ ] IDs and state transitions are deterministic and cannot silently overwrite
      a previous version.
- [ ] Unknown provenance fields are represented as unknown, not invented.
- [ ] All writes keep the registry and artifact state consistent after an
      interrupted operation.
- [ ] The existing documents manifest is preserved or migrated only through a
      tested, reversible compatibility path.

Add tests for persistence, duplicate/version transitions, restart behavior,
provenance retention, and interrupted-write safety appropriate to the chosen
local mechanism.

Run focused tests plus the affected baseline checks. Commit only the validated
registry phase, for example:

    feat(gate-01): add local source registry

## Phase 1.3 — Candidate-only processing

Implement this explicit pipeline:

    upload/import
      -> validate
      -> preserve original
      -> parse using existing supported behavior
      -> canonical candidate artifact
      -> candidate chunks
      -> candidate index

Checklist:

- [ ] Candidate outputs use storage and identifiers separate from the live index.
- [ ] Existing live retrieval configuration cannot discover a candidate artifact.
- [ ] Unsupported formats fail clearly and leave no partial live state.
- [ ] Failed parsing can be retried or inspected without corrupting original
      artifacts or registry state.
- [ ] No MarkItDown or Firecrawl dependency is introduced.

Prove isolation with an integration test that creates a distinctive candidate
document, queries the normal live RAG path before publish, and demonstrates that
the candidate cannot affect the answer/context. The test must not call a live
model; inspect the deterministic retrieval context or use the project mock lane.

Run focused tests plus relevant baseline regression checks. Commit only the
validated candidate-processing phase, for example:

    feat(gate-01): isolate candidate document processing

## Phase 1.4 — Review, atomic publish, retire, and rollback

Implement explicit review state and a small, testable state transition model.
Publishing must be an all-or-nothing change from a reviewed candidate version to
the live version. Retiring must remove a version from live retrieval without
destroying its provenance. Rollback must restore a prior reviewed version
without recreating or mutating the original artifact.

Checklist:

- [ ] Candidate content cannot publish without an explicit reviewed transition.
- [ ] Publish changes live manifest/index pointers atomically from the reader's
      perspective.
- [ ] The live retrieval cache/store refreshes deterministically after publish,
      retire, and rollback; no stale live index is silently reused.
- [ ] Retire and rollback are idempotent or reject invalid transitions
      deterministically.
- [ ] Existing static RAG paths continue to work for the baseline corpus.

Add integration tests that prove:

- candidate isolation before review/publish;
- publish switches the live version atomically;
- normal live retrieval sees the newly published content only after publish;
- retire removes it from live retrieval;
- rollback restores the prior version;
- duplicate operations and restart/cache behavior remain deterministic; and
- existing RAG regression behavior is preserved.

Run the new lifecycle tests, affected API/retrieval tests, the Gate 00
deterministic baseline commands that remain applicable, and an offline retrieval
smoke. Record actual failures; never soften a test or change a baseline solely
to obtain PASS.

Commit only the validated transition phase, for example:

    feat(gate-01): publish reviewed document versions

## Final result and stop

Update only the smallest authoritative project-state and decision records
established by Gate 00. Do not add duplicate ledgers. Write:

    gates/results/GATE_01_RESULT.md

Use the operating-contract result format:

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

Mark PASS only when every Gate 01 acceptance item is proved by current evidence:
unsafe input rejection, deterministic duplicate behavior, durable provenance and
versions, candidate/live isolation, atomic publish, retire/rollback, and RAG
regression coverage. Existing unrelated failures remain documented blockers, not
facts to hide.

After final checks, commit only the result/state files in a separate clear
commit, for example:

    docs(gate-01): record document lifecycle result

For every commit:

1. stage explicit paths only;
2. inspect the staged file list and staged diff;
3. run git diff --cached --check;
4. commit after the relevant validation; and
5. run git status.

Never push. Do not start Gate 02, MarkItDown work, Firecrawl work, provider
work, deployment, or paper writing.

## Final response format

Return a compact handoff:

1. Gate status and why.
2. Verified Gate 00 prerequisite/baseline identity.
3. Commit IDs and exact files in each commit.
4. Lifecycle invariants proved, with test names/commands.
5. Every unchecked acceptance item and its evidence.
6. Known limitations and the only next allowed action.

Do not claim PASS from a design review, helper output, historical test run, or
successful upload alone. STOP after the handoff.
