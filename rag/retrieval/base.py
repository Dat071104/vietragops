"""Shared retrieval types and text helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any


WORD_RE = re.compile(r"\w+", re.UNICODE)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    collapsed = re.sub(r"\s+", " ", normalized).strip()
    return collapsed.casefold()


def tokenize(text: str) -> list[str]:
    return [token for token in WORD_RE.findall(normalize_text(text)) if token]


def make_word_bigrams(tokens: list[str]) -> list[str]:
    return [f"{left}__{right}" for left, right in zip(tokens, tokens[1:])]


def make_char_ngrams(text: str, min_n: int = 3, max_n: int = 5) -> list[str]:
    normalized = normalize_text(text).replace(" ", "_")
    if not normalized:
        return []
    padded = f"_{normalized}_"
    features: list[str] = []
    for size in range(min_n, max_n + 1):
        if len(padded) < size:
            continue
        for index in range(len(padded) - size + 1):
            features.append(f"c{size}:{padded[index:index + size]}")
    return features


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    doc_id: str
    score: float
    rank: int
    text: str
    source_url: str
    heading_path: list[str]
    authority_level: str
    domain: str
    component_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "score": self.score,
            "rank": self.rank,
            "text": self.text,
            "source_url": self.source_url,
            "heading_path": list(self.heading_path),
            "authority_level": self.authority_level,
            "domain": self.domain,
            "component_scores": dict(self.component_scores),
            "metadata": dict(self.metadata),
        }


class BaseRetriever(ABC):
    """Common retriever interface."""

    name = "base"
    backend_name = "unknown"

    def __init__(self, store: Any) -> None:
        self.store = store

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {
            "retriever": self.name,
            "backend": self.backend_name,
            "chunk_count": len(self.store),
        }
