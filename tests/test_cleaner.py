from rag.preprocessing.cleaner import clean_text


def test_clean_text_removes_boilerplate_and_normalizes() -> None:
    raw = "Nhảy đến nội dung\n\n  Dòng   nội   dung  \nblock_builder\n• Mục tiêu"
    cleaned = clean_text(raw)
    assert "Nhảy đến nội dung" not in cleaned
    assert "block_builder" not in cleaned
    assert "Dòng nội dung" in cleaned
    assert "- Mục tiêu" in cleaned
