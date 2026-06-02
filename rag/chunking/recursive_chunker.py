"""Recursive fallback splitting for oversized section content."""

from __future__ import annotations

import re
from dataclasses import dataclass


TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", flags=re.UNICODE)
LINE_PATTERN = re.compile(r"[^\n]+", flags=re.UNICODE)
SENTENCE_BOUNDARY_PATTERN = re.compile(r"(?<=[\.;:!?])\s+(?=[A-ZÀ-Ỵ0-9])", flags=re.UNICODE)
LEGAL_BOUNDARY_PATTERN = re.compile(
    r"(?=(?:Chương|Mục|Điều|Khoản)\s+[A-Za-zÀ-Ỵ0-9IVXLCDM])",
    flags=re.IGNORECASE | re.UNICODE,
)
NUMBERED_BOUNDARY_PATTERN = re.compile(
    r"(?=(?:\d+[\.\)]|[A-Z][\.\)])\s+)",
    flags=re.UNICODE,
)


@dataclass(frozen=True)
class TextSpan:
    text: str
    start: int
    end: int


def estimate_token_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def split_section_lines(text: str) -> list[TextSpan]:
    spans = []
    for match in LINE_PATTERN.finditer(text):
        line = match.group(0).strip()
        if not line:
            continue
        leading_ws = len(match.group(0)) - len(match.group(0).lstrip())
        start = match.start() + leading_ws
        end = start + len(line)
        spans.append(TextSpan(text=line, start=start, end=end))
    return spans


def split_oversized_span(span: TextSpan, max_tokens: int) -> list[TextSpan]:
    if estimate_token_count(span.text) <= max_tokens:
        return [span]

    for pattern in (LEGAL_BOUNDARY_PATTERN, NUMBERED_BOUNDARY_PATTERN, SENTENCE_BOUNDARY_PATTERN):
        pieces = _split_by_pattern(span, pattern)
        if len(pieces) > 1:
            results = []
            for piece in pieces:
                if estimate_token_count(piece.text) > max_tokens:
                    results.extend(split_oversized_span(piece, max_tokens))
                else:
                    results.append(piece)
            return results

    return _split_by_token_windows(span, max_tokens)


def _split_by_pattern(span: TextSpan, pattern: re.Pattern[str]) -> list[TextSpan]:
    boundary_positions = [match.start() for match in pattern.finditer(span.text) if match.start() > 0]
    return _split_by_boundaries(span, boundary_positions)


def _split_by_boundaries(span: TextSpan, boundaries: list[int]) -> list[TextSpan]:
    if not boundaries:
        return [span]

    positions = [0, *sorted(set(boundaries)), len(span.text)]
    pieces = []
    for left, right in zip(positions, positions[1:]):
        raw = span.text[left:right].strip()
        if not raw:
            continue
        start = span.text.find(raw, left, right)
        absolute_start = span.start + start
        absolute_end = absolute_start + len(raw)
        pieces.append(TextSpan(text=raw, start=absolute_start, end=absolute_end))
    return pieces or [span]


def _split_by_token_windows(span: TextSpan, max_tokens: int) -> list[TextSpan]:
    token_matches = list(re.finditer(r"\S+", span.text, flags=re.UNICODE))
    if not token_matches:
        return [span]

    pieces = []
    for index in range(0, len(token_matches), max_tokens):
        window = token_matches[index : index + max_tokens]
        left = window[0].start()
        right = window[-1].end()
        raw = span.text[left:right].strip()
        absolute_start = span.start + left
        absolute_end = absolute_start + len(raw)
        pieces.append(TextSpan(text=raw, start=absolute_start, end=absolute_end))
    return pieces
