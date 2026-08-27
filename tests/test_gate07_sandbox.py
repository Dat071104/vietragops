"""Gate 07 sandbox isolation and execution tests."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import sys

from research.gate07.sandbox import Gate07SandboxStore, build_api


def test_gate07_surface_has_target_tool_count_and_unique_names():
    for version in ("v1", "v2", "v3"):
        definitions = build_api(version).definitions()
        assert 25 <= len(definitions) <= 40
        assert len({definition.name for definition in definitions}) == len(definitions)


def test_gate07_store_reset_is_reproducible_after_mutation():
    store = Gate07SandboxStore()
    initial = store.state_hash()
    api = build_api("v1", store)
    api.call("submit_course_enrollment", student_id="STU-0001", course_code="CRS-001", term_id="TERM-02")
    assert store.state_hash() != initial
    store.reset()
    assert store.state_hash() == initial
    assert store.snapshot() == Gate07SandboxStore().snapshot()


def test_gate07_state_hash_matches_in_a_fresh_subprocess():
    expected = Gate07SandboxStore().state_hash()
    code = "from research.gate07.sandbox import Gate07SandboxStore; print(Gate07SandboxStore().state_hash())"
    completed = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    assert completed.stdout.strip() == expected


def test_gate07_real_calls_cover_reads_and_mutations():
    read_api = build_api("v3", Gate07SandboxStore())
    assert read_api.call("find_course_catalog", course_code="CRS-001")["course_code"] == "CRS-001"
    assert read_api.call("get_course_summary_generalized", course_code="CRS-001")["credits"] >= 2
    write_api = build_api("v3", Gate07SandboxStore())
    result = write_api.call("finalize_paid_registration", learner_ref="STU-0001", section_ref="CRS-001::TERM-02", payment_status="paid")
    assert result["status"] == "registered"
    assert write_api.store.enrollments


def test_gate07_store_source_has_no_product_or_io_boundary():
    source_path = Path(__file__).parents[1] / "research" / "gate07" / "sandbox" / "store.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and "rag" in ast.unparse(node).casefold() for node in tree.body)
    forbidden = ("open(", "Path(", "sqlite", "httpx", "urllib")
    assert not any(token in source for token in forbidden)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and any(name in ast.unparse(node).casefold() for name in ("requests", "httpx", "urllib")) for node in tree.body)
