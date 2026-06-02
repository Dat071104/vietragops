from __future__ import annotations

import html
import json

import pandas as pd
import streamlit as st


def render_document_table(documents: list[dict], selected_detail: dict | None = None) -> None:
    if not documents:
        st.markdown(
            """
            <div class="info-strip">
              No documents are available.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    rows = []
    for item in documents:
        rows.append(
            {
                "doc_id": item.get("doc_id"),
                "title": item.get("title"),
                "source_url": item.get("source_url"),
                "domain": item.get("domain"),
                "authority": item.get("authority_level"),
                "parse_status": item.get("parse_status"),
                "chunk_count": item.get("chunk_count"),
            }
        )

    st.markdown("<div class='section-title'>Document Inventory</div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    if selected_detail:
        st.markdown("<div class='section-title'>Selected Document</div>", unsafe_allow_html=True)
        st.markdown(
            "\n".join(
                [
                    "<div class='document-card'>",
                    f"<div class='chip-domain'>{html.escape(str(selected_detail.get('domain') or 'unknown domain'))}</div> "
                    f"<span class='chip-success'>{html.escape(str(selected_detail.get('authority_level') or 'unknown authority'))}</span> "
                    f"<span class='chip'>{html.escape(str(selected_detail.get('parse_status') or 'unknown status'))}</span>",
                    f"<div class='document-title'>{html.escape(str(selected_detail.get('title') or selected_detail.get('doc_id') or 'Document'))}</div>",
                    f"<div class='source-meta'>{html.escape(str(selected_detail.get('doc_id') or ''))}</div>",
                    f"<div class='muted'>{html.escape(str(selected_detail.get('source_url') or ''))}</div>",
                    f"<div class='muted'>chunk_count: {html.escape(str(selected_detail.get('chunk_count') or '0'))} • "
                    f"source_type: {html.escape(str(selected_detail.get('source_type') or 'n/a'))}</div>",
                    "</div>",
                ]
            ),
            unsafe_allow_html=True,
        )
        with st.expander("Open full document metadata", expanded=False):
            st.markdown(
                "<div class='json-block'><div class='json-block-header'>JSON</div>"
                f"<div class='json-body'>{html.escape(json.dumps(selected_detail, ensure_ascii=False, indent=2))}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
