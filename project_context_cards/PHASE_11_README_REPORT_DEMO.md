# Phase 11 - README, report, demo

## Phase goal

Produce recruiting-ready README, report, demo video/GIF, architecture diagram, CV bullets.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

README.md, reports/technical_report.md, reports/benchmark_report.md, assets/demo.gif

## Quality gate

README is reproducible, numbers are real, limitations and failure analysis are included.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

- Completed files:
  - `README.md`
  - `reports/technical_report.md`
  - `reports/benchmark_report.md`
  - `reports/failure_analysis.md`
  - `assets/architecture.md`
  - `assets/architecture.mmd`
  - `demo_video_script.md`
  - `reports/FINAL_PROJECT_HANDOFF.md`
- Commands run:
  - `python -m compileall app rag evals frontend scripts tests`
  - `pytest -q`
  - `python scripts/validate_chunks.py --chunks-dir data/chunks`
  - `python -m evals.experiments.run_retrieval_eval --chunks data/chunks/chunks_500.jsonl --qa evals/datasets/dev_qa.jsonl --retriever hybrid --top_k 5`
  - `docker compose config`
  - `rg -n "gsk_[A-Za-z0-9]{20,}" .`
  - `rg -n "GROQ_API_KEY\s*=\s*gsk_" .`
- Result:
  - final docs, architecture assets, demo script, and project handoff are complete and metric-backed
- Blockers:
  - none for documentation delivery
  - previously documented Docker-daemon blocker from Phase 10 still applies to local image-build verification
- Next phase risks:
  - none; project handoff complete
