"""Download curated public Phase 1 sources and build the manifest."""

from __future__ import annotations

import csv
import hashlib
import mimetypes
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from phase1_sources import SOURCE_CATALOG


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "data" / "manifests" / "documents_manifest.csv"

MANIFEST_COLUMNS = [
    "doc_id",
    "title",
    "source_url",
    "source_type",
    "domain",
    "authority_level",
    "language",
    "published_at",
    "crawled_at",
    "file_path",
    "checksum",
    "status",
    "notes",
]


@dataclass
class DownloadResult:
    title: str
    source_type: str
    published_at: str
    file_path: str
    checksum: str


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def detect_extension(source_type: str, url: str, content_type: str) -> str:
    if source_type == "pdf":
        return ".pdf"
    if source_type == "html":
        return ".html"
    guess = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
    if guess:
        return guess
    path = Path(urlparse(url).path)
    return path.suffix or ".bin"


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def extract_published_at_html(soup: BeautifulSoup) -> str:
    selectors = [
        ("meta", {"property": "article:published_time"}, "content"),
        ("meta", {"name": "article:published_time"}, "content"),
        ("meta", {"property": "og:updated_time"}, "content"),
        ("meta", {"name": "pubdate"}, "content"),
        ("time", {}, "datetime"),
    ]
    for tag_name, attrs, attr_name in selectors:
        tag = soup.find(tag_name, attrs=attrs) if attrs else soup.find(tag_name)
        if tag and tag.get(attr_name):
            return tag.get(attr_name).strip()
    return ""


def infer_date_from_text_or_url(text: str, url: str) -> str:
    patterns = [
        (r"\b(\d{4}-\d{2}-\d{2})\b", lambda match: match.group(1)),
        (
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
            lambda match: f"{int(match.group(3)):04d}-{int(match.group(2)):02d}-{int(match.group(1)):02d}",
        ),
    ]
    for pattern, formatter in patterns:
        match = re.search(pattern, text)
        if match:
            return formatter(match)

    year_match = re.search(r"\b(20\d{2})\b", url)
    if year_match:
        return year_match.group(1)
    return ""


def extract_title_html(soup: BeautifulSoup, fallback: str) -> str:
    for selector in ("h1", "title"):
        node = soup.find(selector)
        if node:
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if text:
                return text
    meta = soup.find("meta", attrs={"property": "og:title"})
    if meta and meta.get("content"):
        return normalize_whitespace(meta["content"])
    return fallback


def download_source(item: dict, crawled_at: str) -> DownloadResult:
    headers = {
        "User-Agent": "VietRAGOpsPhase1Collector/1.0 (+https://tdtu.edu.vn/)",
        "Accept-Language": "vi,en;q=0.8",
    }
    response = requests.get(item["source_url"], headers=headers, timeout=60)
    response.raise_for_status()

    source_type = item["source_type"]
    content_type = response.headers.get("content-type", "")
    extension = detect_extension(source_type, item["source_url"], content_type)
    output_path = RAW_DIR / f"{item['doc_id']}{extension}"

    if source_type == "html":
        response.encoding = response.encoding or "utf-8"
        text = response.text
        payload = text.encode("utf-8")
        output_path.write_bytes(payload)
        soup = BeautifulSoup(text, "html.parser")
        title = item.get("title_override") or extract_title_html(soup, item["doc_id"])
        published_at = item.get("published_at") or extract_published_at_html(soup) or infer_date_from_text_or_url(
            soup.get_text(" ", strip=True),
            item["source_url"],
        )
    else:
        payload = response.content
        output_path.write_bytes(payload)
        title = item.get("title_override") or Path(urlparse(item["source_url"]).path).stem
        published_at = item.get("published_at") or infer_date_from_text_or_url(title, item["source_url"])

    checksum = sha256_bytes(payload)
    return DownloadResult(
        title=title,
        source_type=source_type,
        published_at=published_at,
        file_path=output_path.relative_to(ROOT).as_posix(),
        checksum=checksum,
    )


def write_manifest(rows: list[dict]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    crawled_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    rows = []
    failures = []

    for item in SOURCE_CATALOG:
        doc_id = item["doc_id"]
        print(f"[phase1] downloading {doc_id} -> {item['source_url']}")
        try:
            result = download_source(item, crawled_at)
        except Exception as exc:  # pragma: no cover - surfaced in CLI output
            failures.append((doc_id, str(exc)))
            print(f"[phase1] FAILED {doc_id}: {exc}", file=sys.stderr)
            continue

        row = {
            "doc_id": doc_id,
            "title": result.title,
            "source_url": item["source_url"],
            "source_type": result.source_type,
            "domain": item["domain"],
            "authority_level": item["authority_level"],
            "language": item.get("language", "vi"),
            "published_at": result.published_at,
            "crawled_at": crawled_at,
            "file_path": result.file_path,
            "checksum": result.checksum,
            "status": item["status"],
            "notes": item.get("notes", ""),
        }
        rows.append(row)

    write_manifest(rows)

    unique_checksums = {row["checksum"] for row in rows}
    print(f"[phase1] wrote manifest: {MANIFEST_PATH}")
    print(f"[phase1] successful rows: {len(rows)}")
    print(f"[phase1] unique checksums: {len(unique_checksums)}")
    if failures:
        print("[phase1] failures:")
        for doc_id, error in failures:
            print(f"  - {doc_id}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
