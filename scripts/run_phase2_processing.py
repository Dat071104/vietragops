"""Run Phase 2 parsing and cleaning across the manifest."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.loaders.docx_loader import load_docx
from rag.loaders.html_loader import load_html
from rag.loaders.markdown_loader import load_markdown_or_text
from rag.loaders.pdf_loader import load_pdf
from rag.preprocessing.section_detector import build_sections

MANIFEST_PATH = ROOT / "data" / "manifests" / "documents_manifest.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "processed_docs.jsonl"


def pick_loader(source_type: str, file_path: Path):
    suffix = file_path.suffix.lower()
    if source_type == "html" or suffix == ".html":
        return load_html
    if source_type == "pdf" or suffix == ".pdf":
        return load_pdf
    if suffix == ".docx":
        return load_docx
    return load_markdown_or_text


def main() -> int:
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    processed = []

    for row in rows:
        file_path = ROOT / row["file_path"]
        loader = pick_loader(row["source_type"], file_path)
        warnings = []
        parse_status = "ok"
        sections = []
        title = row["title"]

        try:
            loaded = loader(file_path)
            title = loaded.get("title") or title
            warnings.extend(loaded.get("warnings", []))
            sections = build_sections(loaded.get("blocks", []), row["doc_id"], title)
            if not sections:
                parse_status = "failed"
                warnings.append("no_sections_built")
        except Exception as exc:  # pragma: no cover - surfaced in CLI output
            parse_status = "failed"
            warnings.append(f"parser_exception:{exc}")

        processed.append(
            {
                "doc_id": row["doc_id"],
                "title": title,
                "source_url": row["source_url"],
                "source_type": row["source_type"],
                "sections": sections,
                "parse_status": parse_status,
                "warnings": warnings,
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for doc in processed:
            handle.write(json.dumps(doc, ensure_ascii=False) + "\n")

    success_count = sum(1 for doc in processed if doc["parse_status"] == "ok")
    print(f"processed_docs={len(processed)}")
    print(f"parse_success={success_count}")
    print(f"output={OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
