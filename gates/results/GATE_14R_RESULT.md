# Gate 14-R — Restore dense retrieval and re-measure grounding

**Status:** COMPLETE LOCALLY — product-lane ONNX retrieval selected; retrieval-only
ceiling improved. Push is blocked by host Git credentials, so the remote release
is not yet complete. Generation remains a separate gate.

## Protocol and entry receipts

- Frozen protocol: `gates/baselines/GATE_14R_PROTOCOL.json`.
- Final protocol SHA-256:
  `6d75e51696008f3b9a1c7360055cbf8d7515d7614c2e31646528cd14d414281f`.
- Protocol freeze commit: `ed9c258`.
- Owner decision addendum commit: `d8b074d`.
- Model-selection registration commit: `5f98d88`.
- R0 entry HEAD and `origin/main`:
  `31a69c02fee68ab004c14a4ecd85eca563ae728f`.
- R0 overlay: exactly 25 pre-existing paths; Git index empty.
- R0 interpreter: `.venv/Scripts/python.exe`.
- R0 full suite: `591 passed, 3 warnings` in 611.03 seconds with an external
  `--basetemp`.
- Final full suite after this gate's source changes: `598 passed, 3 warnings` in
  348.93 seconds. The increase of seven is accounted for by new observability,
  vector-contract, and default-model tests; no existing test was removed.
- Count-only `.env` presence check found `.env`; no value was read or printed.

Production was sparse-only at entry and remains the deployed pre-gate behavior:
`requirements.txt` had no ML runtime and `Dockerfile` installed only that file.
The three import probes for `sentence_transformers`, `torch`, and `transformers`
were absent at R0.

## R1 — Loud degradation and health state

Implemented in `ad6a887`:

- Dense and BGE initialization no longer redirect exceptions into `StringIO`.
- Known import/initialization failures are caught narrowly, logged at WARNING
  with the exception type and reason, and accumulated in the downgrade chain.
- `DenseRetriever.status()` exposes the active backend, state, model identity,
  degradation reason, and downgrade reasons.
- The state is visible through retriever metadata, `ContextBuilder` debug,
  `/retrieve` debug, and `/health`.
- The backend order is now ONNX -> sentence-transformers -> sparse fallback.
- Vector-space mismatch is a typed failure, not a usable result.
- Focused R1 tests passed `15 passed, 1 warning`; the post-ONNX focused slice
  passed `13 passed, 1 warning`.
- Isolated no-ONNX tests passed `11 passed, 1 warning`.
- The same focused tests with the ONNX/ML temp environment passed
  `11 passed, 1 warning`.

## R2 — Owner decision

