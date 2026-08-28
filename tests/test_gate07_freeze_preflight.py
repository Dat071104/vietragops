"""Mechanical freeze-order checks for Gate 07 headline runners."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import types

import pytest

from research.gate07.baselines import offline_runner
from research.gate07.dataset import build_all_cases
from research.gate07.protocol import FreezePreflightError, build_protocol, dataset_manifest_digests, preflight_headline_run, write_protocol
from research.gate07.runner import llm


def _git(repo: Path, *args: str) -> None:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def _protocol_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate07-test@example.invalid")
    _git(repo, "config", "user.name", "Gate 07 Test")
    bootstrap = repo / "README.md"
    bootstrap.write_text("bootstrap\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "bootstrap")
    protocol_path = repo / "gates" / "baselines" / "protocol.json"
    write_protocol(build_protocol(build_all_cases(), ("model/test",), repo_root=repo, created_at="2026-08-28T00:00:00+00:00"), protocol_path)
    _git(repo, "add", "--", "gates/baselines/protocol.json")
    _git(repo, "commit", "-m", "freeze")
    return repo, protocol_path


def test_gate07_dirty_protocol_blocks(tmp_path: Path):
    repo, protocol_path = _protocol_repo(tmp_path)
    protocol_path.write_text(protocol_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(FreezePreflightError, match="dirty or uncommitted"):
        preflight_headline_run(protocol_path, repo_root=repo)


def test_gate07_uncommitted_protocol_blocks(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "gate07-test@example.invalid")
    _git(repo, "config", "user.name", "Gate 07 Test")
    bootstrap = repo / "README.md"
    bootstrap.write_text("bootstrap\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "bootstrap")
    protocol_path = repo / "gates" / "baselines" / "protocol.json"
    write_protocol(build_protocol(build_all_cases(), ("model/test",), repo_root=repo, created_at="2026-08-28T00:00:00+00:00"), protocol_path)
    with pytest.raises(FreezePreflightError, match="not tracked"):
        preflight_headline_run(protocol_path, repo_root=repo)


def test_gate07_digest_mismatch_blocks(tmp_path: Path):
    repo, protocol_path = _protocol_repo(tmp_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["dataset"]["graded_manifest_sha256"] = "sha256:deliberate-mismatch"
    protocol_path.write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _git(repo, "add", "--", "gates/baselines/protocol.json")
    _git(repo, "commit", "-m", "bad digest fixture")
    with pytest.raises(FreezePreflightError, match="digest mismatch"):
        preflight_headline_run(protocol_path, repo_root=repo)


def test_gate07_clean_committed_protocol_permits(tmp_path: Path):
    repo, protocol_path = _protocol_repo(tmp_path)
    receipt = preflight_headline_run(protocol_path, repo_root=repo)
    assert receipt["status"] == "passed"
    assert receipt["protocol_git_head_resolved"] == receipt["protocol_git_head_at_freeze"]
    assert receipt["dataset_digests"] == dataset_manifest_digests(build_all_cases())


def test_gate07_both_headline_runners_call_preflight(monkeypatch, tmp_path: Path, capsys):
    calls: list[str] = []
    for name in (
        "GROQ_RPM_SOFT_PER_KEY",
        "GROQ_TPM_SOFT_PER_KEY",
        "GROQ_RPD_SOFT_PER_KEY",
        "GROQ_TPD_SOFT_PER_KEY",
        "GROQ_POOL_RPM_SOFT",
        "GROQ_POOL_TPM_SOFT",
        "GROQ_POOL_RPD_SOFT",
        "GROQ_POOL_TPD_SOFT",
        "GROQ_ORG_RPM_SOFT",
        "GROQ_ORG_TPM_SOFT",
        "GROQ_ORG_RPD_SOFT",
        "GROQ_ORG_TPD_SOFT",
    ):
        monkeypatch.setenv(name, "100000")
    monkeypatch.setattr(offline_runner, "preflight_headline_run", lambda path: calls.append(str(path)) or {"status": "passed"})
    monkeypatch.setattr(offline_runner, "load_public_tasks", lambda path: [])
    offline_runner._args = lambda: types.SimpleNamespace(
        family="lexical", tasks="unused", output=str(tmp_path / "offline.jsonl"), raw=str(tmp_path / "offline.raw.jsonl"), protocol="protocol.json", bi_model=None, cross_model=None
    )
    offline_runner.main()

    monkeypatch.setattr(llm, "preflight_headline_run", lambda path: calls.append(str(path)) or {"status": "passed"})
    monkeypatch.setattr(llm, "load_public_tasks", lambda path: [])
    llm._args = lambda: types.SimpleNamespace(
        tasks="unused",
        output=str(tmp_path / "llm.jsonl"),
        raw=str(tmp_path / "llm.raw.jsonl"),
        ledger=str(tmp_path / "router.sqlite3"),
        request_ledger=str(tmp_path / "requests.jsonl"),
        models="model/test",
        preflight_only=False,
        protocol="protocol.json",
    )
    llm.run()
    capsys.readouterr()
    assert calls == ["protocol.json", "protocol.json"]
