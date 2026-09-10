"""Extract frozen Gate 07 prediction outputs for the hidden-join cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from research.gate07.metrics.report import latest_attempts


CASE_IDS = (
    "G07-G-0127",
    "G07-G-0130",
    "G07-G-0133",
    "G07-G-0136",
    "G07-G-0139",
)
SOURCE_FILES = (
    "gates/artifacts/gate07/v4/offline_lexical.jsonl",
    "gates/artifacts/gate07/v4/offline_embedding.jsonl",
    "gates/artifacts/gate07/v4/offline_cross_encoder.jsonl",
    "gates/artifacts/gate07/v4/offline_controls.jsonl",
    "gates/artifacts/gate07/v4/llm_results.jsonl",
)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _join_observations(prediction: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(prediction, dict):
        return []
    observations: list[dict[str, Any]] = []
    for item in prediction.get("constructed_argument_values") or []:
        if not isinstance(item, dict) or not isinstance(item.get("arguments"), dict):
            continue
        arguments = item["arguments"]
        if "section_ref" in arguments:
            value = str(arguments["section_ref"])
            observations.append(
                {
                    "source": "constructed_literal",
                    "new_tool": item.get("new_tool"),
                    "value": value,
                    "separator": "::" if "::" in value else None,
                }
            )
    for transform in prediction.get("value_transforms") or []:
        if isinstance(transform, dict) and transform.get("kind") == "join":
            observations.append(
                {
                    "source": "value_transform",
                    "delimiter": transform.get("delimiter"),
                    "order": transform.get("order"),
                }
            )
    return observations


def _classify(observations: list[dict[str, Any]]) -> str:
    if any(item.get("separator") == "::" or item.get("delimiter") == "::" for item in observations):
        return "sandbox_join"
    if observations:
        return "different_separator"
    return "no_join"


def build_report(repo_root: str | Path = ".") -> dict[str, Any]:
    root = Path(repo_root)
    rows: list[dict[str, Any]] = []
    source_receipts: list[dict[str, Any]] = []
    for relative in SOURCE_FILES:
        path = root / relative
        raw_rows = _load_rows(path)
        effective_rows = latest_attempts(raw_rows) if path.name == "llm_results.jsonl" else raw_rows
        source_receipts.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "raw_row_count": len(raw_rows),
                "effective_row_count": len(effective_rows),
            }
        )
        for row in effective_rows:
            if row.get("case_id") not in CASE_IDS:
                continue
            prediction = row.get("prediction")
            observations = _join_observations(prediction)
            rows.append(
                {
                    "source": relative,
                    "case_id": row.get("case_id"),
                    "arm_id": row.get("arm_id"),
                    "model": row.get("model"),
                    "prompt_id": row.get("prompt_id"),
                    "outcome": row.get("outcome"),
                    "failure_kind": row.get("failure_kind"),
                    "selected_tool_names": (prediction or {}).get("selected_tool_names") if isinstance(prediction, dict) else None,
                    "argument_pairs": (prediction or {}).get("argument_pairs") if isinstance(prediction, dict) else None,
                    "value_transforms": (prediction or {}).get("value_transforms") if isinstance(prediction, dict) else None,
                    "constructed_argument_values": (prediction or {}).get("constructed_argument_values") if isinstance(prediction, dict) else None,
                    "join_observations": observations,
                    "join_classification": _classify(observations),
                }
            )
    rows.sort(key=lambda row: (row.get("arm_id") or "", row.get("model") or "", row.get("case_id") or ""))
    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        key = f"{row.get('arm_id')}::{row.get('model')}"
        bucket = summary.setdefault(key, {"sandbox_join": 0, "different_separator": 0, "no_join": 0, "rows": 0})
        bucket[row["join_classification"]] += 1
        bucket["rows"] += 1
    return {
        "schema": "gate19.frozen_convention_extraction.v1",
        "cases": list(CASE_IDS),
        "case_count": len(CASE_IDS),
        "source_receipts": source_receipts,
        "rows": rows,
        "summary_by_arm_model": summary,
        "total_rows": len(rows),
        "sandbox_join_rows": sum(row["join_classification"] == "sandbox_join" for row in rows),
        "different_separator_rows": sum(row["join_classification"] == "different_separator" for row in rows),
        "no_join_rows": sum(row["join_classification"] == "no_join" for row in rows),
        "interpretation_boundary": "This is a read-only extraction of frozen parsed predictions. It does not infer a missing separator from evaluator execution and does not rescore any Gate 07/08 metric.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build_report(args.repo_root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": target.as_posix(), "total_rows": result["total_rows"], "sandbox_join_rows": result["sandbox_join_rows"], "different_separator_rows": result["different_separator_rows"], "no_join_rows": result["no_join_rows"]}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
