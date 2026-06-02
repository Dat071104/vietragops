from __future__ import annotations

import html

import pandas as pd
import streamlit as st


def render_evidence_table(results: list[dict]) -> None:
    if not results:
        st.markdown(
            """
            <div class="info-strip">
              No evidence rows are available yet. Run retrieval to inspect the supporting chunks.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    table_rows = []
    for item in results:
        scores = item.get("component_scores", {})
        table_rows.append(
            {
                "rank": item.get("rank"),
                "doc_id": item.get("doc_id"),
                "chunk_id": item.get("chunk_id"),
                "authority": item.get("authority_level"),
                "domain": item.get("domain"),
                "bm25_score": round(float(scores.get("bm25_score", 0.0)), 4),
                "dense_score": round(float(scores.get("dense_score", 0.0)), 4),
                "hybrid_score": round(float(scores.get("hybrid_score", 0.0)), 4),
                "rerank_score": round(float(scores.get("rerank_score", 0.0)), 4),
                "authority_score": round(float(scores.get("source_authority_score", 0.0)), 4),
                "final_score": round(float(scores.get("final_score", item.get("score", 0.0))), 4),
                "source_url": item.get("source_url"),
                "heading_path": " > ".join(item.get("heading_path", [])),
                "chunk_text": item.get("text", ""),
            }
        )

    st.markdown("<div class='section-title'>Ranked Evidence Overview</div>", unsafe_allow_html=True)
    overview = pd.DataFrame(
        [
            {
                "rank": row["rank"],
                "doc_id": row["doc_id"],
                "chunk_id": row["chunk_id"],
                "authority": row["authority"],
                "domain": row["domain"],
                "final_score": row["final_score"],
                "source_url": row["source_url"],
                "heading_path": row["heading_path"],
            }
            for row in table_rows
        ]
    )
    st.dataframe(overview, width="stretch", hide_index=True)

    st.markdown("<div class='section-title'>Evidence Cards</div>", unsafe_allow_html=True)
    for row in table_rows:
        label = f"#{row['rank']} {row['doc_id']} :: {row['heading_path'] or 'No heading path'}"
        with st.expander(label, expanded=row["rank"] == 1):
            st.markdown(
                "\n".join(
                    [
                        "<div class='evidence-card'>",
                        f"<div class='chip'>Rank {html.escape(str(row['rank']))}</div> "
                        f"<span class='chip-domain'>{html.escape(str(row['domain'] or 'unknown domain'))}</span> "
                        f"<span class='chip-success'>{html.escape(str(row['authority'] or 'unknown authority'))}</span>",
                        f"<div class='evidence-title'>{html.escape(str(row['doc_id']))}</div>",
                        f"<div class='source-meta'>{html.escape(str(row['chunk_id']))}</div>",
                        f"<div class='muted'>{html.escape(row['heading_path'] or 'No heading path')}</div>",
                        f"<div class='source-meta'>{html.escape(str(row['source_url'] or ''))}</div>",
                        "</div>",
                    ]
                ),
                unsafe_allow_html=True,
            )

            score_columns = st.columns(6)
            score_columns[0].metric("BM25", f"{row['bm25_score']:.4f}")
            score_columns[1].metric("Dense", f"{row['dense_score']:.4f}")
            score_columns[2].metric("Hybrid", f"{row['hybrid_score']:.4f}")
            score_columns[3].metric("Rerank", f"{row['rerank_score']:.4f}")
            score_columns[4].metric("Authority", f"{row['authority_score']:.4f}")
            score_columns[5].metric("Final", f"{row['final_score']:.4f}")

            st.markdown(
                f"<div class='evidence-snippet'>{html.escape(row['chunk_text'])}</div>",
                unsafe_allow_html=True,
            )