The owner selected **(b') ONNX runtime with precomputed corpus embeddings**.

Plain option (b) was rejected for the owner's stated reason: precomputing only
corpus vectors still requires the same query encoder at runtime. Otherwise query
and document vectors occupy different spaces and retrieval is meaningless. Plain
(b) would therefore still ship torch plus the model and save almost nothing on
image size or cold start.

The selected contract is:

- torch, sentence-transformers, and transformers are local export tooling only;
- the product requirements add only exact `onnxruntime==1.20.1`,
  `tokenizers==0.23.2`, and `numpy==2.4.6`;
- the product artifact contains ONNX query encoder, tokenizer, normalized corpus
  vectors, chunk IDs, and metadata hashes;
- each persisted artifact records model ID/revision, dimension, pooling,
  normalization, query/passage prefixes, chunk-store SHA-256, chunk-ID SHA-256,
  and embedding SHA-256.

## R3 — ONNX implementation and measured footprint

Source commits:

- `775cda7` — ONNX backend, vector contract, export/materialization scripts,
  exact runtime pins, and tests.
- `0b6616c` — ignore generated local ONNX/vector artifacts.
- `d3f498e` — SentenceTransformers 6 pooling API compatibility.
- `03a5a8a` — select E5-small as the product default and add the pinning test.

The offline scripts are `scripts/export_embedding_onnx.py` and
`scripts/compute_corpus_embeddings.py`; neither is imported by `app/` or
`rag/`. The runtime `_OnnxBackend` validates model identity, optional revision,
dimension, normalized L2 convention, row count/order, and chunk-store hash
before serving a dense result.

### Registered model rationale

The three candidates were registered before measurement:

1. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` — incumbent;
   its card documents 50 languages, semantic search, 384 dimensions, and mean
   pooling: <https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2>.
2. `intfloat/multilingual-e5-small` — multilingual retrieval candidate; its
   card lists Vietnamese and requires `query:`/`passage:` prefixes. The E5 paper
   reports broad zero-shot retrieval evidence:
   <https://huggingface.co/intfloat/multilingual-e5-small>,
   <https://arxiv.org/abs/2212.03533>.
3. `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` — larger
   multilingual comparison point; its card documents 50 languages, 768
   dimensions, and mean pooling:
   <https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2>.

BGE-M3 was not used as an embedding candidate because Gate 07 measured BGE-M3
   embeddings and its research artifacts are frozen. The BGE reranker below is
   a product-lane `BAAI/bge-reranker-v2-m3` run and does not touch Gate 07 files.

### Export and corpus materialization

All export/materialization times below are local CPU measurements from the
isolated ML venv. Model download time is not included in export time.

| Model | Dim | Max length | FP32 ONNX | Int8 ONNX | Export wall-clock | Corpus fp32 | Corpus int8 | Query encode mean fp32/int8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MiniLM-L12-v2 | 384 | 128 | 470,253,876 B | 118,313,767 B | 23.876 s | 27.413 s | 23.931 s | 26.047 / 21.359 ms |
| multilingual-E5-small | 384 | 512 | 470,253,876 B | 118,313,767 B | 24.072 s | 252.352 s | 182.783 s | 221.744 / 193.822 ms |
| MPNet-base-v2 | 768 | 128 | 1,110,038,652 B | 278,646,647 B | 38.303 s | 45.061 s | 24.703 s | 55.304 / 34.716 ms |

The E5 int8 self-contained product artifact is `136,493,803 B` (`130.17 MiB`),
including model, tokenizer, vectors, IDs, and metadata. It is locally present
under the ignored `data/chunks/embeddings/active/` path and is not staged as a
large binary Git object. Its metadata records:

- model: `intfloat/multilingual-e5-small`;
- precision: `int8_dynamic_weight`;
- dimension: 384;
- normalization: L2, normalized=true;
- chunk count: 695;
- chunk-store SHA-256:
  `0510c68876fc4b9295ba9ffff86bd1816432233f9b265b272e6e26613ba7e130`;
- embedding SHA-256:
  `9b9fdfb36951a7f0aef4c1ccf0cf4f914533d7cb41b7e0e62a1f52d72cbcc976`.

PyPI wheel measurements were verified from the official package feeds:

| Runtime package | Windows CPython 3.13 | Docker Linux CPython 3.11 |
|---|---:|---:|
| `onnxruntime==1.20.1` | 11,331,758 B | 13,331,703 B |
| `tokenizers==0.23.2` | 2,863,236 B | 3,386,843 B |
| `numpy==2.4.6` | 12,318,598 B | 16,918,164 B |
| Direct wheel total | 26,513,592 B / 25.29 MiB | 33,636,710 B / 32.08 MiB |

The direct Linux runtime wheels plus the active E5 int8 artifact are
`170,130,513 B` (`162.25 MiB`) before transitive dependency unpacking. The
Docker daemon was unavailable (`docker_engine` pipe absent), so no real image
delta was measured and no image-size estimate is presented as measured.

## R4 — Retrieval-only measurements

All primary rows use the frozen 120-row QA file, 116 answerable rows, product
`ContextBuilder`, candidate depth 50, and no generation. Wilson intervals are
95% intervals for the answerable question-hit ceiling. `micro P raw` is the
relevant-ID numerator over `116*k`.

| Configuration | Macro R@k | Macro P@k | MRR | Ceiling / Wilson | micro P raw | `curriculum_structure` | Query encode mean |
|---|---:|---:|---:|---|---|---|---:|
| Sparse top-5 control | .612069 | .124138 | .452730 | 71/116, .521160–.695793 | 72/580 | 3/15; R .2000; MRR .068889 | — |
| Sparse top-10 | .715517 | .073276 | .465897 | 83/116, .627536–.789681 | 85/1160 | 6/15; R .4000; MRR .095741 | — |
| MiniLM int8 top-5 | .625000 | .127586 | .477586 | 73/116, .538591–.711739 | 74/580 | 3/15; R .2000; MRR .057778 | 21.359 ms |
| MiniLM int8 top-10 | .741379 | .075862 | .492532 | 86/116, .654863–.812420 | 88/1160 | 6/15; R .4000; MRR .083042 | 21.253 ms |
| MiniLM fp32 top-5 | .616379 | .125862 | .482040 | 72/116, .529861–.703780 | 73/580 | 3/15; R .2000; MRR .105556 | 26.047 ms |
| MiniLM fp32 top-10 | .741379 | .075862 | .498902 | 86/116, .654863–.812420 | 88/1160 | 6/15; R .4000; MRR .130079 | 25.616 ms |
| E5 int8 top-5 | .625000 | .127586 | .455603 | 73/116, .538591–.711739 | 74/580 | 3/15; R .2000; MRR .072222 | 193.976 ms |
| **E5 int8 top-10 (winner)** | **.758621** | **.077586** | **.472876** | **88/116, .673268–.827393** | **90/1160** | **7/15; R .466667; MRR .108598** | **193.822 ms** |
| E5 fp32 top-5 | .633621 | .129310 | .457040 | 74/116, .547349–.719670 | 75/580 | 3/15; R .2000; MRR .072222 | 232.103 ms |
| E5 fp32 top-10 | .758621 | .077586 | .472448 | 88/116, .673268–.827393 | 90/1160 | 7/15; R .466667; MRR .108598 | 221.744 ms |
| MPNet int8 top-5 | .633621 | .129310 | .485057 | 74/116, .547349–.719670 | 75/580 | 3/15; R .2000; MRR .105556 | 34.151 ms |
| MPNet int8 top-10 | .715517 | .073276 | .495936 | 83/116, .627536–.789681 | 85/1160 | 6/15; R .4000; MRR .131746 | 34.716 ms |
| MPNet fp32 top-5 | .625000 | .127586 | .484052 | 73/116, .538591–.711739 | 74/580 | 3/15; R .2000; MRR .105556 | 55.599 ms |
| MPNet fp32 top-10 | .732759 | .075000 | .498437 | 85/116, .645718–.804877 | 87/1160 | 6/15; R .4000; MRR .130820 | 55.304 ms |
| E5 int8 + real BGE top-10 | .767241 | .078448 | .481760 | 89/116, .682531–.834819 | 91/1160 | 7/15; R .466667; MRR .102937 | 202.933 ms |

The real BGE row was executed in 12 serial chunks of 10 questions. It used
`BAAI/bge-reranker-v2-m3`, reported `bge_reranker` active in every chunk, and
accumulated `11,325.394 s` of local wall-clock. The chunk outputs covered all
120 question IDs exactly once; the full aggregate denominator remains 116.

### Quantization cost

For the selected E5 model:

- top-5 ceiling: fp32 `74/116` versus int8 `73/116` (one-question,
  `0.862` percentage-point decrease); MRR `.457040` versus `.455603`;
- top-10 ceiling: fp32 and int8 both `88/116`; MRR `.472448` versus `.472876`;
- mean query encoding: `221.744 ms` fp32 versus `193.822 ms` int8;
- self-contained artifact: `465.81 MiB` fp32 versus `130.17 MiB` int8.

The cost is measurable at top-5 and is not claimed to be zero. It disappears
from the top-10 ceiling while saving about 335.64 MiB, so this gate adopts int8
for the owner-selected b' product target. If top-5 fidelity becomes the primary
objective, fp32 remains the explicit alternative rather than a hidden fallback.

### Raw top-50 candidate pool

The selected E5 int8 hybrid raw top-50 path found a relevant chunk for `104/116`
answerable questions, leaving 12 hard candidate-pool misses:

`gold_email_usage_002`, `gold_training_regulation_047`,
`gold_credit_requirement_023`, `gold_training_regulation_233`,
`gold_training_regulation_163`, `gold_training_regulation_049`,
`gold_credit_requirement_032`, `gold_training_regulation_012`,
`gold_training_regulation_154`, `gold_credit_requirement_024`,
`gold_training_regulation_001`, `gold_curriculum_structure_014`.

The sparse control's prior raw top-50 ceiling was `107/116` with nine hard
misses. Dense restoration therefore improves selection at top-10 but does not
improve the raw hybrid candidate-pool ceiling; chunking/corpus coverage remains
the dominant residual limitation for those 12 rows.

## R5 — top-k and input-budget decision

`context_builder.py:35` still retrieves 50 candidates and `:88` still selects
`chunks[:top_k]`; changing top-k adds no retrieval/index cost.

- Sparse top-5 -> sparse top-10: `71/116` -> `83/116`, a `+12/116`
  (`+10.345 pp`) ceiling gain.
- E5 int8 top-5 -> top-10: `73/116` -> `88/116`, a `+15/116`
  (`+12.931 pp`) gain.
- E5 int8 + real BGE at top-10 adds only `+1/116` (`+0.862 pp`).

The default `top_k=5` is **not changed** in this gate. The measured E5-tokenizer
prompt sizes for the current `PromptBuilder` are:

| Selection | Mean | P50 | P95 | Max | Rows over 3000 |
|---|---:|---:|---:|---:|---:|
| top-5 | 3,080.61 | 3,120.5 | 3,552 | 3,654 | 75/120 |
| top-10 | 5,900.53 | 5,950.5 | 7,186 | 7,251 | 119/120 |

There is no `RAG_MAX_INPUT_TOKENS_SOFT` consumer in `app/`, `rag/`, or the
generation path, so neither top-5 nor top-10 is currently hard-truncated. The
configuration name is present in `.env` only; no value was printed. Top-10 is
therefore unsafe to adopt as the default until the generation gate implements a
tested input-budget policy. This gate does not fix that policy or RISK-0030.

## R6 — threshold verdict and recommendation

| Registered lever | Observed change | Pre-registered floor | Verdict |
|---|---:|---:|---|
| Sparse top-5 -> sparse top-10 | +10.345 pp | +5 pp | PASS |
| E5 dense top-5 over sparse top-5 | +1.724 pp | +5 pp | FAIL |
| E5 dense top-10 over sparse top-10 | +4.310 pp | +3 pp | PASS |
| Real BGE over E5 dense top-10 | +0.862 pp | +3 pp | FAIL |

The new best measured product retrieval ceiling is `89/116 = 76.72%` with E5
int8 plus real BGE at top-10. The selected dense/no-reranker product default at
top-10 is `88/116 = 75.86%`, compared with the original `71/116 = 61.21%`.
This is a retrieval ceiling, not answer correctness.

The retrieval path can support a viable product only with a constrained claim:
ONNX E5 materially improves selection-side grounding, but the raw hybrid pool
still misses 12 answerable questions and the current prompt budget is not
enforced. The remaining gap is therefore primarily hard candidate coverage,
chunking/corpus structure, and selection depth; this gate found no basis to
blame annotation quality as the dominant cause.

Recommended next gate: the generation gate. It must fix and test RISK-0030
`max_tokens`, the OpenRouter HTTP-200 embedded-error fallback, and the Groq
control decision, then run a fresh paired protocol. Do not start that gate from
this result without its own freeze.

## Gate 13-D correction addendum

Gate 13-D's reranker rows exercised `LexicalReranker`, not
`BAAI/bge-reranker-v2-m3`: `FlagEmbedding`/the transformer runtime was absent
and the code fell back. Its statement that the reranker did not help must
therefore not be read as evidence about the real BGE reranker.

This gate's controlled product comparison is the corrected evidence: E5 int8
without BGE reached `88/116` at top-10, while E5 int8 plus the real BGE
reranker reached `89/116`. The one-question lift fails the pre-registered +3 pp
reranker threshold. Gate 13-D's original findings are otherwise preserved;
this is an addendum, not a rewrite.

## Limitations and non-claims

- No provider generation call, GCP call, deployment, Cloud Run revision, Secret
  Manager call, IAM change, or `.env` edit occurred.
- The research lane and Gate 07/08 protocols, datasets, metrics, and artifacts
  were not read for recomputation or modified. The BGE reranker is a separate
  product-lane run.
- No answer quality, citation correctness, provider behavior, cloud-mode
  behavior, deployment readiness, concurrency, agent/MCP path, or final image
  delta was measured.
- Docker image delta and cold-start were not measured because the Docker daemon
  was unavailable. The `162.25 MiB` figure is a direct wheel+artifact total,
  not an image measurement.
- Generated model/vector binaries are ignored local artifacts; their metadata
  hashes are recorded above. Packaging them into a deployable image belongs to
  the later deployment gate blocked by RISK-0026.

## Closure

- Full suite: `598 passed, 3 warnings`.
- Final local release HEAD is `bcd924a020ba3d302721d8a2442063baebe04172`.
  Two bounded `git -c http.sslBackend=openssl push origin main` attempts failed
  with exit 1 and no output; `origin/main` remains
  `31a69c02fee68ab004c14a4ecd85eca563ae728f`. No remote release claim is made.
- The pre-existing 25-path overlay was not staged.
