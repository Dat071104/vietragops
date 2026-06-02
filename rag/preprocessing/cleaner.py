"""Content cleaning utilities."""

from __future__ import annotations

from rag.preprocessing.normalizer import normalize_text


EXACT_BOILERPLATE = {
    "nhảy đến nội dung",
    "skip to main content",
    "block_builder",
}

CONTAINS_BOILERPLATE = (
    "googletagmanager",
    "gtag(",
    "drupal",
    "image:",
    "share this",
)


def is_boilerplate_line(line: str) -> bool:
    lowered = line.strip().lower()
    if not lowered:
        return False
    if lowered in EXACT_BOILERPLATE:
        return True
    return any(token in lowered for token in CONTAINS_BOILERPLATE)


def clean_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    previous = None
    for line in lines:
        normalized = normalize_text(line)
        if not normalized or is_boilerplate_line(normalized):
            continue
        if normalized == previous:
            continue
        cleaned.append(normalized)
        previous = normalized
    return cleaned


def clean_text(text: str) -> str:
    lines = clean_lines(text.splitlines())
    return "\n".join(lines).strip()
