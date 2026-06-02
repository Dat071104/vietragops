"""Markdown and text loader for VietRAGOps."""

from __future__ import annotations

from pathlib import Path

from rag.preprocessing.normalizer import normalize_text


def load_markdown_or_text(path: str | Path) -> dict:
    file_path = Path(path)
    blocks = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = normalize_text(raw_line)
        if not line:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            blocks.append({"type": "heading", "level": level, "page": None, "text": line.lstrip("# ").strip()})
        else:
            blocks.append({"type": "paragraph", "level": None, "page": None, "text": line})

    return {"title": file_path.stem, "blocks": blocks, "warnings": []}
