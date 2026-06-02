"""Dense retrieval with optional sentence-transformers support and an offline fallback."""

from __future__ import annotations

from collections import Counter, defaultdict
import contextlib
from dataclasses import dataclass
import importlib
import io
import math
from typing import Any

from rag.retrieval.base import BaseRetriever, RetrievalResult, make_char_ngrams, make_word_bigrams, tokenize
from rag.retrieval.index_store import ChunkIndexStore


@dataclass(frozen=True)
class DenseConfig:
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    local_files_only: bool = True


class _SparseSemanticBackend:
    def __init__(self, store: ChunkIndexStore) -> None:
        self.name = "sparse_semantic_fallback"
        self._doc_weights: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        self._postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        self._idf = Counter()
        self._chunk_count = len(store)

        raw_features = [self._extract_features(chunk.text) for chunk in store]
        feature_document_frequency = Counter()
        for feature_counts in raw_features:
            feature_document_frequency.update(feature_counts.keys())

        for feature, frequency in feature_document_frequency.items():
            self._idf[feature] = math.log((1 + self._chunk_count) / (1 + frequency)) + 1.0

        for index, feature_counts in enumerate(raw_features):
            weights = self._tf_idf(feature_counts)
            norm = math.sqrt(sum(weight * weight for weight in weights.values())) or 1.0
            self._doc_weights.append(weights)
            self._doc_norms.append(norm)
            for feature, weight in weights.items():
                self._postings[feature].append((index, weight))

    def _extract_features(self, text: str) -> Counter[str]:
        tokens = tokenize(text)
        features = tokens + make_word_bigrams(tokens) + make_char_ngrams(text)
        return Counter(features)

    def _tf_idf(self, feature_counts: Counter[str]) -> dict[str, float]:
        weights: dict[str, float] = {}
        for feature, count in feature_counts.items():
            tf = 1.0 + math.log(count)
            weights[feature] = tf * self._idf[feature]
        return weights

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        feature_counts = self._extract_features(query)
        if not feature_counts:
            return []
        query_weights = self._tf_idf(feature_counts)
        query_norm = math.sqrt(sum(weight * weight for weight in query_weights.values())) or 1.0
        scores: dict[int, float] = defaultdict(float)
        for feature, query_weight in query_weights.items():
            for doc_index, doc_weight in self._postings.get(feature, []):
                scores[doc_index] += query_weight * doc_weight

        normalized = [
            (doc_index, dot_product / (query_norm * self._doc_norms[doc_index]))
            for doc_index, dot_product in scores.items()
        ]
        return sorted(normalized, key=lambda item: (-item[1], item[0]))[:top_k]


class _SentenceTransformerBackend:
    def __init__(self, store: ChunkIndexStore, config: DenseConfig) -> None:
        sentence_transformers = importlib.import_module("sentence_transformers")
        numpy = importlib.import_module("numpy")
        self._np = numpy
        self._model = sentence_transformers.SentenceTransformer(
            config.model_name,
            device="cpu",
            local_files_only=config.local_files_only,
        )
        self._embeddings = self._model.encode(
            [chunk.text for chunk in store],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self.name = f"sentence_transformers:{config.model_name}"

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        query_vector = self._model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        scores = self._embeddings @ query_vector
        ranked_indices = self._np.argsort(-scores)[:top_k]
        return [(int(index), float(scores[index])) for index in ranked_indices]


class DenseRetriever(BaseRetriever):
    name = "dense"

    def __init__(self, store: ChunkIndexStore, config: DenseConfig | None = None) -> None:
        super().__init__(store)
        self.config = config or DenseConfig()
        self._backend = self._build_backend()
        self.backend_name = self._backend.name

    def _build_backend(self) -> Any:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return _SentenceTransformerBackend(self.store, self.config)
        except Exception:
            return _SparseSemanticBackend(self.store)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        ranked = self._backend.search(query, top_k)
        results: list[RetrievalResult] = []
        for rank, (index, score) in enumerate(ranked, start=1):
            chunk = self.store.chunks[index]
            results.append(
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
                    component_scores={"dense_score": score},
                    metadata={"title": chunk.title},
                )
            )
        return results
