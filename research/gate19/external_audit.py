"""Apply the Gate 19 auditor to the hand-verified external pair register."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from research.gate19.auditor import audit_items


def build_audit_input(register: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for pair in register["pairs"]:
        tool = pair["new_tool"]
        target = pair["target_field"]
        items.append(
            {
                "item_id": pair["pair_id"],
                "item_type": "external_contract_change",
                "family": "external_mcp_version_pairs",
                "case_id": pair["pair_id"],
                "old_tool": None,
                "old_arg": None,
                "new_tool": tool,
                "new_arg": target,
                "target_value": pair["target_value"],
                "source_values": [],
                "visible_source_values": [],
                "visible_text": [
                    pair["old_observable"],
                    pair["new_observable"],
                    pair["commit_url"],
                ],
                "new_contract_fields": {tool: [target]},
                "derivation": {
                    "status": "observable",
                    "reason": pair["judgement_reason"],
                },
                "external_provenance": {
                    "repository": register["repository"],
                    "old_commit": pair["old_commit"],
                    "new_commit": pair["new_commit"],
                    "artifact_path": pair["artifact_path"],
                    "license": register["repository_license_note"],
                },
            }
        )
    return items


def build(register_path: str | Path, rights_path: str | Path) -> dict[str, Any]:
    register_file = Path(register_path)
    rights = json.loads(Path(rights_path).read_text(encoding="utf-8"))
    register = json.loads(register_file.read_text(encoding="utf-8"))
    items = build_audit_input(register)
    audit = audit_items(items, rights)
    return {
        "schema": "gate19.external_mcp_audit.v1",
        "register": register_file.as_posix().replace("\\", "/"),
        "register_sha256": hashlib.sha256(register_file.read_bytes()).hexdigest(),
        "repository": register["repository"],
        "pair_count": len(register["pairs"]),
        "audit": audit,
        "limitation": "This is a hand-verified source-pair sample, not a claim about prevalence across all MCP servers. A zero unreachable count does not validate the local defect externally; it records that this sample did not reproduce it under the declared naive rights.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True)
    parser.add_argument("--rights", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build(args.register, args.rights)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    summary = result["audit"]["families"]["external_mcp_version_pairs"]
    print(json.dumps({"output": target.as_posix(), "pair_count": result["pair_count"], "status_counts": summary["status_counts"]}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
