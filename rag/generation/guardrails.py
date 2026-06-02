"""Refusal guardrails for grounded answering."""

from __future__ import annotations

from dataclasses import dataclass

from rag.generation.context_builder import ContextBundle
from rag.retrieval.base import normalize_text


PRIVATE_PATTERNS = [
    "s\u1ed1 \u0111i\u1ec7n tho\u1ea1i",
    "\u0111\u1ecba ch\u1ec9 nh\u00e0",
    "cccd",
    "c\u0103n c\u01b0\u1edbc",
    "email c\u00e1 nh\u00e2n",
    "m\u1eadt kh\u1ea9u c\u1ee7a",
    "th\u00f4ng tin c\u00e1 nh\u00e2n",
    "h\u1ed3 s\u01a1 c\u00e1 nh\u00e2n",
]


@dataclass(frozen=True)
class GuardrailDecision:
    refusal: bool
    refusal_reason: str | None = None


class GuardrailEngine:
    def __init__(
        self,
        min_support_score: float = 0.35,
        min_lexical_score: float = 0.25,
        min_bigram_overlap: float = 0.05,
    ) -> None:
        self.min_support_score = min_support_score
        self.min_lexical_score = min_lexical_score
        self.min_bigram_overlap = min_bigram_overlap

    def evaluate(self, question: str, context_bundle: ContextBundle, citation_failures: int = 0) -> GuardrailDecision:
        normalized_question = normalize_text(question)
        if any(normalize_text(pattern) in normalized_question for pattern in PRIVATE_PATTERNS):
            return GuardrailDecision(
                refusal=True,
                refusal_reason="C\u00e2u h\u1ecfi li\u00ean quan \u0111\u1ebfn d\u1eef li\u1ec7u c\u00e1 nh\u00e2n ho\u1eb7c ri\u00eang t\u01b0 ngo\u00e0i ph\u1ea1m vi \u0111\u01b0\u1ee3c ph\u00e9p tr\u1ea3 l\u1eddi.",
            )
        if citation_failures >= 2:
            return GuardrailDecision(
                refusal=True,
                refusal_reason="H\u1ec7 th\u1ed1ng kh\u00f4ng x\u00e1c minh \u0111\u01b0\u1ee3c tr\u00edch d\u1eabn sau hai l\u1ea7n ki\u1ec3m tra.",
            )
        max_lexical_score = max((chunk.get("lexical_score", 0.0) for chunk in context_bundle.chunks), default=0.0)
        max_bigram_overlap = max((chunk.get("bigram_overlap", 0.0) for chunk in context_bundle.chunks), default=0.0)
        if (
            not context_bundle.chunks
            or context_bundle.support_score < self.min_support_score
            or max_lexical_score < self.min_lexical_score
            or max_bigram_overlap < self.min_bigram_overlap
        ):
            return GuardrailDecision(
                refusal=True,
                refusal_reason="Ng\u1eef c\u1ea3nh truy xu\u1ea5t ch\u01b0a \u0111\u1ee7 m\u1ea1nh \u0111\u1ec3 tr\u1ea3 l\u1eddi \u0111\u00e1ng tin c\u1eady.",
            )
        return GuardrailDecision(refusal=False, refusal_reason=None)
