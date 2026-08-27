# Third-Party Tooling — Local Preparation Record

**Status:** `Prepared locally; not integrated into VietRAGOps runtime`

## Locations and Pins

| Tool | Upstream | Pinned revision | Local path | Local verification |
| --- | --- | --- | --- | --- |
| MarkItDown | `https://github.com/microsoft/markitdown` | `9dc0d6579b8739c9d0671ff205e071e3053c7df1` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\markitdown` | isolated Python 3.14 venv; `markitdown=0.1.7`; import + CLI help pass |
| Firecrawl | `https://github.com/firecrawl/firecrawl` | `d26ad4bbf2fe1d0be3b8bb4a94bfe8baa2c15e72` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\firecrawl` | local `.env`; `docker compose config --quiet` pass; no service started |
| BGE-M3 bi-encoder | `https://huggingface.co/BAAI/bge-m3` | `5617a9f61b028005a4858fdac845db406aefb181` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\research_baselines\models\bge-m3` | isolated Python 3.13.9; offline `SentenceTransformer` load + CPU encode pass; shape `(1, 1024)` |
| BGE reranker cross-encoder | `https://huggingface.co/BAAI/bge-reranker-v2-m3` | `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\research_baselines\models\bge-reranker-v2-m3` | isolated Python 3.13.9; offline `CrossEncoder` load + CPU pair score pass |

## Boundary

`external_tools/` is intentionally outside the application Git root
`VietRagOps/`. It must not be staged as application code. Before use, verify the
recorded revision and `git status` inside the relevant checkout.

## Gate 07 Research Baselines

The Gate 07 research-only interpreter is:

```text
D:\Project cua Dat\VietRAGOps\ROOT\external_tools\research_baselines\.venv\Scripts\python.exe
```

It contains `torch==2.13.0+cpu`, `sentence-transformers==6.0.0`,
`transformers==5.16.1`, `huggingface_hub==1.28.0`,
`scikit-learn==1.9.0`, `scipy==1.18.1`, `numpy==2.5.2`,
`tokenizers==0.23.1`, and `safetensors==0.8.0`, with the full environment
verified by `pip freeze` on 2026-08-27. The two model snapshots were
downloaded once at the exact revisions above and loaded with
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, and `local_files_only=True`.

The application `VietRagOps/.venv` remains isolated: its import probe reports
`torch=False`, `sentence_transformers=False`, and `transformers=False`. The
application `requirements.txt` SHA-256 is unchanged at
`69CFB7E4CA54FDF4CC7AB9BA1322F68C6FC2E747C6AF32D95400E1FD6D9A0B26`.
Application retrieval-smoke control metrics before and after the research
install are identical to the Gate 04 frozen control:
`recall_at_3=0.7222`, `recall_at_5=0.8889`, `recall_at_10=0.8889`,
`mrr=0.5917`, `precision_at_5=0.1889`, `answerable=18/20`.
The two smoke outputs were temporary control artifacts used for the comparison
and then cleaned; the recorded metrics are the control evidence, not modified
Gate 04 source or evidence.

## MarkItDown Setup

The isolated interpreter is:

```text
D:\Project cua Dat\VietRAGOps\ROOT\external_tools\markitdown\.venv\Scripts\python.exe
```

Installed editable extras are `pdf`, `docx`, `pptx`, and `xlsx`. This excludes
OCR/cloud plugins and does not alter `VietRagOps/.venv` or `requirements.txt`.
Gate 02 must still add validated input, comparison, fallback and publish controls.

## Firecrawl Setup

- `external_tools\firecrawl\.env` is a minimal localhost-only self-host baseline
  ignored by that checkout.
- It uses no provider, proxy, database-auth, webhook, Supabase, or admin secret.
- It is configuration-validated only. Do not run `up` until Gate 03 authorizes a
  bounded test and an isolated service/port/persistence plan exists.
- Firecrawl self-hosting is not needed for the future hosted API adapter. The
  app-facing secret handoff is `VietRagOps\.env.firecrawl.local`.

### Hosted API-key handoff (when Gate 03 permits it)

1. Create/retrieve **your own authorized** key at
   `https://www.firecrawl.dev/app/api-keys`.
2. Paste it directly on this machine into the ignored
   `VietRagOps\.env.firecrawl.local` as `FIRECRAWL_API_KEY=...`.
3. Do not paste the key into chat, logs, screenshots, `_agent_ops`, or any Git
   command. Confirm only that the local file is populated.
4. This is a credential handoff, not permission to make an API call or bypass
   Gate 03's candidate, SSRF, budget, and review controls.

## Update Rule

Do not `git pull` either checkout implicitly. Any revision update must record
old/new commits, source-compatible setup changes, security review and fresh local
verification here and in the implementation log.
