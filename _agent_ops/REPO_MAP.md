# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`f986976`

## Snapshot

- Branch: `main`
- Generated: `2026-08-26`
- Code files indexed: 127
- Stack: Python

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `rag` | 46 | 73 | - |
| `app` | 16 | 11 | `app/main.py` |
| `evals` | 13 | 9 | - |
| `scripts` | 9 | 1 | - |
| `tests` | 35 | 0 | - |
| `frontend` | 7 | 0 | - |
| `tools` | 1 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `rag/retrieval/base.py` | 15 | 0 |
| `rag/lifecycle/errors.py` | 9 | 0 |
| `rag/retrieval/__init__.py` | 9 | 7 |
| `app/core/config.py` | 8 | 4 |
| `rag/generation/context_builder.py` | 7 | 3 |
| `app/main.py` | 6 | 3 |
| `rag/chunking/metadata_builder.py` | 6 | 0 |
| `rag/lifecycle/registry.py` | 6 | 1 |
| `rag/retrieval/advanced_hybrid_retriever.py` | 6 | 5 |
| `rag/retrieval/index_store.py` | 6 | 0 |
| `app/core/errors.py` | 5 | 0 |
| `rag/generation/groq_client.py` | 5 | 0 |
| `rag/preprocessing/normalizer.py` | 5 | 0 |
| `app/schemas/query.py` | 4 | 0 |
| `evals/experiments/defaults.py` | 4 | 0 |

## Symbol Graph

452 symbols, 850 edges (exact 533, heuristic 231, ambiguous 86, weak 0).

### Routes

- `GET ` -> `app/api/routes_documents.py:42` list_documents
- `GET /experiments` -> `app/api/routes_eval.py:40` list_experiments
- `GET /experiments/{experiment_id}` -> `app/api/routes_eval.py:54` get_experiment
- `GET /health` -> `app/api/routes_health.py:12` health
- `GET /{doc_id}` -> `app/api/routes_documents.py:62` get_document
- `POST /ask` -> `app/api/routes_agent.py:338` ask_agent
- `POST /ask` -> `app/api/routes_query.py:31` ask
- `POST /eval/generation` -> `app/api/routes_eval.py:24` eval_generation
- `POST /eval/retrieval` -> `app/api/routes_eval.py:18` eval_retrieval
- `POST /index` -> `app/api/routes_documents.py:35` index_documents
- `POST /retrieve` -> `app/api/routes_retrieval.py:34` retrieve
- `POST /upload` -> `app/api/routes_documents.py:23` upload_documents

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `FakeResponse.json` | 18 | `tests/test_ollama_client.py:18` |
| `FakeHttpxClient.post` | 13 | `tests/test_ollama_client.py:35` |
| `tokenize` | 12 | `rag/retrieval/base.py:21` |
| `AnswerGenerator` | 10 | `rag/generation/answer_generator.py:26` |
| `normalize_text` | 10 | `rag/retrieval/base.py:15` |
| `get_settings` | 9 | `app/core/config.py:30` |
| `get_store` | 8 | `app/core/config.py:35` |
| `normalize_text` | 8 | `rag/preprocessing/normalizer.py:18` |
| `ProviderRouter` | 7 | `rag/generation/provider_router.py:23` |
| `ProviderRouter.current_provider` | 7 | `rag/generation/provider_router.py:41` |
| `RetrievalResult` | 7 | `rag/retrieval/base.py:44` |
| `api_get` | 6 | `frontend/streamlit_app.py:539` |

Query it instead of grepping:

```bash
python _agent_ops/tools/explore.py --root . --symbol <name>    # callers, callees, flow
python _agent_ops/tools/explore.py --root . --impact <name>    # blast radius + tests
python _agent_ops/tools/explore.py --root . --path <a> <b>     # how a reaches b
```

## Entry Points

- `app/main.py`

## Oversized Files

Files past 400 lines. Long files are where agents lose the thread and
where unrelated responsibilities collect. Split along a responsibility
boundary before adding to one of these.

| File | Lines |
| --- | --- |
| `frontend/streamlit_app.py` | 911 |
| `rag/generation/answer_generator.py` | 469 |

## Isolated Files

17 file(s) have no resolved local imports in either direction.
They are listed only on demand -- enumerating them here would recreate the
context bloat this map exists to prevent.

## Drill Down

This map is deliberately shallow. For the affected zone of a specific change:

```bash
python _agent_ops/tools/scan_deps.py --root . --seed "<keyword>" --hops 2 --output markdown
```

## Limits

- Covers `.py`, `.js`, `.jsx`, `.ts`, `.tsx` only.
- Relative imports resolve exactly. Absolute Python imports and JS path
  aliases are inferred by probing parent directories, so they can be wrong;
  package imports (`react`, `numpy`) are not followed at all.
- Dynamic imports, DI wiring, and runtime registries are invisible here.
  Verify before claiming a file is unused.
