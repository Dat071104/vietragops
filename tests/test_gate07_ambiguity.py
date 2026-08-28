"""Gate 07 v3 ambiguity-audit receipt checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def test_gate07_ambiguity_receipt_matches_blind_public_sample_and_labels():
    root = Path(__file__).parents[1]
    receipt = json.loads((root / "gates" / "baselines" / "GATE_07_AMBIGUITY_AUDIT_V3.json").read_text(encoding="utf-8"))
    artifacts = root / "gates" / "artifacts" / "gate07" / "v3"
    sample = json.loads((artifacts / "ambiguity_public_sample.json").read_text(encoding="utf-8"))
    labels = json.loads((artifacts / "ambiguity_agy_annotations.json").read_text(encoding="utf-8"))["labels"]
    assert receipt["status"] == "completed"
    assert receipt["annotator"]["oracle_in_context"] is False
    assert len(sample) == len(labels) == 36
    assert hashlib.sha256((artifacts / "ambiguity_public_sample.json").read_bytes()).hexdigest() == receipt["sample"]["public_sha256"].removeprefix("sha256:")
    assert hashlib.sha256((artifacts / "ambiguity_agy_annotations.json").read_bytes()).hexdigest() == receipt["annotations"]["sha256"].removeprefix("sha256:")
    sample_fields = {key for item in sample for key in item}
    task_fields = {key for item in sample for key in item["task"]}
    assert not any(key in sample_fields or key in task_fields for key in ("family", "oracle", "expected_tool_names", "expected_argument_pairs", "ground_truth", "lineage_key"))
    assert receipt["disagreement"]["disagreements"] == 5
    assert receipt["oracle_corrections"]["count"] == 0
