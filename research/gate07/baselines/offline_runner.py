"""CLI for the Phase 7.4 offline baseline arms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from research.gate07.baselines.models import RawOutputRecord
from research.gate07.baselines.offline import (
    _load_cross_encoder,
    _load_sentence_transformer,
    predict_cross_encoder_batch,
    predict_embedding_batch,
    predict_lexical,
)
from research.gate07.harness.serialization import load_public_tasks
from research.gate07.protocol import preflight_headline_run
from research.gate07.runner.artifacts import RawArtifactWriter


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=("lexical", "embedding", "cross_encoder"), required=True)
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--bi-model")
    parser.add_argument("--cross-model")
    return parser.parse_args()


def _write(output: Path, raw_writer: RawArtifactWriter, arm_id: str, model_name: str, task: dict, prediction: dict, scores: list[tuple[str, float]], elapsed_ms: float) -> None:
    raw = {"backend": "offline", "scores": [[name, score] for name, score in scores], "prediction": prediction}
    record = RawOutputRecord(arm_id, model_name, task["case_id"], None, json.dumps(task, ensure_ascii=True, sort_keys=True), json.dumps(raw, ensure_ascii=True, sort_keys=True), "offline", elapsed_ms, {}, "success")
    raw_writer.append(record)
    with output.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"arm_id": arm_id, "model": model_name, "case_id": task["case_id"], "prediction": prediction, "scores": [[name, score] for name, score in scores], "backend": "offline"}, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


def _run_streaming(tasks: list[dict], runners, output: Path, raw_writer: RawArtifactWriter) -> None:
    for task in tasks:
        for arm_id, model_name, runner in runners:
            started = time.perf_counter()
            prediction, scores = runner(task)
            _write(output, raw_writer, arm_id, model_name, task, prediction, scores, (time.perf_counter() - started) * 1000)


def _run_batched(tasks: list[dict], model, family: str, output: Path, raw_writer: RawArtifactWriter) -> list[str]:
    started = time.perf_counter()
    if family == "embedding":
        arms = (
            ("embed_name_desc", "BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181", True),
            ("embed_serialized_schema", "BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181", False),
        )
        results_by_arm = [(arm_id, model_name, predict_embedding_batch(tasks, model, names_and_description=names_only)) for arm_id, model_name, names_only in arms]
    else:
        results_by_arm = [("cross_encoder", "BAAI/bge-reranker-v2-m3@953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e", predict_cross_encoder_batch(tasks, model))]
    elapsed_ms = (time.perf_counter() - started) * 1000
    for arm_id, model_name, results in results_by_arm:
        for task, (prediction, scores) in zip(tasks, results):
            _write(output, raw_writer, arm_id, model_name, task, prediction, scores, elapsed_ms / max(1, len(tasks)))
    return [arm_id for arm_id, _, _ in results_by_arm]


def main() -> None:
    args = _args()
    preflight = preflight_headline_run(args.protocol)
    tasks = load_public_tasks(args.tasks)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    raw_path = Path(args.raw)
    raw_path.unlink(missing_ok=True)
    raw_writer = RawArtifactWriter(raw_path)
    runners = []
    arm_ids: list[str]
    if args.family == "lexical":
        runners = [("lexical_name", "deterministic_lexical_name", lambda task: predict_lexical(task, names_only=True)), ("lexical_serialized", "deterministic_lexical_serialized", lambda task: predict_lexical(task, names_only=False))]
        _run_streaming(tasks, runners, output, raw_writer)
        arm_ids = [arm_id for arm_id, _, _ in runners]
    elif args.family == "embedding":
        model = _load_sentence_transformer(args.bi_model)
        arm_ids = _run_batched(tasks, model, args.family, output, raw_writer)
    else:
        model = _load_cross_encoder(args.cross_model)
        arm_ids = _run_batched(tasks, model, args.family, output, raw_writer)
    print(json.dumps({"family": args.family, "tasks": len(tasks), "arms": arm_ids, "output": str(output), "raw": str(raw_writer.path), "preflight": preflight}, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
