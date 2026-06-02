"""DOCX loader for VietRAGOps."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from rag.preprocessing.normalizer import normalize_text


def load_docx(path: str | Path) -> dict:
    file_path = Path(path)
    document = Document(str(file_path))
    blocks = []
    for paragraph in document.paragraphs:
        text = normalize_text(paragraph.text)
        if not text:
            continue
        style_name = getattr(paragraph.style, "name", "") or ""
        is_heading = style_name.lower().startswith("heading")
        level = None
        if is_heading:
            digits = "".join(ch for ch in style_name if ch.isdigit())
            level = int(digits) if digits else 1
        blocks.append({"type": "heading" if is_heading else "paragraph", "level": level, "page": None, "text": text})

    return {"title": file_path.stem, "blocks": blocks, "warnings": []}
