"""Build the additive Gate 19 tool_replacement oracle and manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build(audit_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(audit_path)
    audit = _read(path)
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    items = [item for item in audit["items"] if item.get("family") == "tool_replacement"]
    manifest_rows: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    for item in items:
        retain = item["status"] == "REACHABLE"
        row = {
            "item_id": item["item_id"],
            "case_id": item.get("case_id"),
            "old_tool": item.get("old_tool"),
            "old_arg": item.get("old_arg"),
            "old_value": item.get("source_values", [None])[0] if item.get("source_values") else None,
            "new_tool": item.get("new_tool"),
            "new_arg": item.get("new_arg"),
            "original_target_value": item.get("target_value"),
            "reachability_status": item["status"],
            "action": "RETAIN" if retain else "EXCLUDE",
            "reason": item.get("reason"),
            "derivation": item.get("derivation"),
            "frozen_sources": [
                "research/gate07/oracle/ground_truth.py",
                "research/gate07/harness/method_facing.py",
                "research/gate07/dataset/generator.py::build_v4_cases",
                "gates/baselines/GATE_07_PROTOCOL_V4.json",
                "gates/baselines/GATE_08_PROTOCOL.json",
            ],
        }
        manifest_rows.append(row)
        if retain:
            retained.append(
                {
                    "item_id": row["item_id"],
                    "case_id": row["case_id"],
                    "old_tool": row["old_tool"],
                    "old_arg": row["old_arg"],
                    "new_tool": row["new_tool"],
                    "new_arg": row["new_arg"],
                    "target_value": row["original_target_value"],
                    "reachability_status": row["reachability_status"],
                    "derivation": row["derivation"],
                }
            )
    manifest = {
        "schema": "gate19.tool_replacement_oracle_manifest.v1",
        "version": "GATE_19_TOOL_REPLACEMENT_ORACLE_V1",
        "source_audit": path.as_posix().replace("\\", "/"),
        "source_audit_sha256": source_hash,
        "policy": "Retain only REACHABLE argument-pair items. Exclude target-absent and convention-unobservable items; do not invent replacement values.",
        "items": manifest_rows,
    }
    dataset = {
        "schema": "gate19.tool_replacement_oracle.v1",
        "version": "GATE_19_TOOL_REPLACEMENT_ORACLE_V1",
        "source_manifest": "gates/baselines/GATE_19_TOOL_REPLACEMENT_ORACLE_V1_MANIFEST.json",
        "source_audit": path.as_posix().replace("\\", "/"),
        "source_audit_sha256": source_hash,
        "scope": "Reachable argument-pair targets only; Gate 07 and Gate 08 case-level metrics are not rescored here.",
        "retained_items": retained,
    }
    return dataset, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    dataset, manifest = build(args.audit)
    dataset_path = Path(args.dataset)
    manifest_path = Path(args.manifest)
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_text(json.dumps(dataset, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": dataset_path.as_posix(), "manifest": manifest_path.as_posix(), "retained_items": len(dataset["retained_items"]), "manifest_items": len(manifest["items"])}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
