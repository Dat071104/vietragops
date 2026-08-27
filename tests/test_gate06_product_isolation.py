"""Phase 6.0 non-negotiable: the sandbox is a research/evaluation-owned
module and structurally cannot reach the real product surface -- no
import of `app`/`rag`, no reference to the real corpus, lifecycle
registry, provider settings, or the `/mcp` surface, anywhere under
`research/gate0/`.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE0_ROOT = REPO_ROOT / "research" / "gate0"

BANNED_IMPORT_PREFIXES = ("app", "rag")
BANNED_TEXT_SNIPPETS = (
    "documents_manifest.csv",
    "data/chunks",
    "data/processed",
    "LifecycleService",
    "LifecycleRegistry",
    "ProviderRouter",
    "GroqClient",
    "OllamaClient",
    "/mcp",
    "get_mcp_server",
)


def _all_gate0_source_files():
    return sorted(GATE0_ROOT.rglob("*.py"))


def test_gate0_module_exists_and_is_non_trivial():
    files = _all_gate0_source_files()
    assert len(files) >= 15


def test_no_gate0_file_imports_app_or_rag():
    for path in _all_gate0_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top not in BANNED_IMPORT_PREFIXES, f"{path} imports product package {node.module!r}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top not in BANNED_IMPORT_PREFIXES, f"{path} imports product package {alias.name!r}"


def test_no_gate0_file_references_real_product_surface_by_name():
    for path in _all_gate0_source_files():
        source = path.read_text(encoding="utf-8")
        for banned in BANNED_TEXT_SNIPPETS:
            assert banned not in source, f"{path} references real product surface {banned!r}"


def test_no_gate0_file_opens_a_path_under_data_or_gates():
    for path in _all_gate0_source_files():
        source = path.read_text(encoding="utf-8")
        assert '"data/' not in source and "'data/" not in source
        assert '"gates/' not in source and "'gates/" not in source
