# Gate 00 Execution Prompt

Copy everything below into one Luna implementation session.

## Mission

Execute Gate 00 only: establish a reproducible baseline and make only a safe,
evidence-backed restructure if it is genuinely needed. This is not permission
to start Gate 01 or any later gate.

Working directory:

    D:\Project cua Dat\VietRAGOps\ROOT\VietRagOps

At prompt creation, the repository was on main at 5b9045d and had a dirty
working tree. Treat that only as a historical observation. Re-verify it before
every conclusion; do not assume that HEAD alone identifies the baseline.

## Non-negotiable boundaries

- Run Gate 00 and nothing after it. End immediately after the Gate 00 result.
- Preserve current RAG and scientific behavior. Do not rewrite the app to make
  the structure look cleaner.
- Do not read, print, copy, log, commit, or request secret values. Do not open
  .env or any local credential handoff file.
- Do not use Firecrawl, MarkItDown, Groq, a live provider, Google Cloud, or
  any network-dependent feature. A locally present key does not authorize use.
- Do not reset, restore, clean, stash, amend, rebase, or silently commit
  pre-existing working-tree changes. Do not use git add .
- Do not modify external_tools, dependency manifests, Docker behavior, corpus
  content, or Git remotes unless a separately stated Gate 00 necessity makes
  it unavoidable. If that happens, stop with BLOCKED rather than expand scope.
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
       _agent_ops/phase_context_cards/evolve_2026_08_26/GATE_00.md
       _agent_ops/THIRD_PARTY_TOOLING.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\gates\GATE_00_BASELINE_AND_RESTRUCTURE.md
       ..\VietRAGOps_Evolve_Research_Gate_Pack_2026-08-26\03_AGENT_OPERATING_CONTRACT.md

3. Read _agent_ops/REPO_MAP.md before searching source. If it is stale, treat
   it only as a lead and record that fact. Use the supplied explore tool before
   broad code searching.

4. Maintain _agent_ops/CURRENT_TASK.md throughout the work. Record exact files
   touched, commands run, failures, and deliberately deferred work. Never put
   secret values in it.

5. Separate facts, inferences, and blockers in notes and the final result.
   A failed command is evidence, not a reason to substitute a different result.

## Team use

Primary implementation is sequential. One writer owns all changes.

You may use at most two independent read-only helpers after the initial Git
snapshot, only for:

- baseline command and artifact-inventory audit; and
- secret-safety / manifest-completeness audit.

They must not edit source, ops records, results, Git, or credentials. If an
Antigravity review tool is available, authenticated, and explicitly permitted
to receive this project context, use it only for the second audit with a
two-turn, read-only task. If it is unavailable, blocked, or unauthenticated,
record AGY_UNAVAILABLE once and continue. Its output is advisory; independently
verify every load-bearing claim.

## Phase 0.1 — Verify the current repository

Checklist:

- [ ] Confirm the canonical Git root, branch, HEAD, upstream relation, and
      porcelain working-tree status.
- [ ] Record whether each pre-existing change is tracked, deleted, or untracked.
      Do not classify it as Gate 00 work without evidence.
- [ ] Record the current test/data/index surface and the exact live retrieval
      artifact and configuration path.
- [ ] Record corpus, processed-document, chunk, and index counts using
      deterministic commands.
- [ ] Check that secret and local-handoff filenames are ignored, without
      reading their contents.
- [ ] Run the smallest real deterministic baseline in an offline/mock lane.
- [ ] Record every command, exit code, and warning verbatim enough to repeat,
      but never include environment values or secrets.

Use a process-only offline/mock configuration. Do not edit .env. Disable dotenv
loading for the test process and keep provider credentials absent from that
process. Begin with the existing project commands where applicable:

    python -m compileall app rag evals frontend scripts tests
    python -m pytest -q
    python scripts/validate_chunks.py --chunks-dir data/chunks
    python scripts/validate_processed_docs.py
    python scripts/verify_manifest.py
    docker compose config

Run a deterministic retrieval smoke using the existing evaluator, explicit
checked-in chunks and QA input, and an explicit output location or a
non-persistent mode. Inspect its help first so no uncontrolled artifact is
created. Do not run generation against a live provider.

