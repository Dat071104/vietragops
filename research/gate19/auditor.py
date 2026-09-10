"""Reusable Gate 19 oracle-reachability auditor.

The auditor intentionally audits argument-level target items. It does not infer
semantic equivalence and it does not read evaluator-only truth at run time
except in the frozen-input builder used to create an auditable input register.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Iterable


REACHABLE = "REACHABLE"
TARGET_ABSENT = "UNREACHABLE-TARGET-ABSENT"
CONVENTION_UNOBSERVABLE = "UNREACHABLE-CONVENTION-UNOBSERVABLE"
STATUSES = {REACHABLE, TARGET_ABSENT, CONVENTION_UNOBSERVABLE}


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _fields_for_tool(item: dict[str, Any], tool_name: str) -> set[str]:
    declared = item.get("new_contract_fields", {})
    if isinstance(declared, dict):
        fields = declared.get(tool_name, [])
    else:
        fields = []
    return {value for value in fields if isinstance(value, str)}


def _visible_text(item: dict[str, Any]) -> str:
    values = item.get("visible_text", [])
    if isinstance(values, str):
        return values
    if not isinstance(values, list):
        return ""
    return "\n".join(_as_text(value) for value in values)


def _source_values(item: dict[str, Any]) -> list[str]:
    values = item.get("visible_source_values", item.get("source_values", []))
    if not isinstance(values, list):
        values = [values]
    return [_as_text(value) for value in values if value is not None]


def _find_hidden_join(target: str, source_values: list[str], visible_text: str) -> dict[str, Any] | None:
    """Find a target made from two visible values with an unobserved separator."""

    for left_index, left in enumerate(source_values):
        for right_index, right in enumerate(source_values):
            if left_index == right_index or not target.startswith(left) or not target.endswith(right):
                continue
            separator = target[len(left) : len(target) - len(right)] if right else target[len(left) :]
            if not separator:
                continue
            if separator not in visible_text:
                return {
                    "kind": "join",
                    "left_index": left_index,
                    "right_index": right_index,
                    "separator": separator,
                    "separator_observable": False,
                }
    return None


def _visible_split(target: str, source_values: list[str]) -> dict[str, Any] | None:
    """Recognize only a split whose delimiter is literally present in a source value."""

    for source_index, source in enumerate(source_values):
        for delimiter in ("::", ":", "|", "/", "-", "_", ".", "~", ","):
            if delimiter not in source:
                continue
            pieces = source.split(delimiter, 1)
            if target in pieces and target != source:
                return {
                    "kind": "split",
                    "source_index": source_index,
                    "delimiter": delimiter,
                    "delimiter_observable": True,
                }
    return None


def classify_item(item: dict[str, Any], rights: dict[str, Any]) -> dict[str, Any]:
    """Classify one argument target under a declared rights declaration."""

    required = {"item_id", "new_tool", "new_arg", "new_contract_fields"}
    missing = sorted(required - set(item))
    if missing:
        raise ValueError(f"item {item.get('item_id', '<unknown>')} is missing {missing}")

    fields = _fields_for_tool(item, item["new_tool"])
    target_value = item.get("target_value")
    source_values = _source_values(item)
    visible_text = _visible_text(item)
    base = {
        "item_id": item["item_id"],
        "case_id": item.get("case_id"),
        "family": item.get("family"),
        "old_tool": item.get("old_tool"),
        "old_arg": item.get("old_arg"),
        "new_tool": item["new_tool"],
        "new_arg": item["new_arg"],
        "target_value": target_value,
        "target_field_declared": item["new_arg"] in fields,
        "source_values": source_values,
    }

    if item["new_arg"] not in fields:
        return {
            **base,
            "status": TARGET_ABSENT,
            "reason": "new_arg is not a declared input field of the method-visible new contract",
            "derivation": None,
        }
    if target_value is None:
        return {
            **base,
            "status": TARGET_ABSENT,
            "reason": "the target field is declared but no target value is present in the supplied ground-truth item",
            "derivation": None,
        }

    target_text = _as_text(target_value)
    if target_text in source_values:
        return {
            **base,
            "status": REACHABLE,
            "reason": "target equals a visible source value",
            "derivation": {"kind": "identity"},
        }

    hidden_join = _find_hidden_join(target_text, source_values, visible_text)
    if hidden_join is not None:
        return {
            **base,
            "status": CONVENTION_UNOBSERVABLE,
            "reason": "target requires a join separator absent from the declared method-visible surface",
            "derivation": hidden_join,
        }

    split = _visible_split(target_text, source_values)
    if split is not None:
        return {
            **base,
            "status": REACHABLE,
            "reason": "target is a component of a visible source value using an observed delimiter",
            "derivation": split,
        }

    external = item.get("derivation")
    if isinstance(external, dict) and external.get("status") == "observable":
        return {
            **base,
            "status": REACHABLE,
            "reason": external.get("reason", "hand-verified observable derivation"),
            "derivation": external,
        }

    return {
        **base,
        "status": CONVENTION_UNOBSERVABLE,
        "reason": "no derivation rule is evidenced by the declared information rights",
        "derivation": None,
    }


def audit_items(items: Iterable[dict[str, Any]], rights: dict[str, Any]) -> dict[str, Any]:
    """Audit declared items and return per-item and aggregated results."""

    audited = [classify_item(item, rights) for item in items]
    by_family: dict[str, dict[str, Any]] = {}
    families = sorted({item.get("family") or "<unknown>" for item in audited})
    for family in families:
        rows = [item for item in audited if (item.get("family") or "<unknown>") == family]
        counts = Counter(item["status"] for item in rows)
        pair_count = len(rows)
        cases = {item["case_id"] for item in rows if item.get("case_id")}
        convention_cases = {
            item["case_id"]
            for item in rows
            if item["status"] == CONVENTION_UNOBSERVABLE and item.get("case_id")
        }
        by_family[family] = {
            "pairs": pair_count,
            "status_counts": {status: counts.get(status, 0) for status in sorted(STATUSES)},
            "unreachable_pairs": pair_count - counts.get(REACHABLE, 0),
            "unreachable_share": round((pair_count - counts.get(REACHABLE, 0)) / pair_count, 10) if pair_count else None,
            "max_attainable_recall": round(counts.get(REACHABLE, 0) / pair_count, 10) if pair_count else None,
            "case_count": len(cases),
            "convention_case_count": len(convention_cases),
            "convention_case_share": round(len(convention_cases) / len(cases), 10) if cases else None,
            "convention_case_ids": sorted(convention_cases),
        }

    return {
        "schema": "gate19.oracle_reachability_audit.v1",
        "criterion": "Target and every construction step must be derivable from the declared information rights.",
        "rights_schema": rights.get("schema"),
        "item_count": len(audited),
        "items": audited,
        "families": by_family,
    }


def build_gate07_items() -> list[dict[str, Any]]:
    """Build argument-pair items from the frozen V4/V4.1 method surface."""

    from research.gate0.evaluator.capability import EvaluatorCapability
    from research.gate07.dataset.generator import build_v4_cases
    from research.gate07.harness.serialization import task_record
    from research.gate07.oracle.ground_truth import all_ground_truth

    cases = {case.case_id: case for case in build_v4_cases() if not case.held_out}
    capability = EvaluatorCapability()
    truth_by_id = {
        truth.case_id: truth for truth in all_ground_truth(capability, graded_only=True) if truth.case_id in cases
    }
    items: list[dict[str, Any]] = []
    for case_id, case in sorted(cases.items()):
        truth = truth_by_id[case_id]
        if not truth.argument_pairs:
            continue
        task = task_record(case)
        fields = {
            contract["name"]: sorted((contract.get("input_schema") or {}).get("properties", {}))
            for contract in task["new_contracts"]
        }
        correct_inputs = dict(zip(truth.correct_new_tool_names, case.new_inputs))
        all_old_values = [value for mapping in case.old_inputs for value in mapping.values()]
        visible_text = [json.dumps(task, ensure_ascii=True, sort_keys=True, separators=(",", ":"))]
        for index, (old_tool, old_arg, new_tool, new_arg) in enumerate(truth.argument_pairs):
            old_index = case.old_tool_names.index(old_tool)
            old_value = case.old_inputs[old_index].get(old_arg)
            target_value = correct_inputs.get(new_tool, {}).get(new_arg)
            items.append(
                {
                    "item_id": f"{case_id}#argument_pair_{index:02d}",
                    "case_id": case_id,
                    "family": truth.family,
                    "old_tool": old_tool,
                    "old_arg": old_arg,
                    "old_value": old_value,
                    "new_tool": new_tool,
                    "new_arg": new_arg,
                    "target_value": target_value,
                    "source_values": [old_value],
                    "visible_source_values": all_old_values,
                    "visible_text": visible_text,
                    "new_contract_fields": fields,
                    "frozen_source": {
                        "ground_truth": "research/gate07/oracle/ground_truth.py",
                        "method_surface": "research/gate07/harness/method_facing.py",
                        "case_source": "research/gate07/dataset/generator.py::build_v4_cases",
                    },
                }
            )
    return items


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rights", required=True, help="Machine-readable rights declaration JSON")
    parser.add_argument("--input", help="JSON array of auditor items; omit to build frozen Gate 07 items")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()
    rights = _load_json(args.rights)
    items = _load_json(args.input) if args.input else build_gate07_items()
    if not isinstance(items, list):
        raise SystemExit("input must be a JSON array")
    result = audit_items(items, rights)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": target.as_posix(), "item_count": result["item_count"], "families": result["families"]}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
