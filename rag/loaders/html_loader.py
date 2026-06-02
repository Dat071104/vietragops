"""HTML loader for VietRAGOps."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from rag.preprocessing.normalizer import normalize_text


CONTENT_SELECTORS = [
    "article",
    "div.node__content",
    "div.block-system-main-block",
    "main",
]

DROP_SELECTORS = [
    "script",
    "style",
    "noscript",
    "svg",
    "nav",
    "header",
    "footer",
    "form",
    ".sharethis-wrapper",
]


def _pick_container(soup: BeautifulSoup) -> Tag:
    candidates = []
    for selector in CONTENT_SELECTORS:
        for node in soup.select(selector):
            text = normalize_text(node.get_text("\n", strip=True))
            candidates.append((len(text), node))
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]
    if soup.body:
        return soup.body
    return soup


def _table_to_markdown(table: Tag) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False) or tr.find_all(["th", "td"])
        cell_text = [normalize_text(cell.get_text(" ", strip=True)) for cell in cells]
        if len(cell_text) > 12:
            continue
        if any(cell_text):
            rows.append(cell_text)
    if not rows:
        return normalize_text(table.get_text("\n", strip=True))

    width = max(len(row) for row in rows)
    if width > 12 or len(rows) > 60:
        return normalize_text(table.get_text("\n", strip=True))
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = normalized_rows[0]
    separator = ["---"] * width
    body = normalized_rows[1:] or [[""] * width]
    markdown_rows = [header, separator, *body]
    return "\n".join("| " + " | ".join(row) + " |" for row in markdown_rows)


def load_html(path: str | Path) -> dict:
    file_path = Path(path)
    soup = BeautifulSoup(file_path.read_text(encoding="utf-8"), "html.parser")
    container = _pick_container(soup)

    for selector in DROP_SELECTORS:
        for node in container.select(selector):
            node.decompose()

    title = ""
    if soup.title:
        title = normalize_text(soup.title.get_text(" ", strip=True)).split("|")[0].strip()
    if not title:
        first_heading = container.find(["h1", "h2"])
        if first_heading:
            title = normalize_text(first_heading.get_text(" ", strip=True))

    blocks = []
    seen = set()
    for node in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]):
        if node.name == "table":
            text = _table_to_markdown(node)
            block_type = "table"
            level = None
        else:
            text = normalize_text(node.get_text(" ", strip=True))
            block_type = "heading" if node.name.startswith("h") else "paragraph"
            level = int(node.name[1]) if block_type == "heading" else None

        if not text:
            continue
        signature = (block_type, level, text)
        if signature in seen:
            continue
        seen.add(signature)
        blocks.append({"type": block_type, "level": level, "page": None, "text": text})

    warnings = []
    if not blocks:
        warnings.append("no_html_blocks_extracted")

    return {"title": title or file_path.stem, "blocks": blocks, "warnings": warnings}
