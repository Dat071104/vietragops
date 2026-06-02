import json

from scripts.validate_chunks import validate_chunk_file


def test_validation_catches_empty_chunks(tmp_path) -> None:
    path = tmp_path / "chunks_bad.jsonl"
    path.write_text(
        json.dumps(
            {
                "chunk_id": "c1",
                "doc_id": "d1",
                "title": "T",
                "source_url": "https://example.edu.vn",
                "source_type": "html",
                "domain": "curriculum",
                "authority_level": "official",
                "heading_path": ["A"],
                "page_start": None,
                "page_end": None,
                "section_id": "s1",
                "chunk_index": 1,
                "text": "   ",
                "token_count": 0,
                "char_start": 0,
                "char_end": 0,
                "checksum": "sha256:x",
                "chunk_config": {"name": "medium", "chunk_size": 500, "overlap": 80},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    result = validate_chunk_file(path)
    assert result["critical_errors"]


def test_validation_catches_missing_required_metadata(tmp_path) -> None:
    path = tmp_path / "chunks_missing.jsonl"
    row = {
        "chunk_id": "c2",
        "doc_id": "d2",
        "title": "T",
        "source_url": "",
        "source_type": "pdf",
        "domain": "curriculum",
        "authority_level": "",
        "heading_path": [],
        "page_start": None,
        "page_end": None,
        "section_id": "s2",
        "chunk_index": 1,
        "text": "Nội dung hợp lệ",
        "token_count": 3,
        "char_start": 0,
        "char_end": 10,
        "checksum": "",
        "chunk_config": {"name": "small", "chunk_size": 300, "overlap": 50},
    }
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    result = validate_chunk_file(path)
    assert any("missing source_url" in error for error in result["critical_errors"])
    assert any("missing heading_path" in error for error in result["critical_errors"])
    assert any("missing authority_level" in error for error in result["critical_errors"])
