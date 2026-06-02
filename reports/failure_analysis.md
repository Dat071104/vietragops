# Failure Analysis

## Source

- Experiment: `dist/experiments/pipelines/compare_pipelines_20260602_004911.json`
- Evaluation mode: deterministic or mock generation

## Failure label counts

- `retrieval_miss`: 222
- `stale_source`: 84

## Main patterns

- `retrieval_miss`: still the largest failure mode, especially on regulation-heavy questions where the right chunk is not consistently surfaced in the top retrieved set.
- `stale_source`: appears on source-conflict style prompts where the benchmark deliberately mixes older and newer regulation artifacts.
- Unsupported answers were suppressed well in this run because the current fallback generator is conservative and the guardrails are willing to refuse.

## Cases to watch

- Numeric or fee questions remain sensitive to missing concrete figures, even when semantically related dorm or fee content is retrieved.
- Procedural guide questions can still attract secondary irrelevant evidence lines because the deterministic fallback is extractive rather than concise.
- Regulation and source-conflict questions remain the clearest candidates for later reranker and prompt-quality improvements.

## Next-step recommendations

- Expand the human-curated portion of the QA set beyond the current small validation split.
- Re-run the same matrix with a real Groq-backed generator once local credentials are available.
- Add stricter evidence-line filtering so direct answers cite fewer tangential segments.

## Release note

- Any public demo or README claim should describe these failure counts as deterministic offline benchmark findings, not as final production error rates.
