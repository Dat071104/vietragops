from rag.generation.citation_verifier import CitationVerifier


def test_citation_verifier_accepts_supported_quote():
    verifier = CitationVerifier()
    response = {
        "answer": "Theo ngữ cảnh, email là MSSV@student.tdtu.edu.vn.",
        "citations": [
            {
                "chunk_id": "c1",
                "quoted_evidence": "MSSV@student.tdtu.edu.vn",
            }
        ],
        "refusal": False,
    }
    chunks = [{"chunk_id": "c1", "text": "Cấu trúc email: MSSV@student.tdtu.edu.vn"}]

    result = verifier.verify(response, chunks)

    assert result.is_valid is True


def test_citation_verifier_rejects_unknown_chunk_and_bad_quote():
    verifier = CitationVerifier()
    response = {
        "answer": "Theo ngữ cảnh, email là MSSV@student.tdtu.edu.vn.",
        "citations": [
            {
                "chunk_id": "missing",
                "quoted_evidence": "MSSV@student.tdtu.edu.vn",
            }
        ],
        "refusal": False,
    }
    chunks = [{"chunk_id": "c1", "text": "Cấu trúc email: MSSV@student.tdtu.edu.vn"}]

    result = verifier.verify(response, chunks)

    assert result.is_valid is False
    assert result.errors
