"""Section detection for Vietnamese academic and policy documents."""

from __future__ import annotations

import re
from typing import Optional

from rag.preprocessing.cleaner import clean_text


HEADING_PATTERNS = [
    (re.compile(r"^chương\s+[ivxlcdm\d]+", re.IGNORECASE), 1),
    (re.compile(r"^mục\s+[ivxlcdm\d\.a-z]+", re.IGNORECASE), 2),
    (re.compile(r"^điều\s+\d+[\.:]?", re.IGNORECASE), 3),
    (re.compile(r"^[IVXLCDM]+\.\s+"), 2),
    (re.compile(r"^[A-Z]\.\s+"), 3),
    (re.compile(r"^\d+[\.\)]\s+"), 4),
]


def infer_heading_level(text: str, block_type: str, block_level: Optional[int] = None) -> Optional[int]:
    candidate = text.strip()
    if not candidate:
        return None

    if block_type == "heading":
        level = block_level or 1
        return min(max(level, 1), 6)

    if len(candidate) > 180:
        return None

    for pattern, level in HEADING_PATTERNS:
        if pattern.match(candidate):
            return level
    return None


def build_sections(blocks: list[dict], doc_id: str, title: str) -> list[dict]:
    sections: list[dict] = []
    heading_path: list[str] = [title]
    current_lines: list[str] = []
    current_page: Optional[int] = None

    def commit() -> None:
        nonlocal current_lines, current_page
        text = clean_text("\n".join(current_lines))
        if text:
            section_id = f"{doc_id}_s{len(sections) + 1:03d}"
            sections.append(
                {
                    "section_id": section_id,
                    "heading_path": heading_path.copy(),
                    "page": current_page,
                    "text": text,
                }
            )
        current_lines = []
        current_page = None

    for block in blocks:
        text = clean_text(block.get("text", ""))
        if not text:
            continue

        heading_level = infer_heading_level(text, block.get("type", "paragraph"), block.get("level"))
        if heading_level is not None:
            commit()
            depth = max(heading_level, 1)
            prefix = heading_path[: max(depth - 1, 0)]
            heading_path = prefix + [text]
            continue

        if current_page is None:
            current_page = block.get("page")
        current_lines.append(text)

    commit()

    if not sections:
        fallback_lines = [clean_text(block.get("text", "")) for block in blocks]
        fallback_text = "\n".join(line for line in fallback_lines if line).strip()
        if fallback_text:
            sections.append(
                {
                    "section_id": f"{doc_id}_s001",
                    "heading_path": [title],
                    "page": next((block.get("page") for block in blocks if block.get("page") is not None), None),
                    "text": fallback_text,
                }
            )

    return sections
