"""Proves candidate documents cannot affect the live RAG path before publish.

Uses the real `app.core.config.get_store()` -- the same store `ContextBuilder`
and the `/ask`/`/retrieve` routes read from -- against the real, committed
`data/chunks/chunks_500.jsonl`. This test only reads that file; it never
writes to it. No provider/model is called: retrieval context is inspected
directly, which is deterministic.
"""

from __future__ import annotations

from app.core.config import get_settings, get_store
from rag.lifecycle.pipeline import process_candidate


DISTINCTIVE_DOC_ID = "gate01-candidate-isolation-probe-zzyzx"
DISTINCTIVE_TEXT_MARKER = "Xyzzyplugh quokka policy marker 2026"


def test_candidate_document_is_invisible_to_the_live_store_before_publish(tmp_path):
    original = tmp_path / "originals" / "probe.md"
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(
        f"# {DISTINCTIVE_TEXT_MARKER}\n\nThis paragraph exists only in the candidate.\n",
        encoding="utf-8",
    )

    candidate_dir = tmp_path / "candidates" / "probe-v1"
    result = process_candidate(
        document_id=DISTINCTIVE_DOC_ID,
        version_id="probe-v1",
        original_path=original,
        extension=".md",
        title=DISTINCTIVE_TEXT_MARKER,
        source_url=None,
        domain=None,
        authority_level=None,
        candidate_dir=candidate_dir,
    )
    assert result.parse_status == "ok"
    assert any(DISTINCTIVE_TEXT_MARKER in chunk["text"] for chunk in result.chunks)

    # The candidate was written entirely under tmp_path, never under the real
    # live chunks path that Settings/get_store point at.
    live_settings = get_settings()
    assert result.chunks_path != live_settings.chunks_path
    assert live_settings.chunks_path.resolve() not in result.chunks_path.resolve().parents

    # The normal live RAG path (same store ContextBuilder/routes use) does not
    # see the candidate's chunks, doc_id, or distinctive text.
    live_store = get_store()
    live_doc_ids = {chunk.doc_id for chunk in live_store}
    assert DISTINCTIVE_DOC_ID not in live_doc_ids
    assert not any(DISTINCTIVE_TEXT_MARKER in chunk.text for chunk in live_store)
