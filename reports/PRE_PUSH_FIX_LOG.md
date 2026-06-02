# Pre-Push Fix Log

## Issue 1
Issue: Experiment CLIs did not support the documented no-argument validation commands.
Symptom: `python -m evals.experiments.compare_retrievers` and `python -m evals.experiments.run_generation_eval` failed with missing `--chunks` and `--qa` arguments.
Root cause: the CLIs required explicit artifact paths instead of defaulting to the repo's standard validation datasets, and the generation CLI defaulted `guardrails` to `False` even though the config default was `True`.
Files changed: `evals/experiments/defaults.py`, `evals/experiments/compare_retrievers.py`, `evals/experiments/run_generation_eval.py`, `evals/experiments/compare_pipelines.py`, `tests/test_eval_cli_defaults.py`
Fix: added shared default dataset paths, made the CLI parsers testable, aligned `guardrails` with the config default, and preserved the existing explicit-argument path.
Verification: `python -m evals.experiments.compare_retrievers`, `python -m evals.experiments.run_generation_eval`, `pytest -q tests/test_eval_cli_defaults.py`
Regression risk: low; the change only adds safe defaults and regression coverage.

## Issue 2
Issue: generation evaluation did not actually honor `top_k`.
Symptom: the pipeline matrix claimed to compare `top_k` values `3`, `5`, and `8`, but the runner always used the answer generator's default retrieval depth.
Root cause: `run_generation_eval()` called `generator.answer(..., debug=True)` without forwarding `top_k=config.top_k`.
Files changed: `evals/experiments/run_generation_eval.py`, `tests/test_eval_cli_defaults.py`, `README.md`, `reports/benchmark_report.md`, `reports/failure_analysis.md`, `reports/technical_report.md`, `reports/FINAL_PROJECT_HANDOFF.md`
Fix: forwarded `top_k` into `AnswerGenerator.answer()`, reran `run_generation_eval` and `compare_pipelines`, and updated the published benchmark docs to the new artifact-backed metrics.
Verification: `pytest -q tests/test_eval_cli_defaults.py`, `python -m evals.experiments.run_generation_eval`, `python -m evals.experiments.compare_pipelines`
Regression risk: medium-low; benchmark numbers changed because the prior behavior was under-evaluating the intended configs.

## Issue 3
Issue: the repo-mandated zone-brain helper crashed on Windows consoles.
Symptom: `python skills/zone-brain/scripts/scan_deps.py ...` raised `UnicodeEncodeError` on the default CP1252 console.
Root cause: the script printed emoji and non-ASCII banner text directly to stdout.
Files changed: `skills/zone-brain/scripts/scan_deps.py`
Fix: replaced console output banners with ASCII-safe text.
Verification: `python skills/zone-brain/scripts/scan_deps.py --root . --seed "eval,metric,experiment" --hops 2 --output files`
Regression risk: low; only presentation strings changed.

## Issue 4
Issue: the API smoke payload from the release checklist was only "working" via ignored fields.
Symptom: `/retrieve` ignored `use_reranker` and `return_debug`; `/ask` ignored `return_debug` as an alias and did not expose the reranker toggle from the checklist payload.
Root cause: the request schemas did not include the checklist fields and the routes always used the cached default runtime pipeline.
Files changed: `app/schemas/query.py`, `app/api/routes_retrieval.py`, `app/api/routes_query.py`, `tests/test_api_retrieve.py`, `tests/test_api_ask.py`
Fix: added request-model support for the checklist fields, routed `/retrieve` to advanced hybrid retrieval when `use_reranker=true`, returned a debug payload for `/retrieve`, honored `return_debug` on `/ask`, and explicitly rejected `use_guardrail=false` on `/ask` to preserve the app's safety guarantee.
Verification: `pytest -q tests/test_api_retrieve.py tests/test_api_ask.py`, live `/health`, `/docs`, `/retrieve`, and `/ask` smoke requests using the checklist payloads
Regression risk: low-medium; the API surface is wider, but the unsafe guardrail-disable path remains blocked.

## Issue 5
Issue: the Streamlit frontend used a deprecated dataframe sizing API.
Symptom: frontend smoke surfaced warnings that `use_container_width` is past its deprecation window.
Root cause: three frontend components still used the old Streamlit parameter.
Files changed: `frontend/components/document_table.py`, `frontend/components/evidence_table.py`, `frontend/components/eval_dashboard.py`
Fix: replaced `use_container_width=True` with `width="stretch"`.
Verification: `python -m streamlit run frontend/streamlit_app.py --server.headless true --server.address 127.0.0.1 --server.port 8501`, `streamlit.testing.v1.AppTest`
Regression risk: low; it is a direct API migration to the supported parameter.

## Issue 6
Issue: generated helper artifacts polluted the working tree during validation.
Symptom: `.zone_context.md` and temporary request payload files appeared as untracked scratch artifacts.
Root cause: `.gitignore` did not exclude those generated local-only files.
Files changed: `.gitignore`
Fix: ignored `.zone_context.md` and `tmp_*.json`.
Verification: `.gitignore` now covers the generated helper artifacts; validation log files were also removed after the audit.
Regression risk: low; the ignore rules only target generated local scratch files.
