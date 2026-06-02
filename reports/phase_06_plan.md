# Phase 06 Plan

## Objective

Build the grounded answer-generation layer with retrieved context, citations, citation verification, refusal guardrails, and optional Groq support, while ensuring all tests still pass without any real API key.

## Inputs found

- `data/chunks/chunks_500.jsonl`
- `evals/datasets/dev_qa.jsonl`
- `dist/experiments/retrieval/compare_retrievers_20260601_204043.json`
- `reports/retrieval_baseline.md`
- `reports/advanced_retrieval_benchmark.md`

## Files to create or modify

- `ALWAYS_READ/02_CURRENT_PHASE.md`
- `rag/generation/__init__.py`
- `rag/generation/prompt_builder.py`
- `rag/generation/answer_generator.py`
- `rag/generation/citation_verifier.py`
- `rag/generation/guardrails.py`
- `rag/generation/context_builder.py`
- `rag/generation/groq_client.py`
- `reports/generation_behavior_report.md`
- `reports/phase_06_audit.md`
- `reports/phase_06_completion_report.md`
- `tests/test_prompt_builder.py`
- `tests/test_citation_verifier.py`
- `tests/test_guardrails.py`
- `tests/test_answer_generator.py`
- `ALWAYS_READ/03_IMPLEMENTATION_LOG.md`
- `project_context_cards/PHASE_06_GENERATION_GUARDRAILS.md`

## Implementation plan

1. Add a context builder that uses the Phase 5 recommendation: baseline hybrid retrieval as the default context source.
2. Add a prompt builder that enforces grounded answering, Vietnamese output, citations for factual claims, and refusal when context is insufficient.
3. Add a Groq client that only reads `GROQ_API_KEY` and `GROQ_MODEL`.
4. Add a deterministic offline generator fallback so tests and smoke runs pass without any API key.
5. Add citation verification and refusal guardrails for low-support, private-data, out-of-corpus, and citation-mismatch cases.
6. Add unit tests for prompt construction, citation verification, guardrails, and answer generation.
7. Produce a behavior report with answerable, procedural, multi-hop, unanswerable, private-data refusal, and citation-mismatch examples.

## Test plan

- `python -m compileall rag evals tests`
- `pytest -q`
- Optional if a key appears later: run one real Groq smoke example without printing the key

## Audit plan

- Verify `groq_client.py` reads only `GROQ_API_KEY` and `GROQ_MODEL`.
- Verify tests pass with no Groq key present.
- Verify the answer schema matches the required output structure.
- Verify the behavior report clearly labels mock or deterministic fallback behavior where applicable.
- Run secret scans before phase completion.

## Expected commands

```bash
python -m compileall rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\\s*=\\s*gsk_" .
```

## Risk list

- The deterministic fallback may be extractive and less fluent than a real model.
- Citation verification may need tolerant text normalization to avoid false negatives on punctuation differences.
- Private-data detection is heuristic and needs careful tests to avoid false refusals.

## Manual checks recommended

- Review the refusal wording for private data and out-of-corpus questions.
- Inspect generated citations to confirm evidence quotes are directly traceable to retrieved chunks.
- If a Groq key is provided later, rerun one grounded-answer smoke test before public demo work.
