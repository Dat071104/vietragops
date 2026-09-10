"""Dense retrieval with optional sentence-transformers support and an offline fallback."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import importlib
import json
import logging
import math
from pathlib import Path
import time
from typing import Any

from rag.retrieval.base import BaseRetriever, RetrievalResult, make_char_ngrams, make_word_bigrams, tokenize
from rag.retrieval.index_store import ChunkIndexStore

logger = logging.getLogger(__name__)


_DENSE_BACKEND_FAILURES = (ImportError, OSError, RuntimeError, TypeError, ValueError)
DEFAULT_ONNX_ARTIFACT_DIR = Path("data/chunks/embeddings/active")
INCUMBENT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PRODUCT_MODEL_NAME = "intfloat/multilingual-e5-small"


@dataclass(frozen=True)
class DenseConfig:
    model_name: str = PRODUCT_MODEL_NAME
    local_files_only: bool = True
    onnx_artifact_dir: str | Path | None = None
    model_revision: str | None = None


class VectorSpaceMismatchError(ValueError):
    """Persisted corpus vectors cannot be used with the loaded query encoder."""


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


class _OnnxBackend:
    def __init__(self, store: ChunkIndexStore, config: DenseConfig) -> None:
        onnxruntime = importlib.import_module("onnxruntime")
        numpy = importlib.import_module("numpy")
        tokenizer_cls = importlib.import_module("tokenizers").Tokenizer

        self._np = numpy
        artifact_dir = Path(config.onnx_artifact_dir or DEFAULT_ONNX_ARTIFACT_DIR)
        metadata_path = artifact_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_path = artifact_dir / str(metadata.get("onnx_model", "model.onnx"))
        embeddings_path = artifact_dir / str(metadata.get("embeddings_file", "embeddings.npy"))
        chunk_ids_path = artifact_dir / str(metadata.get("chunk_ids_file", "chunk_ids.json"))
        tokenizer_path = artifact_dir / str(metadata.get("tokenizer_file", "tokenizer/tokenizer.json"))

        self._session = onnxruntime.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = tokenizer_cls.from_file(str(tokenizer_path))
        self._metadata = metadata
        self._embeddings = numpy.load(embeddings_path, mmap_mode="r", allow_pickle=False)
        self.last_query_encode_ms = 0.0
        chunk_ids = json.loads(chunk_ids_path.read_text(encoding="utf-8"))
        session_dimension = _session_output_dimension(self._session)
        _validate_vector_space(
            metadata,
            self._embeddings,
            chunk_ids,
            store,
            expected_model_name=config.model_name,
            expected_model_revision=config.model_revision,
            session_dimension=session_dimension,
        )

        self._max_seq_length = int(metadata["max_seq_length"])
        self._tokenizer.enable_truncation(max_length=self._max_seq_length)
        pad_id = metadata.get("pad_token_id")
        pad_token = metadata.get("pad_token", "[PAD]")
        if pad_id is None:
            pad_id = self._tokenizer.token_to_id(pad_token)
        if pad_id is None:
            raise VectorSpaceMismatchError("ONNX tokenizer has no recorded padding token ID")
        self._tokenizer.enable_padding(
            length=self._max_seq_length,
            pad_id=int(pad_id),
            pad_token=str(pad_token),
        )
        self.name = f"onnx:{metadata['model_id']}:{metadata.get('precision', 'fp32')}"

    def _encode(self, texts: list[str]) -> Any:
        prefix = str(self._metadata.get("query_prefix", ""))
        encodings = self._tokenizer.encode_batch([f"{prefix}{text}" for text in texts])
        input_ids = self._np.asarray([encoding.ids for encoding in encodings], dtype=self._np.int64)
        attention_mask = self._np.asarray(
            [encoding.attention_mask for encoding in encodings],
            dtype=self._np.int64,
        )
        feeds: dict[str, Any] = {}
        for input_spec in self._session.get_inputs():
            name = input_spec.name.casefold()
            if "input_ids" in name:
                feeds[input_spec.name] = input_ids
            elif "attention_mask" in name:
                feeds[input_spec.name] = attention_mask
            elif "token_type_ids" in name:
                feeds[input_spec.name] = self._np.zeros_like(input_ids)
        if len(feeds) < 2:
            raise VectorSpaceMismatchError("ONNX query encoder does not expose input_ids and attention_mask")

        token_embeddings = self._session.run(None, feeds)[0]
        mask = attention_mask[..., None].astype(self._np.float32)
        pooled = (token_embeddings * mask).sum(axis=1) / self._np.clip(mask.sum(axis=1), 1e-9, None)
        norms = self._np.linalg.norm(pooled, axis=1, keepdims=True)
        normalized = pooled / self._np.clip(norms, 1e-12, None)
        if normalized.shape[1] != int(self._metadata["dimension"]):
            raise VectorSpaceMismatchError(
                "ONNX query encoder dimension differs from persisted corpus vectors"
            )
        return normalized.astype(self._np.float32)

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        started = time.perf_counter()
        query_vector = self._encode([query])[0]
        self.last_query_encode_ms = (time.perf_counter() - started) * 1000
        scores = self._embeddings @ query_vector
        ranked_indices = self._np.argsort(-scores, kind="stable")[:top_k]
        return [(int(index), float(scores[index])) for index in ranked_indices]


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
        self.backend_state = "initializing"
        self.degradation_reason: str | None = None
        self.downgrade_reasons: list[str] = []
        self._backend = self._build_backend()
        self.backend_name = self._backend.name

    def _build_backend(self) -> Any:
        backends = (
            ("ONNX", _OnnxBackend),
            ("sentence-transformers", _SentenceTransformerBackend),
        )
        for label, backend_cls in backends:
            try:
                backend = backend_cls(self.store, self.config)
                self.backend_state = "degraded" if self.downgrade_reasons else "active"
                self.degradation_reason = " | ".join(self.downgrade_reasons) or None
                return backend
            except _DENSE_BACKEND_FAILURES as exc:
                reason = f"{label}: {type(exc).__name__}: {exc}"
                self.downgrade_reasons.append(reason)
                logger.warning(
                    "%s retrieval backend unavailable; continuing downgrade chain; reason=%s",
                    label,
                    reason,
                )

        fallback = _SparseSemanticBackend(self.store)
        self.downgrade_reasons.append(f"sparse fallback selected after {len(self.downgrade_reasons)} backend failures")
        self.degradation_reason = " | ".join(self.downgrade_reasons)
        self.backend_state = "degraded"
        logger.warning(
            "Dense retrieval degraded to active backend=%s; reason=%s",
            fallback.name,
            self.degradation_reason,
        )
        return fallback

    def status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "backend": self.backend_name,
            "state": self.backend_state,
            "degraded": self.backend_state == "degraded",
            "degradation_reason": self.degradation_reason,
            "downgrade_reasons": list(self.downgrade_reasons),
            "model_name": self.config.model_name,
            "onnx_artifact_dir": str(self.config.onnx_artifact_dir or DEFAULT_ONNX_ARTIFACT_DIR),
        }

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


def _session_output_dimension(session: Any) -> int | None:
    outputs = session.get_outputs()
    if not outputs or not outputs[0].shape:
        return None
    dimension = outputs[0].shape[-1]
    return int(dimension) if isinstance(dimension, int) else None


def _validate_vector_space(
    metadata: dict[str, Any],
    embeddings: Any,
    chunk_ids: list[str],
    store: ChunkIndexStore,
    *,
    expected_model_name: str,
    expected_model_revision: str | None,
    session_dimension: int | None,
) -> None:
    if metadata.get("model_id") != expected_model_name:
        raise VectorSpaceMismatchError(
            f"persisted model identity {metadata.get('model_id')!r} != loaded query model {expected_model_name!r}"
        )
    if expected_model_revision and metadata.get("model_revision") != expected_model_revision:
        raise VectorSpaceMismatchError(
            f"persisted model revision {metadata.get('model_revision')!r} != loaded query revision {expected_model_revision!r}"
        )
    if metadata.get("normalization") != "l2" or metadata.get("normalized") is not True:
        raise VectorSpaceMismatchError("persisted embeddings do not declare normalized l2 vectors")
    dimension = metadata.get("dimension")
    if not isinstance(dimension, int) or dimension <= 0:
        raise VectorSpaceMismatchError("persisted embeddings have no valid dimension")
    if getattr(embeddings, "ndim", None) != 2 or embeddings.shape[1] != dimension:
        raise VectorSpaceMismatchError("persisted embedding array shape disagrees with its metadata dimension")
    if session_dimension is not None and session_dimension != dimension:
        raise VectorSpaceMismatchError(
            f"ONNX query encoder dimension {session_dimension} != persisted dimension {dimension}"
        )
    expected_chunk_ids = [chunk.chunk_id for chunk in store]
    if chunk_ids != expected_chunk_ids:
        raise VectorSpaceMismatchError("persisted chunk ID order does not match the active chunk store")
    if len(embeddings) != len(expected_chunk_ids):
        raise VectorSpaceMismatchError("persisted embedding row count does not match the active chunk store")
    expected_content_hash = metadata.get("chunk_store_sha256")
    if expected_content_hash and expected_content_hash != store.content_hash():
        raise VectorSpaceMismatchError("persisted embeddings were generated from a different chunk-store content hash")
