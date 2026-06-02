"""Context assembly for grounded answer generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.retrieval import ChunkIndexStore, HybridRetriever, RetrievalResult
from rag.retrieval.base import make_word_bigrams, tokenize
from rag.retrieval.reranker import LexicalReranker


@dataclass(frozen=True)
class ContextBundle:
    question: str
    chunks: list[dict[str, Any]]
    support_score: float
    retrieval_debug: dict[str, Any]


class ContextBuilder:
    def __init__(self, store: ChunkIndexStore, retriever: Any | None = None) -> None:
        self.store = store
        self.retriever = retriever or HybridRetriever(store)
        self.reranker = LexicalReranker()

    def build(self, question: str, top_k: int = 5) -> ContextBundle:
        candidate_count = max(top_k * 4, 20)
        results = self.retriever.retrieve(question, top_k=max(candidate_count, 50))
        augmented = {result.chunk_id: result for result in results}
        for fallback_result in self._global_lexical_candidates(question, limit=20):
            augmented.setdefault(fallback_result.chunk_id, fallback_result)
        results = list(augmented.values())
        query_token_list = tokenize(question)
        query_tokens = set(query_token_list)
        query_bigrams = set(make_word_bigrams(query_token_list))
        hybrid_max = max((result.component_scores.get("hybrid_score", result.score) for result in results), default=0.0)
        hybrid_norm = {
            result.chunk_id: (
                (result.component_scores.get("hybrid_score", result.score) / hybrid_max) if hybrid_max > 0 else 0.0
            )
            for result in results
        }
        reranked = self.reranker.rerank(question, results)
        lexical_scores = {item.result.chunk_id: item.score for item in reranked}
        lexical_max = max(lexical_scores.values(), default=0.0)
        chunks = []
        support_scores = []

        for result in results:
            overlap = self._term_overlap(query_tokens, result)
            bigram_overlap = self._bigram_overlap(query_bigrams, result)
            lexical_score = (lexical_scores.get(result.chunk_id, 0.0) / lexical_max) if lexical_max > 0 else 0.0
            quality_score = self._text_quality_score(result.text)
            combined_support = (
                0.35 * overlap
                + 0.3 * lexical_score
                + 0.15 * bigram_overlap
                + 0.1 * quality_score
                + 0.1 * hybrid_norm.get(result.chunk_id, 0.0)
            )
            support_scores.append(combined_support)
            chunks.append(
                {
                    "chunk_id": result.chunk_id,
                    "doc_id": result.doc_id,
                    "text": result.text,
                    "source_url": result.source_url,
                    "heading_path": list(result.heading_path),
                    "authority_level": result.authority_level,
                    "domain": result.domain,
                    "score": result.score,
                    "component_scores": dict(result.component_scores),
                    "metadata": dict(result.metadata),
                    "lexical_score": round(lexical_score, 6),
                    "bigram_overlap": round(bigram_overlap, 6),
                    "quality_score": round(quality_score, 6),
                    "support_score": round(combined_support, 6),
                }
            )
        chunks.sort(key=lambda chunk: (-chunk["support_score"], chunk["chunk_id"]))
        selected_chunks = chunks[:top_k]

        retrieval_debug = {
            "retriever": self.retriever.name,
            "backend": getattr(self.retriever, "backend_name", "unknown"),
            "top_k": top_k,
            "candidate_count": len(chunks),
            "chunk_ids": [chunk["chunk_id"] for chunk in selected_chunks],
            "scores": [
                {
                    "chunk_id": chunk["chunk_id"],
                    "score": chunk["score"],
                    "component_scores": chunk["component_scores"],
                    "lexical_score": chunk["lexical_score"],
                    "bigram_overlap": chunk["bigram_overlap"],
                    "quality_score": chunk["quality_score"],
                    "support_score": chunk["support_score"],
                }
                for chunk in selected_chunks
            ],
        }
        return ContextBundle(
            question=question,
            chunks=selected_chunks,
            support_score=round(max((chunk["support_score"] for chunk in selected_chunks), default=0.0), 6),
            retrieval_debug=retrieval_debug,
        )

    def _term_overlap(self, query_tokens: set[str], result: RetrievalResult) -> float:
        if not query_tokens:
            return 0.0
        result_tokens = set(tokenize(f"{result.metadata.get('title', '')} {' '.join(result.heading_path)} {result.text}"))
        return len(query_tokens.intersection(result_tokens)) / len(query_tokens)

    def _bigram_overlap(self, query_bigrams: set[str], result: RetrievalResult) -> float:
        if not query_bigrams:
            return 0.0
        result_tokens = tokenize(f"{result.metadata.get('title', '')} {' '.join(result.heading_path)} {result.text}")
        result_bigrams = set(make_word_bigrams(result_tokens))
        return len(query_bigrams.intersection(result_bigrams)) / len(query_bigrams)

    def _text_quality_score(self, text: str) -> float:
        tokens = tokenize(text)
        if not tokens:
            return 0.0
        single_character_tokens = sum(1 for token in tokens if len(token) == 1)
        single_character_ratio = single_character_tokens / len(tokens)
        return max(0.0, 1.0 - min(1.0, single_character_ratio * 2.0))

    def _global_lexical_candidates(self, question: str, limit: int) -> list[RetrievalResult]:
        query_tokens = tokenize(question)
        query_token_set = set(query_tokens)
        query_bigrams = set(make_word_bigrams(query_tokens))
        scored = []
        for chunk in self.store:
            title_heading = f"{chunk.title} {' '.join(chunk.heading_path)}"
            title_tokens = tokenize(title_heading)
            title_token_set = set(title_tokens)
            text_token_set = set(tokenize(chunk.text))
            title_bigrams = set(make_word_bigrams(title_tokens))
            token_overlap = len(query_token_set.intersection(text_token_set)) / max(1, len(query_token_set))
            title_overlap = len(query_token_set.intersection(title_token_set)) / max(1, len(query_token_set))
            bigram_overlap = len(query_bigrams.intersection(title_bigrams)) / max(1, len(query_bigrams))
            quality_score = self._text_quality_score(chunk.text)
            score = (0.5 * title_overlap) + (0.25 * token_overlap) + (0.15 * bigram_overlap) + (0.1 * quality_score)
            if score < 0.18 or (title_overlap == 0 and bigram_overlap == 0):
                continue
            scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        output = []
        for rank, (score, chunk) in enumerate(scored[:limit], start=1):
            output.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    score=score,
                    rank=rank,
                    text=chunk.text,
                    source_url=chunk.source_url,
                    heading_path=list(chunk.heading_path),
                    authority_level=chunk.authority_level,
                    domain=chunk.domain,
                    component_scores={"hybrid_score": 0.0, "global_lexical_score": score},
                    metadata={"title": chunk.title},
                )
            )
        return output
