from rag.chunking.metadata_builder import CHUNK_CONFIGS
from rag.chunking.section_chunker import chunk_section


MANIFEST_ROW = {
    "title": "Điều lệ đào tạo",
    "source_url": "https://example.edu.vn/regulation",
    "source_type": "html",
    "domain": "training_regulation",
    "authority_level": "official",
}


def test_short_section_stays_intact_and_prepends_heading() -> None:
    doc = {"doc_id": "doc01", "sections": []}
    section = {
        "section_id": "doc01_s001",
        "heading_path": ["Chương I", "Điều 1. Phạm vi áp dụng"],
        "page": None,
        "text": "Quy chế này áp dụng cho sinh viên đại học.",
    }
    chunks = chunk_section(doc, section, MANIFEST_ROW, CHUNK_CONFIGS["medium"])
    assert len(chunks) == 1
    assert chunks[0]["chunk_id"] == "doc01_s001_c001"
    assert chunks[0]["heading_path"] == section["heading_path"]
    assert chunks[0]["text"].startswith("Chương I > Điều 1. Phạm vi áp dụng\n")
    assert "Quy chế này áp dụng" in chunks[0]["text"]


def test_long_section_splits_and_overlap_is_applied() -> None:
    doc = {"doc_id": "doc02", "sections": []}
    section = {
        "section_id": "doc02_s001",
        "heading_path": ["Học vụ", "Đăng ký môn học"],
        "page": None,
        "text": "\n".join(
            [
                f"Dòng {index} nội dung về kế hoạch học tập và đăng ký môn học với nhiều chi tiết hướng dẫn cụ thể cho sinh viên."
                for index in range(1, 21)
            ]
        ),
    }
    config = CHUNK_CONFIGS["small"]
    chunks = chunk_section(doc, section, MANIFEST_ROW, config)
    assert len(chunks) > 1
    assert chunks[0]["chunk_id"] == "doc02_s001_c001"
    assert chunks[1]["chunk_id"] == "doc02_s001_c002"
    assert "Dòng 1" in chunks[0]["text"]
    assert any(line in chunks[1]["text"] for line in ["Dòng 2", "Dòng 3", "Dòng 4"])
    assert chunks[0]["checksum"] != ""


def test_chunk_ids_are_deterministic() -> None:
    doc = {"doc_id": "doc03", "sections": []}
    section = {
        "section_id": "doc03_s010",
        "heading_path": ["Chương trình đào tạo"],
        "page": 5,
        "text": "Một đoạn ngắn.\nHai đoạn ngắn.",
    }
    first = chunk_section(doc, section, MANIFEST_ROW, CHUNK_CONFIGS["small"])
    second = chunk_section(doc, section, MANIFEST_ROW, CHUNK_CONFIGS["small"])
    assert [chunk["chunk_id"] for chunk in first] == [chunk["chunk_id"] for chunk in second]
    assert [chunk["checksum"] for chunk in first] == [chunk["checksum"] for chunk in second]
