# Phase 6 - Generation, citations, guardrails

## Phase goal

Generate answers only from retrieved context with citations, verifier, and refusal policy.

## Required inputs

- Current project context.
- Implementation log.
- Relevant previous phase outputs.

## Expected outputs

rag/generation, reports/generation_behavior_report.md

## Quality gate

Answers cite retrieved chunks; unanswerable/private/out-of-scope questions refuse reliably.

## Do not do

- Do not skip logging.
- Do not fake metrics.
- Do not expand scope without recording a decision.
- Do not read unrelated code files unless zone-brain identifies them.

## Current status

done

## Handoff notes

Completed files:

- `rag/generation/__init__.py`
- `rag/generation/prompt_builder.py`
- `rag/generation/answer_generator.py`
- `rag/generation/citation_verifier.py`
- `rag/generation/guardrails.py`
- `rag/generation/context_builder.py`
- `rag/generation/groq_client.py`
- `reports/generation_behavior_report.md`
- `reports/phase_06_plan.md`
- `reports/phase_06_audit.md`
- `reports/phase_06_completion_report.md`
- `tests/test_prompt_builder.py`
- `tests/test_citation_verifier.py`
- `tests/test_guardrails.py`
- `tests/test_answer_generator.py`

Commands run:

```bash
python -m compileall rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

Blockers:

- No blocker. Real Groq smoke coverage was skipped because `GROQ_API_KEY` was not present locally.

Next phase risks:

- Phase 7 should measure refusal accuracy and citation support rate on a much larger QA set.
- The deterministic fallback is grounded and reproducible, but its answer style is still more extractive than a real LLM response.
