from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# This app's own repo root (VietRagOps/.env) -- same file/convention
# `scripts/web_import.py` already uses (`_REPO_ROOT / ".env"`). Loaded here,
# before any other project import: at least one transitive dependency
# (markitdown, imported deep inside rag.lifecycle.pipeline) calls a bare
# `load_dotenv()` of its own at import time, which would otherwise beat this
# explicit load to the punch and set empty/partial values into `os.environ`
# first. `load_dotenv()` defaults to never overriding an already-set
# variable, so loading this file any later -- e.g. after importing
# `app.api`/`app.core.config` -- can silently lose to that. `override=True`
# makes this explicit load authoritative regardless of import order
# elsewhere.
ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


def should_load_dotenv() -> bool:
    return os.environ.get("PYTHON_DOTENV_DISABLED", "").strip().casefold() not in {"1", "true", "yes", "on"}


if should_load_dotenv():
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from app.api import routes_admin, routes_agent, routes_documents, routes_eval, routes_health, routes_query, routes_retrieval  # noqa: E402
from app.core.config import get_mcp_server  # noqa: E402
from app.core.errors import AppError, app_error_handler, generic_error_handler  # noqa: E402
from app.core.logging import setup_logging  # noqa: E402

setup_logging()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    # The MCP Streamable HTTP session manager owns its own request-scoped
    # task group and must be entered exactly once per process, from the
    # actual top-level ASGI app's lifespan -- a mounted sub-app's own
    # `lifespan=` is never triggered by Starlette/FastAPI automatically.
    async with get_mcp_server().mcp_server.session_manager.run():
        yield


app = FastAPI(title="VietRAGOps API", version="0.1.0", lifespan=_lifespan)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(routes_health.router)
app.include_router(routes_admin.router)
app.include_router(routes_documents.router)
app.include_router(routes_retrieval.router)
app.include_router(routes_query.router)
app.include_router(routes_agent.router)
app.include_router(routes_eval.router)
app.mount("/mcp", get_mcp_server().asgi_app)
