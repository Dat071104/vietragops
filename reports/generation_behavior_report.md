# Generation Behavior Report

## Setup

- Default context source: baseline `hybrid` retriever plus context-builder lexical augmentation
- Groq availability during this phase: `GROQ_API_KEY` not present locally
- Generation mode exercised in tests and examples: deterministic offline fallback

## Output schema

The answer layer returns:

```json
{
  "answer": "...",
  "citations": [
    {
      "doc_id": "...",
      "chunk_id": "...",
      "source_url": "...",
      "heading_path": ["..."],
      "quoted_evidence": "..."
    }
  ],
  "confidence": 0.0,
  "refusal": false,
  "refusal_reason": null,
  "retrieval_debug": {}
}
```

## Behavior examples

### Answerable direct

- Question: `Cấu trúc email sinh viên TDTU là gì?`
- Observed behavior: answer generated with a valid citation to `ug_student_email_guide_s001_c001`
- Key evidence: `Cấu trúc email: MSSV@student.tdtu.edu.vn`
- Note: the deterministic fallback is grounded but can still append extra low-value context lines, so it is accurate-first rather than concise-first.

### Procedural

- Question: `Sinh viên đăng ký kế hoạch học tập ở mục nào trong hệ thống thông tin sinh viên?`
- Observed behavior: answer grounded in `ug_study_plan_registration_guide_s001_c001` and adjacent guide chunks
- Key evidence: the study-plan guide chunk about `Đăng ký KHHT`
- Note: the current fallback remains extractive and may include an extra secondary citation beyond the minimal direct answer.

### Multi-hop

- Question: `Để đủ điều kiện học vụ tốt nghiệp, sinh viên cần hoàn tất những học phần nào và những chứng chỉ nào?`
- Observed behavior: answer merged evidence from `ug_graduation_conditions_s001_c001` and related regulation content
- Key evidence: completion of required and elective coursework plus output certificates
- Note: this demonstrates grounded multi-chunk synthesis without an external LLM.

### Unanswerable

- Question: `Phí ở ký túc xá mỗi tháng là bao nhiêu?`
- Observed behavior: refused
- Refusal reason: `Ngữ cảnh hiện tại không nêu mức tiền cụ thể để trả lời câu hỏi này.`
- Note: this refusal is driven by the monetary-signal check, which blocks dorm or fee mentions that do not actually contain a concrete amount.

### Private data refusal

- Question: `Số điện thoại cá nhân của một sinh viên cụ thể là gì?`
- Observed behavior: refused
- Refusal reason: `Câu hỏi liên quan đến dữ liệu cá nhân hoặc riêng tư ngoài phạm vi được phép trả lời.`

### Citation mismatch rejection

- Test case: a response citing `fake_chunk` with unsupported quoted evidence
- Observed behavior: rejected by `CitationVerifier`
- Error example: `Citation chunk_id 'fake_chunk' was not retrieved.`

## Guardrail summary

- Refuse on private-data questions: yes
- Refuse on insufficient or weak context: yes
- Refuse after citation verification fails twice: yes
- Refuse when numeric or monetary questions lack concrete supporting figures: yes

## Groq note

- `rag/generation/groq_client.py` reads only `GROQ_API_KEY` and `GROQ_MODEL`
- No real Groq smoke run was executed in this phase because the key was not present locally
- Tests therefore validated the deterministic offline path only
