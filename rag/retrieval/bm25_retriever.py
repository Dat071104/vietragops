"""Offline BM25 retriever."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math

from rag.retrieval.base import BaseRetriever, RetrievalResult, tokenize
from rag.retrieval.index_store import ChunkIndexStore


@dataclass(frozen=True)
class BM25Config:
    k1: float = 1.5
    b: float = 0.75


class BM25Retriever(BaseRetriever):
    name = "bm25"
    backend_name = "offline_bm25"

    def __init__(self, store: ChunkIndexStore, config: BM25Config | None = None) -> None:
        super().__init__(store)
        self.config = config or BM25Config()
        self._doc_tokens = [tokenize(chunk.text) for chunk in self.store]
        self._doc_lengths = [max(1, len(tokens)) for tokens in self._doc_tokens]
        self._avg_doc_length = sum(self._doc_lengths) / max(1, len(self._doc_lengths))
        self._term_frequencies = [Counter(tokens) for tokens in self._doc_tokens]
        self._doc_frequency = Counter()
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)

        for index, term_frequencies in enumerate(self._term_frequencies):
            for term, frequency in term_frequencies.items():
                self._doc_frequency[term] += 1
                self._postings[term].append((index, frequency))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        scores: dict[int, float] = defaultdict(float)
        query_counts = Counter(query_terms)
        chunk_count = len(self.store)
        for term, query_frequency in query_counts.items():
            postings = self._postings.get(term)
            if not postings:
                continue
            doc_frequency = self._doc_frequency[term]
            idf = math.log(1.0 + ((chunk_count - doc_frequency + 0.5) / (doc_frequency + 0.5)))
            for doc_index, term_frequency in postings:
                length_norm = 1.0 - self.config.b + self.config.b * (
                    self._doc_lengths[doc_index] / max(1.0, self._avg_doc_length)
                )
                numerator = term_frequency * (self.config.k1 + 1.0)
                denominator = term_frequency + self.config.k1 * length_norm
                scores[doc_index] += idf * (numerator / denominator) * query_frequency

        ranked = sorted(
            scores.items(),
            key=lambda item: (-item[1], self.store.chunks[item[0]].chunk_id),
        )[:top_k]
        return [
            RetrievalResult(
                chunk_id=self.store.chunks[index].chunk_id,
                doc_id=self.store.chunks[index].doc_id,
                score=score,
                rank=rank,
                text=self.store.chunks[index].text,
                source_url=self.store.chunks[index].source_url,
                heading_path=list(self.store.chunks[index].heading_path),
                authority_level=self.store.chunks[index].authority_level,
                domain=self.store.chunks[index].domain,
                component_scores={"bm25_score": score},
                metadata={"title": self.store.chunks[index].title},
            )
            for rank, (index, score) in enumerate(ranked, start=1)
        ]
