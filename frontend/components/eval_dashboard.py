from __future__ import annotations

import html
from collections.abc import Iterable

import pandas as pd
import streamlit as st


KEY_METRICS = [
    "recall_at_5",
    "mrr",
    "token_f1",
    "citation_support_rate",
    "refusal_accuracy",
    "exact_match",
]


def render_eval_dashboard(detail: dict, mode_label: str) -> None:
    st.markdown(f"<div class='mode-pill'>{html.escape(mode_label)}</div>", unsafe_allow_html=True)
    if not detail:
        st.markdown(
            """
            <div class="info-strip">
              No experiment details are available.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if "experiments" in detail:
        _render_matrix_dashboard(detail)
        return

    metrics = detail.get("metrics", {})
    if metrics:
        st.markdown("<div class='section-title'>Experiment Summary</div>", unsafe_allow_html=True)
        _render_metric_cards(metrics)
        st.markdown("<div class='section-title'>Metric Table</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([metrics]), width="stretch", hide_index=True)
        _render_latency_summary(metrics)

    failure_rows = detail.get("records") or detail.get("per_query") or []
    _render_failure_rows(failure_rows)


def _render_matrix_dashboard(detail: dict) -> None:
    experiments = detail.get("experiments", [])
    if not experiments:
        st.markdown(
            """
            <div class="info-strip">
              This experiment bundle does not contain child experiments.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    summary_rows = []
    for index, experiment in enumerate(experiments, start=1):
        config = experiment.get("config", {})
        metrics = experiment.get("metrics", {})
        label = _label_experiment(experiment, index)
        summary_rows.append(
            {
                "label": label,
                "retriever": config.get("retriever") or experiment.get("retriever") or experiment.get("name", "unknown"),
                "top_k": config.get("top_k"),
                "reranker": config.get("reranker"),
                "guardrails": config.get("guardrails"),
                "source_priority": config.get("source_priority"),
                "recall_at_5": metrics.get("recall_at_5"),
                "mrr": metrics.get("mrr"),
                "token_f1": metrics.get("token_f1"),
                "citation_support_rate": metrics.get("citation_support_rate"),
                "refusal_accuracy": metrics.get("refusal_accuracy"),
                "latency_p50_ms": metrics.get("latency_p50_ms", metrics.get("latency_ms")),
                "latency_p95_ms": metrics.get("latency_p95_ms"),
            }
        )

    st.markdown("<div class='section-title'>Experiment Matrix</div>", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

    options = {row["label"]: experiment for row, experiment in zip(summary_rows, experiments, strict=False)}
    selected_label = st.selectbox("Inspect configuration", list(options.keys()))
    selected = options[selected_label]

    metrics = selected.get("metrics", {})
    if metrics:
        st.markdown("<div class='section-title'>Selected Metrics</div>", unsafe_allow_html=True)
        _render_metric_cards(metrics)
        st.dataframe(pd.DataFrame([metrics]), width="stretch", hide_index=True)
        _render_latency_summary(metrics)

    _render_failure_rows(selected.get("records") or selected.get("per_query") or [])


def _render_metric_cards(metrics: dict) -> None:
    cards = []
    for key in KEY_METRICS:
        if key not in metrics:
            continue
        cards.append((key, _format_metric_value(metrics[key])))
    if not cards:
        return

    columns = st.columns(min(4, len(cards)))
    for index, (key, value) in enumerate(cards):
        columns[index % len(columns)].markdown(
            f"<div class='eval-metric-card'><div class='eval-metric-label'>{html.escape(key)}</div>"
            f"<div class='eval-metric-val'>{html.escape(value)}</div></div>",
            unsafe_allow_html=True,
        )


def _render_latency_summary(metrics: dict) -> None:
    latency_keys = [key for key in metrics if key.startswith("latency")]
    if not latency_keys:
        return

    st.markdown("<div class='section-title'>Latency Summary</div>", unsafe_allow_html=True)
    columns = st.columns(min(4, len(latency_keys)))
    for index, key in enumerate(latency_keys):
        value = metrics[key]
        formatted = f"{float(value):.2f}" if isinstance(value, (int, float)) else str(value)
        columns[index % len(columns)].markdown(
            f"<div class='latency-card'><div class='latency-label'>{html.escape(key)}</div>"
            f"<div class='latency-val'>{html.escape(formatted)}</div></div>",
            unsafe_allow_html=True,
        )


def _render_failure_rows(rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        st.markdown(
            """
            <div class="info-strip">
              No failure rows are available for this experiment.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    failure_table = []
    for row in rows:
        label = row.get("failure_label") or row.get("miss_reason")
        if not label:
            continue
        failure_table.append(
            {
                "question_id": row.get("question_id"),
                "category": row.get("category"),
                "failure_label": label,
                "latency_ms": row.get("latency_ms"),
                "question": row.get("question"),
                "refusal_reason": row.get("refusal_reason"),
            }
        )

    if not failure_table:
        st.success("No labeled failures were recorded for this selection.")
        return

    st.markdown("<div class='section-title'>Failure Cases</div>", unsafe_allow_html=True)
    preview = failure_table[:20]
    for row in preview[:5]:
        label = row.get("failure_label") or "failure"
        question = row.get("question") or "No question text"
        reason = row.get("refusal_reason") or "No refusal reason recorded."
        st.markdown(
            "\n".join(
                [
                    "<div class='academic-panel'>",
                    f"<div class='failure-label'>{html.escape(str(label))}</div>",
                    f"<div class='document-title'>{html.escape(str(question))}</div>",
                    f"<div class='muted'>question_id: {html.escape(str(row.get('question_id') or 'n/a'))} • "
                    f"category: {html.escape(str(row.get('category') or 'n/a'))} • "
                    f"latency_ms: {html.escape(str(row.get('latency_ms') or 'n/a'))}</div>",
                    f"<div class='citation-quote'>{html.escape(str(reason))}</div>",
                    "</div>",
                ]
            ),
            unsafe_allow_html=True,
        )
    st.dataframe(pd.DataFrame(preview), width="stretch", hide_index=True)


def _label_experiment(experiment: dict, index: int) -> str:
    if experiment.get("name"):
        return f"{index:02d}. {experiment['name']}"
    config = experiment.get("config", {})
    parts = [
        config.get("retriever", "pipeline"),
        f"top_k={config.get('top_k', '?')}",
    ]
    if "reranker" in config:
        parts.append(f"reranker={config.get('reranker')}")
    if "guardrails" in config:
        parts.append(f"guardrails={config.get('guardrails')}")
    if "source_priority" in config:
        parts.append(f"source_priority={config.get('source_priority')}")
    return f"{index:02d}. " + " | ".join(parts)


def _format_metric_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
