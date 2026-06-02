"""Metadata helpers and config definitions for chunk generation."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChunkConfig:
    name: str
    chunk_size: int
    overlap: int
    output_filename: str


CHUNK_CONFIGS = {
    "small": ChunkConfig(name="small", chunk_size=300, overlap=50, output_filename="chunks_300.jsonl"),
    "medium": ChunkConfig(name="medium", chunk_size=500, overlap=80, output_filename="chunks_500.jsonl"),
    "large": ChunkConfig(name="large", chunk_size=800, overlap=120, output_filename="chunks_800.jsonl"),
}

REQUIRED_MANIFEST_FIELDS = {
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "status",
}


def load_manifest_metadata(path: str | Path) -> dict[str, dict]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_MANIFEST_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing required fields: {sorted(missing)}")
        return {row["doc_id"]: row for row in reader}


def make_chunk_text(heading_path: list[str], body_text: str) -> str:
    heading = " > ".join(part.strip() for part in heading_path if part.strip())
    body = body_text.strip()
    return f"{heading}\n{body}" if heading else body


def make_chunk_checksum(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def chunk_config_payload(config: ChunkConfig) -> dict:
    payload = asdict(config)
    payload.pop("output_filename")
    return payload


def json_dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=False)
