# VietRAGOps

VietRAGOps is a Vietnamese retrieval-augmented generation (RAG) demo focused on grounded academic-policy question answering.

It is designed to help users ask questions about university regulations, curriculum structure, credits, and related policy documents while keeping answers tied to retrieved evidence instead of unsupported model guesses.

## What This Project Does

- Retrieves relevant chunks from a prepared academic-policy corpus.
- Answers with citations to the retrieved chunks.
- Supports a safe `/ask` flow for standard grounded QA.
- Supports a demo-friendly `/agent/ask` flow with local-agent behavior, tool tracing, and verified fallback.
- Includes a Streamlit frontend for interactive demos.
- Includes evaluation and experiment endpoints for retrieval and generation workflows.

## Main Features

- Grounded answering with citation verification
- FastAPI backend
- Streamlit frontend
- Hybrid retrieval pipeline
- Strict refusal behavior for private, unsupported, or out-of-scope questions
- Optional local Ollama integration
- Optional provider routing between `mock`, `groq`, and `ollama`

## Architecture Overview

The project is organized into a few main parts:

- `app/`: FastAPI application, routes, schemas, and app configuration
- `rag/`: retrieval, context building, grounding, citation verification, and generation logic
- `frontend/`: Streamlit demo UI
- `evals/`: evaluation utilities and experiment runners
- `scripts/`: chunk validation, Ollama checks, and processing helpers
- `tests/`: automated test suite

## API Endpoints

Core routes exposed by the backend include:

- `GET /health`
  Returns API health and provider status information.

- `POST /ask`
  Standard grounded QA endpoint. This keeps the original response contract and is intended for normal use.

- `POST /agent/ask`
  Local Agent demo endpoint. This can use optional local Ollama generation, internal retrieval, tool-call tracing, verified fallback, and citation-safe answering.

- `POST /retrieve`
  Returns retrieved chunks for a question.

- `GET /documents`
- `GET /documents/{doc_id}`
- `POST /documents/upload`
- `POST /documents/index`

- `POST /eval/retrieval`
- `POST /eval/generation`
- `GET /experiments`
- `GET /experiments/{experiment_id}`

## Local Agent Behavior

The Local Agent tab and `/agent/ask` are designed to be demo-safe:

- If the local model answers cleanly with verifiable citations, the response is shown directly.
- If the model produces invalid citations, the app does not trust them blindly.
- Instead, it can fall back to a verified grounded answer rebuilt from real retrieved chunks.
- Private or unsupported questions are still refused.

This makes the demo safer for local LLM use, especially with smaller models.

## Optional Ollama Mode

Ollama is optional. The project should still work in non-Ollama modes.

Supported provider values:

- `LLM_PROVIDER=mock`
- `LLM_PROVIDER=groq`
- `LLM_PROVIDER=ollama`

Recommended local Ollama variables:

```powershell
$env:LLM_PROVIDER="ollama"
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="qwen2.5:3b"
$env:OLLAMA_NUM_CTX="8192"
```

If you want to verify your local Ollama setup:

```powershell
python scripts/check_ollama.py
```

## Running The Backend

Start the API locally with:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful smoke checks:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Example `/agent/ask` request:

```powershell
@'
{
  "question": "Cấu trúc email sinh viên TDTU là gì?",
  "top_k": 5,
  "return_debug": true
}
'@ | Set-Content -Path .\tmp_agent.json -Encoding utf8

curl.exe -s -X POST "http://127.0.0.1:8000/agent/ask" `
  -H "Content-Type: application/json; charset=utf-8" `
  --data-binary "@tmp_agent.json"
```

## Running The Frontend

Start the Streamlit app with:

```powershell
streamlit run frontend/streamlit_app.py
```

The frontend includes:

- standard QA
- retrieval inspection
- evaluation views
- Local Agent tab
- provider and Ollama status display
- citations and tool-call trace display

## Example Questions

Good in-scope demo questions:

- `Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?`
- `Cấu trúc email sinh viên TDTU là gì?`

Questions that should be refused:

- `Học phí kỳ này của tôi là bao nhiêu?`
- `Tôi nên mua laptop nào?`

## Testing And Validation

Useful commands for local verification:

```powershell
python -m compileall app rag evals frontend scripts tests
pytest -q
python scripts/check_ollama.py
python scripts/validate_chunks.py --chunks-dir data/chunks
docker compose config
```

## Streamlit Deployment

Live demo URL:

`Coming soon`

When your Streamlit deployment is ready, replace that line with your public app URL.

## Project Goals

This project aims to demonstrate:

- grounded Vietnamese QA over institutional documents
- safe local-LLM integration
- clear citations
- strict refusal handling when evidence is missing
- practical RAG evaluation and demo workflows

## Notes For This Public Repo

- Do not commit real API keys or secrets.
- Keep local environment files out of version control.
- Keep generated caches and temporary files ignored.
- If you publish the repo, make sure the actual source `.py` files are included, not only generated `__pycache__` artifacts.

## License

Add your preferred license here before broad public sharing.
