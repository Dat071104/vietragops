"""Citation verification for grounded answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.retrieval.base import normalize_text


@dataclass(frozen=True)
class CitationVerificationResult:
    is_valid: bool
    errors: list[str]


class CitationVerifier:
    def verify(self, response: dict[str, Any], retrieved_chunks: list[dict[str, Any]]) -> CitationVerificationResult:
        if response.get("refusal"):
            return CitationVerificationResult(is_valid=True, errors=[])

        errors: list[str] = []
        citations = response.get("citations") or []
        answer = (response.get("answer") or "").strip()
        if answer and not citations:
            errors.append("Answer contains factual content but no citations were provided.")

        chunk_map = {chunk["chunk_id"]: chunk for chunk in retrieved_chunks}
        for citation in citations:
            chunk_id = citation.get("chunk_id")
            if chunk_id not in chunk_map:
                errors.append(f"Citation chunk_id '{chunk_id}' was not retrieved.")
                continue
            quote = (citation.get("quoted_evidence") or "").strip()
            if not quote:
                errors.append(f"Citation for chunk '{chunk_id}' is missing quoted evidence.")
                continue
            normalized_quote = normalize_text(quote)
            normalized_chunk_text = normalize_text(chunk_map[chunk_id]["text"])
            if normalized_quote not in normalized_chunk_text:
                errors.append(f"Quoted evidence for chunk '{chunk_id}' is not supported by the chunk text.")

        return CitationVerificationResult(is_valid=not errors, errors=errors)
