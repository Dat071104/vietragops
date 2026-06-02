# Phase 06 Audit

## Audit scope

Validate grounded answer generation, citation verification, refusal behavior, Groq env handling, and secret hygiene before Phase 7.

## Required outputs

- Present: `rag/generation/prompt_builder.py`
- Present: `rag/generation/answer_generator.py`
- Present: `rag/generation/citation_verifier.py`
- Present: `rag/generation/guardrails.py`
- Present: `rag/generation/context_builder.py`
- Present: `rag/generation/groq_client.py`
- Present: `reports/generation_behavior_report.md`
- Present: `tests/test_prompt_builder.py`
- Present: `tests/test_citation_verifier.py`
- Present: `tests/test_guardrails.py`
- Present: `tests/test_answer_generator.py`

## Verification commands

```bash
python -m compileall rag evals tests
pytest -q
rg -n "gsk_[A-Za-z0-9]{20,}" .
rg -n "GROQ_API_KEY\s*=\s*gsk_" .
```

## Results

- Compile check: passed
- Tests: `23 passed`
- Deterministic generation examples: passed for direct, procedural, multi-hop, unanswerable, and private-data cases
- Groq presence check: `false`
- Secret scans: no matches in repository files

## Reviewer notes

- `groq_client.py` reads only `GROQ_API_KEY` and `GROQ_MODEL`
- The deterministic fallback is grounded and testable offline, but still more extractive than a production LLM answerer
- Unanswerable and private-data questions now refuse with explicit reasons
- Citation verification rejects missing or unsupported citations

## Sign-off

- Reviewer: pass
- Security/Release Auditor: pass
- Phase status: `ready_for_next_phase`
