"""Deterministic changed-section diff between two web candidate versions.

No LLM summarization: the diff is computed purely from normalized-Markdown
section boundaries -- the exact same section builder the candidate
pipeline already uses -- compared by heading path and content hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from rag.lifecycle.storage import write_bytes_atomic
from rag.loaders.markdown_loader import load_markdown_or_text
from rag.preprocessing.section_detector import build_sections


DIFF_SCHEMA = "vietragops.web_candidate_diff"
DIFF_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SectionDiff:
    added_sections: tuple[str, ...]
    removed_sections: tuple[str, ...]
    changed_sections: tuple[str, ...]
    unchanged_count: int

    @property
    def has_changes(self) -> bool:
        return bool(self.added_sections or self.removed_sections or self.changed_sections)

    def to_record(self) -> dict:
        return {
            "schema": DIFF_SCHEMA,
            "schema_version": DIFF_SCHEMA_VERSION,
            "added_count": len(self.added_sections),
            "removed_count": len(self.removed_sections),
            "changed_count": len(self.changed_sections),
            "unchanged_count": self.unchanged_count,
            "added_sections": list(self.added_sections),
            "removed_sections": list(self.removed_sections),
            "changed_sections": list(self.changed_sections),
        }


def _section_key(section: dict) -> str:
    return " > ".join(section.get("heading_path", []))


def _section_hash(section: dict) -> str:
    return hashlib.sha256(section.get("text", "").encode("utf-8")).hexdigest()


def _sections_for(canonical_path: Path, document_id: str, title: str) -> dict[str, str]:
    if not canonical_path.is_file():
        return {}
    loaded = load_markdown_or_text(canonical_path)
    sections = build_sections(loaded.get("blocks", []), document_id, title)
    result: dict[str, str] = {}
    for section in sections:
        result[_section_key(section)] = _section_hash(section)
    return result


def compute_section_diff(
    *,
    prior_canonical_path: Path,
    new_canonical_path: Path,
    document_id: str,
    title: str,
) -> SectionDiff:
    prior_sections = _sections_for(Path(prior_canonical_path), document_id, title)
    new_sections = _sections_for(Path(new_canonical_path), document_id, title)

    prior_keys = set(prior_sections)
    new_keys = set(new_sections)

    added = tuple(sorted(new_keys - prior_keys))
    removed = tuple(sorted(prior_keys - new_keys))
    common = prior_keys & new_keys
    changed = tuple(sorted(key for key in common if prior_sections[key] != new_sections[key]))
    unchanged_count = len(common) - len(changed)

    return SectionDiff(
        added_sections=added, removed_sections=removed, changed_sections=changed, unchanged_count=unchanged_count
    )


def write_diff_artifact(path: Path, diff: SectionDiff) -> None:
    serialized = json.dumps(diff.to_record(), ensure_ascii=False, sort_keys=True) + "\n"
    write_bytes_atomic(Path(path), serialized.encode("utf-8"))
