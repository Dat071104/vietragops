"""Optional Qdrant integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.retrieval.index_store import ChunkIndexStore


@dataclass(frozen=True)
class QdrantSearchResult:
    chunk_id: str
    score: float
    payload: dict[str, Any]


class QdrantIndexer:
    def __init__(self, url: str = "http://localhost:6333", collection_name: str = "vietragops_chunks") -> None:
        self.url = url
        self.collection_name = collection_name
        self._client = self._load_client()

    def _load_client(self):
        try:
            from qdrant_client import QdrantClient
        except ImportError as error:
            raise RuntimeError("qdrant-client is not installed; Qdrant integration is optional.") from error
        return QdrantClient(url=self.url)

    @staticmethod
    def is_available() -> bool:
        try:
            from qdrant_client import QdrantClient  # noqa: F401
        except ImportError:
            return False
        return True

    def build_points(self, store: ChunkIndexStore, embeddings: list[list[float]]) -> list[dict[str, Any]]:
        points = []
        for index, (chunk, embedding) in enumerate(zip(store, embeddings, strict=False)):
            points.append(
                {
                    "id": index,
                    "vector": embedding,
                    "payload": {
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "source_url": chunk.source_url,
                        "heading_path": chunk.heading_path,
                        "authority_level": chunk.authority_level,
                        "domain": chunk.domain,
                    },
                }
            )
        return points

    def upsert(self, points: list[dict[str, Any]]) -> None:
        self._client.upsert(collection_name=self.collection_name, points=points)

    def search(self, vector: list[float], limit: int = 5) -> list[QdrantSearchResult]:
        results = self._client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
        )
        return [
            QdrantSearchResult(
                chunk_id=point.payload["chunk_id"],
                score=float(point.score),
                payload=dict(point.payload),
            )
            for point in results.points
        ]
