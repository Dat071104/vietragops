"""PDF loader for VietRAGOps."""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from rag.preprocessing.cleaner import clean_lines
from rag.preprocessing.normalizer import normalize_text


def _infer_title(reader: PdfReader, fallback: str) -> str:
    metadata_title = getattr(reader.metadata, "title", None) if reader.metadata else None
    if metadata_title:
        return normalize_text(str(metadata_title))
    for page in reader.pages[:2]:
        text = normalize_text(page.extract_text() or "")
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned and len(cleaned) <= 120:
                return cleaned
    return fallback


def load_pdf(path: str | Path) -> dict:
    file_path = Path(path)
    reader = PdfReader(str(file_path))
    title = _infer_title(reader, file_path.stem)
    blocks = []
    warnings = []

    for index, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if not text:
            warnings.append(f"page_{index}_empty")
            continue

        raw_lines = [line for line in text.splitlines()]
        lines = clean_lines(raw_lines)
        if not lines:
            warnings.append(f"page_{index}_cleaned_empty")
            continue

        paragraph_buffer: list[str] = []

        def flush() -> None:
            nonlocal paragraph_buffer
            paragraph = normalize_text(" ".join(paragraph_buffer))
            if paragraph:
                blocks.append({"type": "paragraph", "level": None, "page": index, "text": paragraph})
            paragraph_buffer = []

        for line in lines:
            if re.match(r"^(Chương|Mục|Điều|Khoản)\b", line, re.IGNORECASE) or re.match(r"^[IVXLCDM]+\.\s+", line):
                flush()
                blocks.append({"type": "heading", "level": None, "page": index, "text": line})
                continue

            if len(line) <= 6 and re.fullmatch(r"\d+", line):
                flush()
                continue

            paragraph_buffer.append(line)
            if len(paragraph_buffer) >= 4:
                flush()

        flush()

    if not blocks:
        warnings.append("no_pdf_blocks_extracted")

    warnings.append("pdf_table_extraction_limited")
    return {"title": title, "blocks": blocks, "warnings": warnings}
