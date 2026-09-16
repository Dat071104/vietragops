# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`d809598`

## Snapshot

- Branch: `main`
- Generated: `2026-09-11`
- Code files indexed: 301
- Stack: Python

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `rag` | 60 | 181 | - |
| `research` | 90 | 87 | - |
| `app` | 22 | 24 | `app/main.py`, `app/mcp/server.py` |
| `evals` | 15 | 10 | - |
| `scripts` | 17 | 1 | - |
| `frontend` | 8 | 1 | - |
| `tests` | 88 | 0 | - |
| `tools` | 1 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `rag/generation/context_builder.py` | 17 | 3 |
| `research/gate0/evaluator/capability.py` | 16 | 0 |
| `app/core/config.py` | 15 | 11 |
| `rag/generation/groq_client.py` | 15 | 0 |
| `rag/retrieval/__init__.py` | 15 | 8 |
| `rag/retrieval/base.py` | 15 | 0 |
| `rag/lifecycle/registry.py` | 14 | 1 |
| `rag/retrieval/index_store.py` | 14 | 0 |
| `rag/lifecycle/errors.py` | 13 | 0 |
| `rag/generation/provider_router.py` | 12 | 4 |
| `research/gate07/dataset/models.py` | 12 | 0 |
| `research/gate07/harness/serialization.py` | 11 | 2 |
| `rag/lifecycle/gcs_storage.py` | 10 | 0 |
| `rag/lifecycle/service.py` | 10 | 8 |
| `research/gate0/contracts/__init__.py` | 10 | 1 |

## Symbol Graph

2163 symbols, 4868 edges (exact 3118, heuristic 944, ambiguous 806, weak 0).

### Routes

- `GET ` -> `app/api/routes_documents.py:130` list_documents
- `GET /experiments` -> `app/api/routes_eval.py:40` list_experiments
- `GET /experiments/{experiment_id}` -> `app/api/routes_eval.py:54` get_experiment
- `GET /health` -> `app/api/routes_health.py:22` health
- `GET /health/live` -> `app/api/routes_health.py:43` liveness
- `GET /health/ready` -> `app/api/routes_health.py:50` readiness
- `GET /{doc_id}` -> `app/api/routes_documents.py:192` get_document
- `GET /{doc_id}/versions` -> `app/api/routes_documents.py:150` list_document_versions
- `POST /ask` -> `app/api/routes_agent.py:362` ask_agent
- `POST /ask` -> `app/api/routes_query.py:31` ask
- `POST /eval/generation` -> `app/api/routes_eval.py:24` eval_generation
- `POST /eval/retrieval` -> `app/api/routes_eval.py:18` eval_retrieval
- `POST /index` -> `app/api/routes_documents.py:123` index_documents
- `POST /retrieve` -> `app/api/routes_retrieval.py:34` retrieve
- `POST /upload` -> `app/api/routes_documents.py:56` upload_documents
- _... 5 more_

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `VersionResolver.resolve` | 58 | `rag/retrieval/version_resolver.py:90` |
| `test_local_api_client_does_not_add_cloud_auth.Response` | 55 | `tests/test_cloud_auth.py:11` |
| `test_cloud_iam_client_fetches_id_token_without_logging_or_persisting_it.Response` | 51 | `tests/test_cloud_auth.py:35` |
| `GroqClient.generate_json` | 40 | `rag/generation/groq_client.py:157` |
| `ProviderRouter` | 36 | `rag/generation/provider_router.py:99` |
| `ApiClient.post` | 33 | `frontend/api_client.py:47` |
| `test_ollama_output_budget_reaches_wire.FakeClient.post` | 32 | `tests/test_generation_budget_wire.py:77` |
| `FakeHttpxClient.post` | 32 | `tests/test_ollama_client.py:35` |
| `ProviderRouter.generate_json` | 27 | `rag/generation/provider_router.py:201` |
| `build_case_manifest` | 27 | `research/gate0/drift/manifest.py:163` |
| `build_all_cases` | 27 | `research/gate07/dataset/generator.py:15` |
| `GcsObjectStore.exists` | 26 | `rag/lifecycle/gcs_storage.py:171` |

Query it instead of grepping:

```bash
python _agent_ops/tools/explore.py --root . --symbol <name>    # callers, callees, flow
python _agent_ops/tools/explore.py --root . --impact <name>    # blast radius + tests
python _agent_ops/tools/explore.py --root . --path <a> <b>     # how a reaches b
```

## Entry Points

- `app/main.py`
- `app/mcp/server.py`

## Oversized Files

Files past 400 lines. Long files are where agents lose the thread and
where unrelated responsibilities collect. Split along a responsibility
boundary before adding to one of these.

| File | Lines |
| --- | --- |
| `evals/gate12v_runner.py` | 1108 |
| `frontend/streamlit_app.py` | 979 |
| `rag/generation/openrouter_client.py` | 862 |
| `rag/generation/answer_generator.py` | 609 |
| `rag/generation/provider_router.py` | 581 |
| `rag/lifecycle/gcs_registry.py` | 519 |
| `rag/lifecycle/gcs_service.py` | 513 |
| `rag/lifecycle/registry.py` | 500 |
| `research/gate07/protocol/freeze.py` | 495 |
| `research/gate07/metrics/report.py` | 458 |

## Isolated Files

31 file(s) have no resolved local imports in either direction.
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
