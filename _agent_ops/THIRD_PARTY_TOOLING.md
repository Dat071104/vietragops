# Third-Party Tooling — Local Preparation Record

**Status:** `Prepared locally; not integrated into VietRAGOps runtime`

## Locations and Pins

| Tool | Upstream | Pinned revision | Local path | Local verification |
| --- | --- | --- | --- | --- |
| MarkItDown | `https://github.com/microsoft/markitdown` | `9dc0d6579b8739c9d0671ff205e071e3053c7df1` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\markitdown` | isolated Python 3.14 venv; `markitdown=0.1.7`; import + CLI help pass |
| Firecrawl | `https://github.com/firecrawl/firecrawl` | `d26ad4bbf2fe1d0be3b8bb4a94bfe8baa2c15e72` | `D:\Project cua Dat\VietRAGOps\ROOT\external_tools\firecrawl` | local `.env`; `docker compose config --quiet` pass; no service started |

## Boundary

`external_tools/` is intentionally outside the application Git root
`VietRagOps/`. It must not be staged as application code. Before use, verify the
recorded revision and `git status` inside the relevant checkout.

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
