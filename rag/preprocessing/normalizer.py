"""Text normalization helpers."""

from __future__ import annotations

import re
import unicodedata


BULLET_MAP = {
    "\u2022": "-",
    "\u25cf": "-",
    "\u25aa": "-",
    "\uf0b7": "-",
    "•": "-",
}


def normalize_text(text: str) -> str:
    """Normalize Unicode, bullets, and whitespace while preserving paragraphs."""
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    for source, target in BULLET_MAP.items():
        text = text.replace(source, target)

    lines = []
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        lines.append(line)

    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
