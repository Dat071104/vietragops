from __future__ import annotations

import json
from pathlib import Path
import random
import re


ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "chunks" / "chunks_500.jsonl"
DEV_QA_PATH = ROOT / "evals" / "datasets" / "dev_qa.jsonl"
OUTPUT_DIR = ROOT / "evals" / "datasets"

DOMAIN_CATEGORY_MAP = {
    "student_account": "student_account",
    "email_usage": "email_usage",
    "course_registration": "course_registration",
    "academic_schedule": "academic_schedule",
    "training_regulation": "training_regulation",
    "curriculum": "curriculum_structure",
    "graduation_requirement": "graduation_requirement",
    "academic_policy": "policy_exception",
    "regulation": "training_regulation",
    "admission": "credit_requirement",
    "student_guide": "policy_exception",
}

TEMPLATE_BY_CATEGORY = {
    "student_account": 'Theo tài liệu "{leaf}", thông tin nào được nêu?',
    "email_usage": 'Theo tài liệu "{leaf}", thông tin nào được nêu?',
    "course_registration": 'Theo hướng dẫn "{leaf}", thông tin nào được nêu?',
    "academic_schedule": 'Theo hướng dẫn "{leaf}", thông tin nào được nêu?',
    "training_regulation": 'Theo quy định "{leaf}", nội dung nào được nêu?',
    "curriculum_structure": 'Theo chương trình "{leaf}", nội dung nào được nêu?',
    "graduation_requirement": 'Theo điều kiện tốt nghiệp "{leaf}", nội dung nào được nêu?',
    "policy_exception": 'Theo tài liệu "{leaf}", quy định nào được nêu?',
    "credit_requirement": 'Theo tài liệu "{leaf}", nội dung nào được nêu?',
}


MANUAL_QA = [
    {
        "question_id": "gold_manual_001",
        "question": "Theo quy định đào tạo 2021, sinh viên được công nhận chuyển đổi tối đa bao nhiêu phần trăm khối lượng học tập?",
        "expected_answer": "Khối lượng tối đa được công nhận, chuyển đổi không vượt quá 50% khối lượng học tập tối thiểu của chương trình đào tạo.",
        "relevant_chunk_ids": ["ug_training_reg_k2021_pdf_s038_c001"],
        "category": "credit_requirement",
        "difficulty": "medium",
        "is_answerable": True,
        "must_cite": True,
    },
    {
        "question_id": "gold_manual_002",
        "question": "Theo hướng dẫn kế hoạch học tập, nếu sinh viên muốn đăng ký vượt số tín chỉ tối đa thì phải làm gì?",
        "expected_answer": "Sinh viên phải làm đơn và nộp trực tiếp tại Văn phòng Tư vấn & Hỗ trợ, phòng E0001, trong giờ hành chính.",
        "relevant_chunk_ids": ["ug_study_plan_registration_guide_s001_c002"],
        "category": "policy_exception",
        "difficulty": "medium",
        "is_answerable": True,
        "must_cite": True,
    },
    {
        "question_id": "gold_manual_003",
        "question": "Nếu hỏi về khối lượng học tối đa trong học kỳ chính, nên ưu tiên quy định năm 2021 hay 2020?",
        "expected_answer": "Nên ưu tiên quy định năm 2021 vì đây là bản mới hơn trong ngữ liệu công khai đang được sử dụng cho hệ tuyển sinh từ năm 2021 trở về sau.",
        "relevant_chunk_ids": ["ug_training_reg_k2021_pdf_s016_c001", "ug_training_reg_k2020_pdf_s021_c001"],
        "category": "source_conflict",
        "difficulty": "hard",
        "is_answerable": True,
        "must_cite": True,
    },
    {
        "question_id": "gold_manual_004",
        "question": "Số điện thoại cá nhân của một sinh viên cụ thể là gì?",
        "expected_answer": "Không có thông tin này trong ngữ liệu công khai đã thu thập, nên hệ thống phải từ chối trả lời.",
        "relevant_chunk_ids": [],
        "category": "personal_data",
        "difficulty": "easy",
        "is_answerable": False,
        "must_cite": False,
    },
    {
        "question_id": "gold_manual_005",
        "question": "Học phí ở ký túc xá mỗi tháng là bao nhiêu?",
        "expected_answer": "Ngữ liệu hiện tại không nêu mức phí ký túc xá theo tháng, nên hệ thống phải từ chối trả lời.",
        "relevant_chunk_ids": [],
        "category": "out_of_scope",
        "difficulty": "easy",
        "is_answerable": False,
        "must_cite": False,
    },
]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def split_segments(text: str) -> list[str]:
    segments = []
    for block in text.splitlines():
        for part in block.split("|"):
            cleaned = re.sub(r"\s+", " ", part).strip()
            if len(cleaned) >= 40:
                segments.append(cleaned)
    return segments


def text_quality(text: str) -> float:
    tokens = re.findall(r"\w+", text, re.UNICODE)
    if not tokens:
        return 0.0
    single_char_ratio = sum(1 for token in tokens if len(token) == 1) / len(tokens)
    return 1.0 - min(1.0, single_char_ratio * 2.0)


def build_template_question(category: str, leaf: str) -> str:
    template = TEMPLATE_BY_CATEGORY.get(category, 'Theo tài liệu "{leaf}", nội dung nào được nêu?')
    safe_leaf = leaf or "phần này"
    return template.format(leaf=safe_leaf)


def infer_difficulty(segment: str) -> str:
    token_count = len(re.findall(r"\w+", segment, re.UNICODE))
    if token_count < 25:
        return "easy"
    if token_count < 55:
        return "medium"
    return "hard"


def make_generated_rows() -> list[dict]:
    rows = load_jsonl(CHUNKS_PATH)
    generated = []
    seen_questions = set()
    counters: dict[str, int] = {}

    for row in rows:
        category = DOMAIN_CATEGORY_MAP.get(row["domain"])
        if category is None:
            continue
        quality = text_quality(row["text"])
        if quality < 0.7:
            continue
        segments = split_segments(row["text"])
        if not segments:
            continue
        leaf = row["heading_path"][-1] if row["heading_path"] else row["title"]
        question = build_template_question(category, leaf)
        if question in seen_questions:
            question = build_template_question(category, f"{leaf} ({row['doc_id']})")
        segment = segments[0]
        seen_questions.add(question)
        counters[category] = counters.get(category, 0) + 1
        generated.append(
            {
                "question_id": f"gold_{category}_{counters[category]:03d}",
                "question": question,
                "expected_answer": segment,
                "relevant_chunk_ids": [row["chunk_id"]],
                "category": category,
                "difficulty": infer_difficulty(segment),
                "is_answerable": True,
                "must_cite": True,
            }
        )

    random.Random(42).shuffle(generated)
    return generated


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dev_rows = load_jsonl(DEV_QA_PATH)
    generated_rows = make_generated_rows()
    combined = []
    seen_ids = set()
    for row in dev_rows + MANUAL_QA + generated_rows:
        if row["question_id"] in seen_ids:
            continue
        combined.append(row)
        seen_ids.add(row["question_id"])

    combined = combined[:120]
    golden_rows = combined
    dev_rows = golden_rows[:20]
    validation_rows = golden_rows[20:26]
    test_rows = golden_rows[26:46]

    for filename, rows in [
        ("golden_qa.jsonl", golden_rows),
        ("dev_qa.jsonl", dev_rows),
        ("validation_qa.jsonl", validation_rows),
        ("test_qa.jsonl", test_rows),
    ]:
        path = OUTPUT_DIR / filename
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        print(f"[build_golden_qa] wrote {len(rows)} rows to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
