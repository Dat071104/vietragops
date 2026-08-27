# Repo Map / Ban do ma nguon

Generated file. Do not hand-edit; regenerate with
`python _agent_ops/tools/generate_repo_map.py --root . --output _agent_ops/REPO_MAP.md --force`.

Read this BEFORE grepping the repository. It answers "where does the code
live" and "what breaks if I touch this" in one Tier-1 read.

## Last Verified Commit

`81589e2`

## Snapshot

- Branch: `main`
- Generated: `2026-08-27`
- Code files indexed: 185
- Stack: Python

## Modules

`Inbound` counts imports coming from OUTSIDE the module: higher means more
code depends on it, so changes there travel further.

| Module | Files | Inbound | Entry points |
| --- | --- | --- | --- |
| `rag` | 54 | 125 | - |
| `research` | 22 | 20 | - |
| `app` | 21 | 17 | `app/main.py`, `app/mcp/server.py` |
| `evals` | 13 | 9 | - |
| `scripts` | 10 | 1 | - |
| `tests` | 57 | 0 | - |
| `frontend` | 7 | 0 | - |
| `tools` | 1 | 0 | - |

## Hot Files (widest blast radius)

Ranked by fan-in. Treat an edit here as cross-module until proven otherwise.

| File | Imported by | Imports |
| --- | --- | --- |
| `rag/generation/context_builder.py` | 15 | 3 |
| `rag/retrieval/base.py` | 15 | 0 |
| `rag/retrieval/__init__.py` | 13 | 8 |
| `app/core/config.py` | 12 | 8 |
| `rag/lifecycle/registry.py` | 12 | 1 |
| `rag/retrieval/index_store.py` | 11 | 0 |
| `rag/lifecycle/errors.py` | 10 | 0 |
| `rag/generation/groq_client.py` | 9 | 0 |
| `rag/lifecycle/service.py` | 9 | 8 |
| `research/gate0/sandbox/__init__.py` | 8 | 4 |
| `app/main.py` | 7 | 4 |
| `rag/chunking/metadata_builder.py` | 7 | 0 |
| `rag/lifecycle/storage.py` | 6 | 0 |
| `rag/preprocessing/section_detector.py` | 6 | 1 |
| `rag/retrieval/advanced_hybrid_retriever.py` | 6 | 5 |

## Symbol Graph

1200 symbols, 2532 edges (exact 1710, heuristic 600, ambiguous 222, weak 0).

### Routes

- `GET ` -> `app/api/routes_documents.py:124` list_documents
- `GET /experiments` -> `app/api/routes_eval.py:40` list_experiments
- `GET /experiments/{experiment_id}` -> `app/api/routes_eval.py:54` get_experiment
- `GET /health` -> `app/api/routes_health.py:12` health
- `GET /{doc_id}` -> `app/api/routes_documents.py:186` get_document
- `GET /{doc_id}/versions` -> `app/api/routes_documents.py:144` list_document_versions
- `POST /ask` -> `app/api/routes_agent.py:355` ask_agent
- `POST /ask` -> `app/api/routes_query.py:31` ask
- `POST /eval/generation` -> `app/api/routes_eval.py:24` eval_generation
- `POST /eval/retrieval` -> `app/api/routes_eval.py:18` eval_retrieval
- `POST /index` -> `app/api/routes_documents.py:117` index_documents
- `POST /retrieve` -> `app/api/routes_retrieval.py:34` retrieve
- `POST /upload` -> `app/api/routes_documents.py:59` upload_documents
- `POST /versions/{version_id}/publish` -> `app/api/routes_documents.py:159` publish_document_version
- `POST /versions/{version_id}/retire` -> `app/api/routes_documents.py:168` retire_document_version
- _... 2 more_

### Most-called symbols

| Symbol | Called by | Where |
| --- | --- | --- |
| `VersionResolver.resolve` | 38 | `rag/retrieval/version_resolver.py:90` |
| `FakeHttpxClient.post` | 31 | `tests/test_ollama_client.py:35` |
| `build_case_manifest` | 27 | `research/gate0/drift/manifest.py:163` |
| `FakeResponse.json` | 26 | `tests/test_ollama_client.py:18` |
| `GroqClient.generate_json` | 24 | `rag/generation/groq_client.py:193` |
| `EducationSandboxStore` | 23 | `research/gate0/sandbox/store.py:64` |
| `ProviderRouter` | 21 | `rag/generation/provider_router.py:63` |
| `build_api` | 21 | `research/gate0/sandbox/__init__.py:11` |
| `LifecycleService.review` | 19 | `rag/lifecycle/service.py:175` |
| `WebImportService.import_url` | 19 | `rag/lifecycle/web_import.py:118` |
| `VersionResolver` | 18 | `rag/retrieval/version_resolver.py:66` |
| `ToolContract` | 18 | `research/gate0/contracts/contract.py:80` |

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
| `frontend/streamlit_app.py` | 911 |
| `rag/generation/answer_generator.py` | 553 |
| `rag/lifecycle/registry.py` | 500 |

## Isolated Files

20 file(s) have no resolved local imports in either direction.
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
