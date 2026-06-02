from __future__ import annotations

from fastapi import FastAPI

from app.api import routes_agent, routes_documents, routes_eval, routes_health, routes_query, routes_retrieval
from app.core.errors import AppError, app_error_handler, generic_error_handler
from app.core.logging import setup_logging


setup_logging()

app = FastAPI(title="VietRAGOps API", version="0.1.0")
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.include_router(routes_health.router)
app.include_router(routes_documents.router)
app.include_router(routes_retrieval.router)
app.include_router(routes_query.router)
app.include_router(routes_agent.router)
app.include_router(routes_eval.router)
