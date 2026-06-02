"""Section-aware chunk construction."""

from __future__ import annotations

from rag.chunking.metadata_builder import ChunkConfig, chunk_config_payload, make_chunk_checksum, make_chunk_text
from rag.chunking.recursive_chunker import TextSpan, estimate_token_count, split_oversized_span, split_section_lines

def chunk_document(doc: dict, manifest_row: dict, config: ChunkConfig) -> list[dict]:
    chunks = []
    for section in doc["sections"]:
        chunks.extend(chunk_section(doc, section, manifest_row, config))
    return chunks


def chunk_section(doc: dict, section: dict, manifest_row: dict, config: ChunkConfig) -> list[dict]:
    body_text = section["text"].strip()
    if not body_text:
        return []

    heading_budget = estimate_token_count(" > ".join(section["heading_path"]))
    body_budget = max(40, config.chunk_size - heading_budget)

    spans = _prepare_spans(body_text, body_budget)
    grouped_spans = _group_spans(spans, body_budget, config.overlap)
    results = []

    for chunk_index, chunk_spans in enumerate(grouped_spans, start=1):
        chunk_body = "\n".join(span.text.strip() for span in chunk_spans if span.text.strip()).strip()
        chunk_text = make_chunk_text(section["heading_path"], chunk_body)
        char_start = min(span.start for span in chunk_spans)
        char_end = max(span.end for span in chunk_spans)
        page_value = section.get("page")

        results.append(
            {
                "chunk_id": f"{section['section_id']}_c{chunk_index:03d}",
                "doc_id": doc["doc_id"],
                "title": manifest_row["title"],
                "source_url": manifest_row["source_url"],
                "source_type": manifest_row["source_type"],
                "domain": manifest_row["domain"],
                "authority_level": manifest_row["authority_level"],
                "heading_path": section["heading_path"],
                "page_start": page_value,
                "page_end": page_value,
                "section_id": section["section_id"],
                "chunk_index": chunk_index,
                "text": chunk_text,
                "token_count": estimate_token_count(chunk_text),
                "char_start": char_start,
                "char_end": char_end,
                "checksum": make_chunk_checksum(chunk_text),
                "chunk_config": chunk_config_payload(config),
            }
        )

    return results


def _prepare_spans(text: str, chunk_size: int) -> list[TextSpan]:
    raw_spans = split_section_lines(text)
    prepared = []
    for span in raw_spans:
        if estimate_token_count(span.text) > chunk_size:
            prepared.extend(split_oversized_span(span, chunk_size))
        else:
            prepared.append(span)
    return prepared


def _group_spans(spans: list[TextSpan], chunk_size: int, overlap: int) -> list[list[TextSpan]]:
    if not spans:
        return []

    chunks: list[list[TextSpan]] = []
    current: list[TextSpan] = []
    current_tokens = 0

    for span in spans:
        span_tokens = estimate_token_count(span.text)
        if current and current_tokens + span_tokens > chunk_size:
            chunks.append(current)
            current = _tail_overlap(current, overlap)
            current_tokens = sum(estimate_token_count(item.text) for item in current)
            while current and current_tokens + span_tokens > chunk_size:
                current_tokens -= estimate_token_count(current[0].text)
                current = current[1:]

        current.append(span)
        current_tokens += span_tokens

    if current:
        chunks.append(current)

    return _dedupe_adjacent_chunks(chunks)


def _tail_overlap(spans: list[TextSpan], overlap: int) -> list[TextSpan]:
    selected: list[TextSpan] = []
    tokens = 0
    for span in reversed(spans):
        span_tokens = estimate_token_count(span.text)
        if selected and tokens + span_tokens > overlap:
            break
        selected.append(span)
        tokens += span_tokens
        if tokens >= overlap:
            break
    return list(reversed(selected))


def _dedupe_adjacent_chunks(chunks: list[list[TextSpan]]) -> list[list[TextSpan]]:
    deduped = []
    previous_signature = None
    for chunk in chunks:
        signature = tuple((span.start, span.end) for span in chunk)
        if signature == previous_signature:
            continue
        deduped.append(chunk)
        previous_signature = signature
    return deduped
