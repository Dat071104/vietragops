from __future__ import annotations

import html
import json

import streamlit as st


def render_answer_view(response: dict, mode_label: str, show_debug: bool = False) -> None:
    if not response:
        st.markdown(
            """
            <div class="info-strip">
              Ask a question to render the answer card, citation evidence, refusal state, and retrieval debug panel.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    confidence = float(response.get("confidence", 0.0) or 0.0)
    refusal = bool(response.get("refusal"))
    citations = response.get("citations", [])
    status_label = "Refusal" if refusal else "Grounded answer"
    status_class = "mode-refusal" if refusal else "mode-grounded"

    st.markdown(
        f"<div class='mode-pill {status_class}'>{html.escape(mode_label)} • {status_label}</div>",
        unsafe_allow_html=True,
    )

    metric_columns = st.columns(3)
    metric_columns[0].metric("Confidence", f"{confidence:.0%}")
    metric_columns[1].metric("Status", status_label)
    metric_columns[2].metric("Citations", str(len(citations)))

    st.markdown("<div class='section-title'>Answer</div>", unsafe_allow_html=True)
    if refusal:
        refusal_reason = response.get("refusal_reason") or "The system refused because the retrieved context was not sufficient."
        st.markdown(
            f"<div class='result-area'><div class='refusal-banner'>{html.escape(refusal_reason)}</div></div>",
            unsafe_allow_html=True,
        )
    else:
        answer_text = html.escape(response.get("answer", ""))
        st.markdown(f"<div class='result-area'><div class='answer-text'>{answer_text}</div></div>", unsafe_allow_html=True)

    if citations:
        st.markdown("<div class='section-title'>Citation Cards</div>", unsafe_allow_html=True)
        for index, citation in enumerate(citations, start=1):
            heading_path = " > ".join(citation.get("heading_path", [])) or "No heading path"
            doc_id = citation.get("doc_id", "unknown_doc")
            chunk_id = citation.get("chunk_id", "unknown_chunk")
            source_url = citation.get("source_url", "")
            quoted_evidence = citation.get("quoted_evidence", "")
            st.markdown(
                "\n".join(
                    [
                        "<div class='citation-card'>",
                        f"<div class='chip'>Citation {index}</div>",
                        f"<div class='citation-title'>{html.escape(doc_id)}</div>",
                        f"<div class='source-meta'>{html.escape(chunk_id)}</div>",
                        f"<div class='muted'>{html.escape(heading_path)}</div>",
                        f"<div class='source-meta'>{html.escape(source_url)}</div>",
                        f"<div class='citation-quote'>{html.escape(quoted_evidence)}</div>",
                        "</div>",
                    ]
                ),
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="info-strip">
              No citations were returned for this response.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if show_debug:
        retrieval_debug = response.get("retrieval_debug", {})
        st.markdown("<div class='section-title'>Retrieval Debug</div>", unsafe_allow_html=True)
        with st.expander("Open retrieval debug payload", expanded=False):
            st.markdown(
                "<div class='json-block'><div class='json-block-header'>JSON</div>"
                f"<div class='json-body'>{html.escape(json.dumps(retrieval_debug, ensure_ascii=False, indent=2))}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
