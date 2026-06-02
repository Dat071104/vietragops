from rag.preprocessing.section_detector import build_sections


def test_build_sections_preserves_vietnamese_legal_headings() -> None:
    blocks = [
        {"type": "heading", "level": 1, "page": 1, "text": "Chương I Quy định chung"},
        {"type": "heading", "level": 2, "page": 1, "text": "Điều 1. Phạm vi áp dụng"},
        {"type": "paragraph", "level": None, "page": 1, "text": "Quy chế này áp dụng cho sinh viên đại học."},
        {"type": "paragraph", "level": None, "page": 1, "text": "Khoản 1. Sinh viên phải tuân thủ quy định."},
    ]
    sections = build_sections(blocks, "doc", "Quy chế")
    assert len(sections) >= 1
    assert sections[0]["heading_path"][-1] == "Điều 1. Phạm vi áp dụng"
    assert "Sinh viên phải tuân thủ" in sections[0]["text"]
