from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalEvalRequest(BaseModel):
    chunks_path: str
    qa_path: str
    retriever: str = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)


class GenerationEvalRequest(BaseModel):
    chunks_path: str
    qa_path: str
    retriever: str = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    reranker: bool = False
    guardrails: bool = True
    source_priority: bool = False


class EvalResponse(BaseModel):
    experiment_id: str
    metrics: dict


class ExperimentSummary(BaseModel):
    experiment_id: str
    experiment_type: str
    file_path: str
