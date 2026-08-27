"""Deterministic answer/evidence-state resolution (Gate 04 Phase 4.2).

This is a separate axis from citation verification
(`rag.generation.citation_verifier.CitationVerifier`): that module checks
whether a quoted citation is actually grounded in the chunk text it points
at. This module answers a different question -- given the resolved
source/version/authority/freshness metadata of the chunks actually cited,
should the answer be trusted, or does the underlying evidence itself carry
a caveat (it is stale, or two active official sources disagree)? A citation
can be perfectly grounded (quoted correctly) while the evidence state is
still `stale_source` or `source_conflict`; the two are never merged into one
verdict.

States, in explicit precedence order (most specific first -- each rule below
is checked only if the ones above it did not already decide the state):

1. `INSUFFICIENT_EVIDENCE` -- the answer was refused, has no citations, or
   none of its citations resolve to any version metadata at all. Checked
   first because conflict/staleness are meaningless without evidence.
2. `SOURCE_CONFLICT` -- two or more cited chunks are both `authority_state
   == "active"`, share the same non-null `conflict_key`, but resolve to a
   different `source_version`. This is the only automated signal for
   conflict; it never inspects answer text or uses an LLM/heuristic
   semantic-similarity check (explicitly out of scope for Gate 04).
3. `STALE_SOURCE` -- at least one cited chunk resolves to `freshness_state
   == "stale"` and no conflict was already found.
4. `SUPPORTED` -- none of the above triggered.

Every branch reasons only over the explicit `version` metadata already
attached to each chunk by `rag.retrieval.version_resolver.VersionResolver`
via `ContextBuilder`; nothing here infers policy conflict from free text.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

SUPPORTED = "supported"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"
STALE_SOURCE = "stale_source"
SOURCE_CONFLICT = "source_conflict"

_AUTHORITY_ACTIVE = "active"
_FRESHNESS_STALE = "stale"


@dataclass(frozen=True)
class EvidenceStateResult:
    state: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "reasons": list(self.reasons)}


def resolve_evidence_state(
    *,
    refusal: bool,
    citations: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> EvidenceStateResult:
    """Resolve the evidence state for one answer.

    `citations` is the response's citation list (each with a `chunk_id`).
    `chunks` is the full retrieved/ranked chunk list for the same turn
    (`ContextBundle.chunks`); each chunk dict may carry a `"version"` key
    (a `ChunkVersionInfo.to_dict()`) when a `VersionResolver` was wired in.
    Missing version metadata is treated as unresolved, never guessed.
    """
    if refusal:
        return EvidenceStateResult(INSUFFICIENT_EVIDENCE, ["refusal"])
    if not citations:
        return EvidenceStateResult(INSUFFICIENT_EVIDENCE, ["no_citations"])

    versions_by_chunk_id = {chunk["chunk_id"]: chunk.get("version") for chunk in chunks if "chunk_id" in chunk}
    cited_versions = [
        versions_by_chunk_id[citation["chunk_id"]]
        for citation in citations
        if citation.get("chunk_id") in versions_by_chunk_id and versions_by_chunk_id[citation["chunk_id"]] is not None
    ]
    if not cited_versions:
        return EvidenceStateResult(INSUFFICIENT_EVIDENCE, ["no_resolved_version_for_citations"])

    conflicting_keys = _find_conflicting_keys(cited_versions)
    if conflicting_keys:
        return EvidenceStateResult(SOURCE_CONFLICT, [f"conflict_key={key}" for key in sorted(conflicting_keys)])

    stale_source_ids = sorted(
        {version["source_id"] for version in cited_versions if version.get("freshness_state") == _FRESHNESS_STALE}
    )
    if stale_source_ids:
        return EvidenceStateResult(STALE_SOURCE, [f"stale:{source_id}" for source_id in stale_source_ids])

    return EvidenceStateResult(SUPPORTED, [])


def _find_conflicting_keys(cited_versions: list[dict[str, Any]]) -> set[str]:
    versions_by_conflict_key: dict[str, set[str]] = defaultdict(set)
    for version in cited_versions:
        conflict_key = version.get("conflict_key")
        if conflict_key and version.get("authority_state") == _AUTHORITY_ACTIVE:
            versions_by_conflict_key[conflict_key].add(version.get("source_version", ""))
    return {key for key, source_versions in versions_by_conflict_key.items() if len(source_versions) > 1}
