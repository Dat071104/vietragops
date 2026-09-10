"""Capture and re-verify the Gate 07/Gate 08 frozen-input hash manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


BASELINE_GLOBS = (
    "gates/baselines/GATE_07*.json",
    "gates/baselines/GATE_08*.json",
    "gates/results/GATE_07*.md",
    "gates/results/GATE_08*.md",
)
ARTIFACT_DIRS = ("gates/artifacts/gate07", "gates/artifacts/gate08")
CODE_DIRS = (
    "research/gate0/contracts",
    "research/gate0/evaluator",
    "research/gate07/dataset",
    "research/gate07/harness",
    "research/gate07/oracle",
    "research/gate07/traces",
    "research/gate07/sandbox",
    "research/gate07/metrics",
    "research/gate08/metrics",
)


def _files(root: Path) -> list[tuple[str, str]]:
    selected: dict[str, str] = {}
    for pattern in BASELINE_GLOBS:
        for path in root.glob(pattern):
            if path.is_file():
                selected[path.as_posix()] = "frozen_protocol_or_result"
    for relative in ARTIFACT_DIRS:
        directory = root / relative
        if directory.exists():
            for path in directory.rglob("*"):
                if path.is_file():
                    selected[path.as_posix()] = "frozen_raw_artifact"
    for relative in CODE_DIRS:
        directory = root / relative
        if directory.exists():
            for path in directory.rglob("*.py"):
                selected[path.as_posix()] = "frozen_code_surface"
            for path in directory.rglob("*.ts"):
                selected[path.as_posix()] = "frozen_code_surface"
    return sorted((str(Path(path).relative_to(root)).replace("\\", "/"), role) for path, role in selected.items())


def capture(root: str | Path) -> dict:
    root_path = Path(root).resolve()
    files = []
    for relative, role in _files(root_path):
        path = root_path / relative
        data = path.read_bytes()
        files.append(
            {
                "path": relative,
                "role": role,
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {
        "schema": "gate19.frozen_source_hashes.v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root_path),
        "file_count": len(files),
        "files": files,
    }


def verify(root: str | Path, manifest: dict) -> dict:
    root_path = Path(root).resolve()
    comparisons = []
    for entry in manifest.get("files", []):
        path = root_path / entry["path"]
        if not path.exists():
            comparisons.append({"path": entry["path"], "status": "MISSING"})
            continue
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        comparisons.append(
            {
                "path": entry["path"],
                "expected_sha256": entry["sha256"],
                "actual_sha256": actual,
                "status": "UNCHANGED" if actual == entry["sha256"] else "CHANGED",
            }
        )
    counts = {}
    for row in comparisons:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema": "gate19.frozen_source_hash_verification.v1",
        "manifest_schema": manifest.get("schema"),
        "file_count": len(comparisons),
        "status_counts": counts,
        "comparisons": comparisons,
        "all_unchanged": all(row["status"] == "UNCHANGED" for row in comparisons),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    if args.verify:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result = verify(args.root, manifest)
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0 if result["all_unchanged"] else 1
    result = capture(args.root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": manifest_path.as_posix(), "file_count": result["file_count"]}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
