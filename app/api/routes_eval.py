from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.core.errors import AppError
from app.schemas.eval import EvalResponse, ExperimentSummary, GenerationEvalRequest, RetrievalEvalRequest
from evals.experiments.run_generation_eval import GenerationEvalConfig, run_generation_eval
from evals.experiments.run_retrieval_eval import run_eval


router = APIRouter(tags=["eval"])


@router.post("/eval/retrieval", response_model=EvalResponse)
def eval_retrieval(payload: RetrievalEvalRequest) -> EvalResponse:
    result = run_eval(payload.chunks_path, payload.qa_path, payload.retriever, payload.top_k)
    return EvalResponse(experiment_id=result["experiment_id"], metrics=result["metrics"])


@router.post("/eval/generation", response_model=EvalResponse)
def eval_generation(payload: GenerationEvalRequest) -> EvalResponse:
    result = run_generation_eval(
        GenerationEvalConfig(
            chunks_path=payload.chunks_path,
            qa_path=payload.qa_path,
            retriever=payload.retriever,
            top_k=payload.top_k,
            reranker=payload.reranker,
            guardrails=payload.guardrails,
            source_priority=payload.source_priority,
        )
    )
    return EvalResponse(experiment_id=result["experiment_id"], metrics=result["metrics"])


@router.get("/experiments", response_model=list[ExperimentSummary])
def list_experiments() -> list[ExperimentSummary]:
    summaries = []
    for path in sorted((Path("dist") / "experiments").rglob("*.json")):
        summaries.append(
            ExperimentSummary(
                experiment_id=path.stem,
                experiment_type=path.parent.name,
                file_path=str(path),
            )
        )
    return summaries


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    for path in (Path("dist") / "experiments").rglob(f"{experiment_id}.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise AppError("Experiment not found.", status_code=404)