If a command is unavailable or fails, preserve the failure with its cause. Do
not install packages, rewrite tests, or mask the result simply to obtain PASS.

Dirty-tree decision:

- If source, test, or data files are dirty, identify the baseline as HEAD plus
  the exact tracked/untracked overlay inventory and safe content hashes. For a
  deleted tracked file, record the source HEAD blob identity rather than
  inventing a hash.
- Do not tag HEAD and describe it as a dirty baseline.
- If the overlay cannot be safely and reproducibly identified, Gate 00 is
  BLOCKED. Write the result, make no Gate 01 change, and stop.

Commit only Gate-00-owned evidence after its validation. Never stage an
unrelated pre-existing change.

## Phase 0.2 — Write the baseline manifest

Create one machine-readable manifest at:

    gates/baselines/GATE_00_BASELINE.json

Use stable, readable JSON. It must contain at least:

- schema/version and creation time;
- canonical Git root, branch, HEAD, upstream relation, and working-tree state;
- dirty-overlay inventory and safe hashes when applicable;
- exact corpus, processed-document, chunk, and index artifact paths, counts,
  sizes, and SHA-256 checksums;
- provider mode used for each smoke command, without credentials;
- commands, exit status, captured result locations, and known warnings;
- baseline limitations and a clear reproduction procedure.

Do not put raw document content, credentials, environment dumps, provider
responses, or a generated patch containing unknown user changes in the manifest.

Validate that the manifest parses and that every referenced local artifact
exists. Commit just the new Gate-00-owned manifest and validation evidence when
this phase is complete, for example:

    docs(gate-00): record reproducible baseline

Before committing, inspect the explicit staged file list and staged diff. Never
push.

## Phase 0.3 — Safe module boundary decision

First produce a compact decision table:

    current responsibility -> current owner -> proposed boundary -> evidence
    -> change needed now? -> compatibility test

The only candidate top-level responsibility names are ingestion, knowledge,
agents, tools, evolution, research, and ops. They are targets, not a quota.

Checklist:

- [ ] Inspect actual ownership and call paths before moving anything.
- [ ] Reuse existing modules and compatibility wrappers.
- [ ] Make a boundary change only when it reduces a demonstrated coupling or
      enables a Gate 01 requirement without changing behavior.
- [ ] Add/adjust focused tests before declaring a move safe.
- [ ] Run affected tests plus the Gate 00 baseline checks again.

If no safe and necessary boundary change exists, record NOT NEEDED with
evidence. That is preferable to creating empty folders, duplicate wrappers, a
new framework, or a broad rewrite.

Each validated boundary change is its own small commit, for example:

    refactor(gate-00): isolate document ingestion boundary

Stage explicit files only. Do not include unrelated dirty work.

## Phase 0.4 — State, result, and stop

Create or update only the smallest authoritative state/control files required
by actual repository conventions:

- preserve the existing AGENTS.md; do not overwrite it;
- create/update PROJECT_STATE.md if no equivalent authoritative project-state
  record exists;
- reuse the authoritative decision record if one already exists. Do not create
  a duplicate decision ledger merely to satisfy a filename preference; document
  the mapping in PROJECT_STATE.md and the result;
- ensure gates/results exists; and
- write gates/results/GATE_00_RESULT.md using the Gate completion format from
  the operating contract.

The result must include:

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

Gate 00 may be PASS only when a later Gate can compare its behavior against a
frozen, reproducible baseline. A dirty state that is merely noted, but not
identified, is not a frozen baseline.

Run the final relevant checks, then commit only the state/result files in a
separate clear commit, for example:

    docs(gate-00): record baseline gate result

Run git status after each commit. Never push. Do not create, read, plan, or
implement Gate 01 after writing the result.

## Final response format

Return a compact handoff:

1. Gate status and why.
2. Commit IDs and exact files in each commit.
3. Baseline identity and the clean/dirty overlay condition.
4. Commands run with PASS/FAIL/BLOCKED outcomes.
5. Every unchecked acceptance item and its evidence.
6. The only next allowed action.

Do not claim PASS based on a helper, historical result, setup completion, or a
provider stop response. STOP after the handoff.
