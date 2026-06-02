from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys

import requests
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_answer_generator, get_settings, get_store
from app.api.routes_agent import run_agent_query
from app.schemas.query import AgentAskRequest
from frontend.components.answer_view import render_answer_view
from frontend.components.document_table import render_document_table
from frontend.components.eval_dashboard import render_eval_dashboard
from frontend.components.evidence_table import render_evidence_table
from rag.generation import ProviderRouter
from rag.retrieval.advanced_hybrid_retriever import AdvancedHybridConfig, AdvancedHybridRetriever


API_BASE_URL = os.environ.get("VIETRAGOPS_API_BASE_URL", "http://127.0.0.1:8000")
DEMO_MODE = os.environ.get("VIETRAGOPS_DEMO_MODE", "auto").casefold()


st.set_page_config(
    page_title="VietRAGOps Demo",
    page_icon="V",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_academic_light_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
          --ivory: #FAF8F3;
          --ivory-2: #F3F0E8;
          --ivory-3: #E8E3D5;
          --ivory-4: #D6CFB8;
          --text-primary: #2A2018;
          --text-secondary: #6B5F4E;
          --text-muted: #9A8E7C;
          --dark-brown: #3D2E1A;
          --mid-brown: #6B5540;
          --warm-brown: #8B7355;
          --accent: #C85A3A;
          --accent-light: #F2EAE5;
          --accent-mid: #E8C4B5;
          --border: #DDD8CC;
          --border-light: #EAE6DC;
          --success: #3D6B4F;
          --success-bg: #EBF3EE;
          --warning: #8B6B00;
          --warning-bg: #FFF8E6;
          --error: #8B2A2A;
          --error-bg: #FAF0F0;
          --font-serif: 'Lora', Georgia, serif;
          --font-sans: 'DM Sans', system-ui, sans-serif;
          --font-mono: 'JetBrains Mono', monospace;
        }

        html, body, [class*="css"] {
          font-family: var(--font-sans);
          color: var(--text-primary);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(200, 90, 58, 0.08), transparent 24%),
            linear-gradient(180deg, #FCFAF5 0%, var(--ivory) 28%, #F6F1E7 100%);
          color: var(--text-primary);
        }

        .block-container {
          max-width: 1380px;
          padding-top: 2rem;
          padding-bottom: 2rem;
        }

        h1, h2, h3, h4, .page-title, .section-title, .result-section-title {
          font-family: var(--font-serif);
          color: var(--dark-brown);
          letter-spacing: -0.02em;
        }

        p, li, label, .stMarkdown, .stText, .stCaption {
          color: var(--text-primary);
        }

        [data-testid="stSidebar"] {
          background: #F5F1E8;
          border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] .block-container {
          padding-top: 1.4rem;
          padding-bottom: 1.4rem;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stCaption {
          color: var(--text-secondary);
        }

        .sidebar-logo {
          padding-bottom: 0.9rem;
          margin-bottom: 1rem;
          border-bottom: 1px solid var(--border);
        }

        .logo-badge,
        .page-tag,
        .chip,
        .chip-domain,
        .chip-success,
        .chip-warning,
        .chip-error,
        .failure-label,
        .mode-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          padding: 0.22rem 0.62rem;
          border-radius: 4px;
          font-size: 0.68rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        .logo-badge,
        .page-tag {
          background: var(--accent-light);
          color: var(--accent);
        }

        .mode-pill {
          background: var(--accent-mid);
          color: var(--accent);
        }

        .mode-pill.mode-grounded {
          background: var(--success-bg);
          color: var(--success);
        }

        .mode-pill.mode-refusal {
          background: var(--warning-bg);
          color: var(--warning);
        }

        .chip-domain {
          background: var(--ivory-3);
          color: var(--mid-brown);
        }

        .chip-success {
          background: var(--success-bg);
          color: var(--success);
        }

        .chip-warning {
          background: var(--warning-bg);
          color: var(--warning);
        }

        .chip-error,
        .failure-label {
          background: var(--error-bg);
          color: var(--error);
        }

        .logo-title,
        .page-title {
          font-family: var(--font-serif);
          color: var(--dark-brown);
          letter-spacing: -0.02em;
        }

        .logo-title {
          font-size: 1.18rem;
          margin-top: 0.35rem;
        }

        .page-header {
          margin-bottom: 1.4rem;
          padding: 1.55rem 1.7rem;
          background: linear-gradient(180deg, rgba(255,255,255,0.74), rgba(243,240,232,0.84));
          border: 1px solid var(--border);
          border-radius: 12px;
        }

        .page-title {
          margin: 0.65rem 0 0.45rem;
          font-size: 2rem;
          line-height: 1.18;
        }

        .page-desc,
        .section-intro {
          max-width: 760px;
          color: var(--text-secondary);
          line-height: 1.75;
          font-size: 0.95rem;
        }

        .section-title {
          font-size: 1.05rem;
          margin: 0 0 0.55rem;
          padding-bottom: 0.55rem;
          border-bottom: 1px solid var(--border-light);
        }

        .section-intro {
          margin: 0 0 1rem;
        }

        .control-panel,
        .academic-panel,
        .result-area,
        .citation-card,
        .evidence-card,
        .document-card,
        .info-strip,
        .json-block {
          background: rgba(255,255,255,0.78);
          border: 1px solid var(--border);
          border-radius: 10px;
        }

        .control-panel,
        .academic-panel,
        .result-area {
          padding: 1.1rem 1.15rem;
          margin-bottom: 1rem;
        }

        .info-strip {
          padding: 0.95rem 1rem;
          color: var(--text-secondary);
          margin-bottom: 1rem;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.15rem;
          border-bottom: 1px solid var(--border);
          margin-bottom: 1rem;
        }

        .stTabs [data-baseweb="tab"] {
          height: auto;
          padding: 0.9rem 1.1rem 0.8rem;
          background: transparent;
          color: var(--text-muted);
          font-size: 0.84rem;
          font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
          color: var(--accent);
          border-bottom: 2px solid var(--accent);
        }

        .stTextInput label,
        .stSelectbox label,
        .stSlider label,
        .stToggle label {
          color: var(--text-secondary);
          font-size: 0.74rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextArea textarea {
          border-radius: 8px;
          border: 1px solid var(--border);
          background: rgba(255,255,255,0.82);
          color: var(--text-primary);
        }

        .stButton button,
        .stDownloadButton button {
          border-radius: 8px;
          border: 1px solid var(--accent);
          background: var(--accent);
          color: white;
          font-size: 0.84rem;
          font-weight: 600;
          padding: 0.62rem 1.15rem;
          box-shadow: none;
        }

        .stButton button:hover,
        .stDownloadButton button:hover {
          background: #B34E31;
          border-color: #B34E31;
          color: white;
        }

        .stExpander {
          border: 1px solid var(--border) !important;
          border-radius: 8px !important;
          background: rgba(255,255,255,0.6);
        }

        .stDataFrame {
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow: hidden;
        }

        [data-testid="stMetric"] {
          background: rgba(255,255,255,0.72);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 0.75rem 0.9rem;
        }

        [data-testid="stMetricLabel"] {
          color: var(--text-muted);
          font-size: 0.72rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        [data-testid="stMetricValue"] {
          font-family: var(--font-serif);
          color: var(--dark-brown);
        }

        .citation-stack,
        .evidence-stack,
        .document-stack {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .citation-card,
        .evidence-card,
        .document-card {
          padding: 1rem 1.05rem;
        }

        .citation-title,
        .evidence-title,
        .document-title {
          font-weight: 600;
          color: var(--dark-brown);
          margin: 0.35rem 0;
        }

        .mono,
        .source-meta {
          font-family: var(--font-mono);
        }

        .source-meta,
        .muted {
          color: var(--text-muted);
          font-size: 0.8rem;
        }

        .citation-quote,
        .evidence-snippet {
          margin-top: 0.75rem;
          padding-top: 0.75rem;
          border-top: 1px solid var(--border-light);
          color: var(--text-primary);
          line-height: 1.75;
        }

        .eval-metrics-grid,
        .latency-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 0.75rem;
          margin: 0.8rem 0 1rem;
        }

        .eval-metric-card,
        .latency-card {
          padding: 0.95rem 1rem;
          background: rgba(255,255,255,0.78);
          border: 1px solid var(--border);
          border-radius: 8px;
        }

        .eval-metric-label,
        .latency-label {
          color: var(--text-muted);
          font-size: 0.68rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 0.4rem;
        }

        .eval-metric-val {
          font-family: var(--font-serif);
          font-size: 1.45rem;
          color: var(--dark-brown);
        }

        .latency-val {
          font-family: var(--font-mono);
          font-size: 1.2rem;
          color: var(--dark-brown);
        }

        .json-block-header {
          padding: 0.7rem 0.9rem;
          background: var(--ivory-2);
          border-bottom: 1px solid var(--border);
          color: var(--text-secondary);
          font-size: 0.72rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .json-body {
          padding: 0.9rem;
          font-family: var(--font-mono);
          font-size: 0.78rem;
          line-height: 1.7;
          color: var(--mid-brown);
          white-space: pre-wrap;
          overflow-x: auto;
        }

        @media (max-width: 900px) {
          .page-header {
            padding: 1.25rem;
          }

          .page-title {
            font-size: 1.55rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header() -> None:
    st.markdown(
        """
        <div class="page-header">
          <div class="page-tag">VietRAGOps</div>
          <h1 class="page-title">Grounded Vietnamese Academic Policy QA</h1>
          <p class="page-desc">
            A production-style Vietnamese RAG evaluation platform with retrieval evidence, citation-grounded
            answers, refusal guardrails, and benchmark visibility.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_local_retriever() -> AdvancedHybridRetriever:
    settings = get_settings()
    return AdvancedHybridRetriever(
        get_store(),
        AdvancedHybridConfig(
            manifest_path=str(settings.manifest_path),
            enable_reranker=True,
            enable_source_priority=True,
            enable_recency=True,
        ),
    )


@st.cache_data(show_spinner=False)
def load_local_documents() -> list[dict]:
    settings = get_settings()
    chunk_counts = {}
    for chunk in get_store():
        chunk_counts[chunk.doc_id] = chunk_counts.get(chunk.doc_id, 0) + 1
    with settings.manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            "doc_id": row["doc_id"],
            "title": row["title"],
            "source_url": row["source_url"],
            "domain": row["domain"],
            "authority_level": row["authority_level"],
            "parse_status": "ok",
            "chunk_count": chunk_counts.get(row["doc_id"], 0),
            "source_type": row["source_type"],
            "file_path": row["file_path"],
            "checksum": row["checksum"],
            "notes": row.get("notes"),
        }
        for row in rows
    ]


@st.cache_data(show_spinner=False)
def load_local_experiments() -> list[dict]:
    experiments = []
    for path in sorted((ROOT / "dist" / "experiments").rglob("*.json")):
        experiments.append(
            {
                "experiment_id": path.stem,
                "experiment_type": path.parent.name,
                "file_path": str(path),
            }
        )
    return experiments


@st.cache_data(show_spinner=False)
def load_local_experiment_detail(experiment_id: str) -> dict:
    for path in (ROOT / "dist" / "experiments").rglob(f"{experiment_id}.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def api_get(base_url: str, path: str) -> dict | list:
    response = requests.get(f"{base_url.rstrip('/')}{path}", timeout=8)
    response.raise_for_status()
    return response.json()


def api_post(base_url: str, path: str, payload: dict) -> dict:
    response = requests.post(f"{base_url.rstrip('/')}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def is_api_available(base_url: str) -> bool:
    if DEMO_MODE == "force_local":
        return False
    try:
        payload = api_get(base_url, "/health")
        return payload.get("status") == "ok"
    except Exception:
        return False


def ask_local(question: str, debug: bool, top_k: int) -> dict:
    return get_answer_generator().answer(question, debug=debug, top_k=top_k)


def ask_local_agent(question: str, debug: bool, top_k: int) -> dict:
    return run_agent_query(AgentAskRequest(question=question, top_k=top_k, return_debug=debug)).model_dump()


def retrieve_local(question: str, top_k: int) -> list[dict]:
    return [item.to_dict() for item in get_local_retriever().retrieve(question, top_k=top_k)]


def get_local_agent_status() -> dict:
    settings = get_settings()
    return ProviderRouter(
        provider=settings.llm_provider,
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_num_ctx=settings.ollama_num_ctx,
    ).status()


def get_agent_status_payload(base_url: str, api_available: bool) -> dict:
    if api_available:
        try:
            return api_get(base_url, "/health")
        except Exception:
            pass
    local_status = get_local_agent_status()
    return {
        "llm_provider": local_status["provider"],
        "llm_model": local_status["model"],
        "ollama": local_status["ollama"],
    }


def load_documents(base_url: str, use_api: bool) -> list[dict]:
    if use_api:
        try:
            return api_get(base_url, "/documents")
        except Exception:
            pass
    return load_local_documents()


def load_document_detail(base_url: str, doc_id: str, use_api: bool) -> dict:
    if use_api:
        try:
            return api_get(base_url, f"/documents/{doc_id}")
        except Exception:
            pass
    for row in load_local_documents():
        if row["doc_id"] == doc_id:
            return row
    return {}


def list_experiments(base_url: str, use_api: bool) -> list[dict]:
    if use_api:
        try:
            return api_get(base_url, "/experiments")
        except Exception:
            pass
    return load_local_experiments()


def get_experiment_detail(base_url: str, experiment_id: str, use_api: bool) -> dict:
    if use_api:
        try:
            return api_get(base_url, f"/experiments/{experiment_id}")
        except Exception:
            pass
    return load_local_experiment_detail(experiment_id)


def render_sidebar(base_url: str, api_available: bool) -> None:
    mode_label = "Live API mode" if api_available else "Local demo mode"
    st.sidebar.markdown(
        """
        <div class="sidebar-logo">
          <div class="logo-badge">Academic Dashboard</div>
          <div class="logo-title">VietRAGOps</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.text_input("API base URL", value=base_url, key="api_base_url")
    st.sidebar.markdown(f"<div class='mode-pill'>{mode_label}</div>", unsafe_allow_html=True)
    st.sidebar.caption(
        "Demo mode reads local experiment artifacts and runs the offline pipeline directly from this workspace."
    )
    with st.sidebar.expander("Demo instructions", expanded=False):
        st.markdown(
            "\n".join(
                [
                    "- Start the backend with `uvicorn app.main:app --reload` for live API mode.",
                    "- Run the UI with `streamlit run frontend/streamlit_app.py`.",
                    "- Set `VIETRAGOPS_API_BASE_URL` if the API is not on `http://127.0.0.1:8000`.",
                    "- Set `VIETRAGOPS_DEMO_MODE=force_local` to skip API probing.",
                ]
            )
        )


def main() -> None:
    inject_academic_light_css()
    base_url = st.session_state.get("api_base_url", API_BASE_URL)
    api_available = is_api_available(base_url)
    render_sidebar(base_url, api_available)
    render_page_header()

    ask_tab, agent_tab, evidence_tab, evaluation_tab, documents_tab = st.tabs(
        ["Ask", "Local Agent", "Evidence", "Evaluation", "Documents"]
    )

    with ask_tab:
        st.markdown("<div class='section-title'>Ask</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p class='section-intro'>
              Submit a question, tune retrieval depth, and inspect the grounded answer with citations,
              refusal guardrails, and optional debug traces.
            </p>
            """,
            unsafe_allow_html=True,
        )
        default_question = st.session_state.get("last_question", "Cấu trúc email sinh viên TDTU là gì?")
        st.markdown(
            """
            <div class="academic-panel">
              <div class="mode-pill">Query Controls</div>
              <p class="section-intro">Adjust retrieval depth and toggle debug output without changing answer behavior.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        prompt_col, control_col = st.columns([2.3, 1.2])
        with prompt_col:
            question = st.text_input("Question", value=default_question, key="ask_question")
        with control_col:
            top_k = st.slider("Top-k context", min_value=3, max_value=8, value=5, key="ask_top_k")
            debug = st.toggle("Show retrieval debug", value=True, key="ask_debug")
        submit = st.button("Generate grounded answer", type="primary")

        if submit:
            st.session_state["last_question"] = question
            with st.spinner("Building grounded answer..."):
                if api_available:
                    try:
                        response = api_post(base_url, "/ask", {"question": question, "top_k": top_k, "debug": debug})
                        mode_label = "Live API mode"
                    except Exception:
                        response = ask_local(question, debug, top_k)
                        mode_label = "Local demo mode"
                else:
                    response = ask_local(question, debug, top_k)
                    mode_label = "Local demo mode"
                st.session_state["ask_response"] = response
                st.session_state["ask_mode_label"] = mode_label

        render_answer_view(
            st.session_state.get("ask_response", {}),
            st.session_state.get("ask_mode_label", "Awaiting query"),
            show_debug=debug,
        )

    with agent_tab:
        st.markdown("<div class='section-title'>Local Agent</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p class='section-intro'>
              Demo optional local Ollama tool calling. The app asks the model to call
              <span class="mono">retrieve_policy_context</span>, executes retrieval internally, and falls back to
              grounded retrieval if the model skips tool calls or Ollama is unavailable.
            </p>
            """,
            unsafe_allow_html=True,
        )
        agent_question = st.text_input(
            "Agent question",
            value=st.session_state.get(
                "agent_last_question",
                "Ngành Khoa học máy tính cần bao nhiêu tín chỉ để tốt nghiệp?",
            ),
            key="agent_question",
        )
        agent_top_k = st.slider("Agent top-k", min_value=1, max_value=5, value=5, key="agent_top_k")
        agent_debug = st.toggle("Show agent debug", value=True, key="agent_debug")
        if st.button("Run local agent", key="agent_submit"):
            st.session_state["agent_last_question"] = agent_question
            with st.spinner("Running local agent demo..."):
                if api_available:
                    try:
                        response = api_post(
                            base_url,
                            "/agent/ask",
                            {"question": agent_question, "top_k": agent_top_k, "return_debug": agent_debug},
                        )
                        mode_label = "Live API mode"
                    except Exception:
                        response = ask_local_agent(agent_question, agent_debug, agent_top_k)
                        mode_label = "Local demo mode"
                else:
                    response = ask_local_agent(agent_question, agent_debug, agent_top_k)
                    mode_label = "Local demo mode"
                st.session_state["agent_response"] = response
                st.session_state["agent_mode_label"] = mode_label

        health_payload = get_agent_status_payload(base_url, api_available)
        ollama_status = health_payload.get("ollama", {})
        provider_name = health_payload.get("llm_provider", get_settings().llm_provider)
        model_name = health_payload.get("llm_model", get_settings().ollama_model)

        if ollama_status.get("available") and ollama_status.get("model_available"):
            st.success(f"Ollama is available at {ollama_status['base_url']} with model `{ollama_status['model']}`.")
        else:
            st.warning("Ollama local mode is optional and currently unavailable.")
            st.markdown(
                "\n".join(
                    [
                        f"- Expected base URL: `{get_settings().ollama_base_url}`",
                        f"- Expected model: `{get_settings().ollama_model}`",
                        "- Start Ollama if needed: `ollama serve`",
                        f"- Pull the model if missing: `ollama pull {get_settings().ollama_model}`",
                        f"- Warm the model up once: `ollama run {get_settings().ollama_model}`",
                    ]
                )
            )
            if ollama_status.get("error"):
                st.caption(ollama_status["error"])

        agent_response = st.session_state.get("agent_response", {})
        active_provider = agent_response.get("provider", provider_name)
        active_model = agent_response.get("model", model_name)
        generation_mode = agent_response.get("generation_mode", "Awaiting query")
        fallback_used = "Yes" if agent_response.get("fallback_used") else "No"
        confidence_value = agent_response.get("confidence")
        confidence_label = f"{float(confidence_value):.0%}" if confidence_value is not None else "N/A"
        citations_status = "Citations verified" if agent_response.get("citations_verified") else "Awaiting query"
        status_col1, status_col2, status_col3 = st.columns(3)
        status_col4, status_col5, status_col6 = st.columns(3)
        status_col1.metric("Provider", active_provider)
        status_col2.metric("Model", active_model)
        status_col3.metric("Generation Mode", generation_mode)
        status_col4.metric("Fallback Used", fallback_used)
        status_col5.metric("Confidence", confidence_label)
        status_col6.metric("Citations", citations_status)
        if st.session_state.get("agent_mode_label"):
            st.caption(st.session_state["agent_mode_label"])
        if active_provider == "mock":
            st.info("Start the API with `LLM_PROVIDER=ollama` to use the local model.")
        if agent_response.get("fallback_reason"):
            st.caption(f"Fallback reason: {agent_response['fallback_reason']}")

        if agent_response:
            render_answer_view(
                {
                    "answer": agent_response.get("answer", ""),
                    "citations": agent_response.get("citations", []),
                    "confidence": agent_response.get("confidence", 0.0),
                    "refusal": agent_response.get("refusal", False),
                    "refusal_reason": agent_response.get("refusal_reason"),
                    "retrieval_debug": agent_response.get("debug", {}).get("retrieval_debug", {}),
                },
                agent_response.get("generation_mode", "Local Agent"),
                show_debug=agent_debug,
            )
            st.markdown("**Tool Call Trace**")
            if agent_response.get("tool_calls"):
                st.json(agent_response["tool_calls"])
            else:
                st.caption("No model-emitted tool calls were returned, so the app answered from verified retrieved chunks.")
            st.markdown("**Retrieved Chunks / Citations**")
            st.json(
                {
                    "retrieved_chunks": agent_response.get("retrieved_chunks", []),
                    "citations": agent_response.get("citations", []),
                }
            )

    with evidence_tab:
        st.markdown("<div class='section-title'>Evidence</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p class='section-intro'>
              Review ranked chunks, authority metadata, score components, and source paths for the current query.
            </p>
            """,
            unsafe_allow_html=True,
        )
        evidence_question = st.text_input(
            "Evidence query",
            value=st.session_state.get("last_question", "Điều kiện tốt nghiệp của sinh viên là gì?"),
            key="evidence_question",
        )
        evidence_top_k = st.slider("Evidence top-k", min_value=3, max_value=10, value=5, key="evidence_top_k")
        if st.button("Inspect retrieval evidence"):
            st.session_state["last_question"] = evidence_question
            with st.spinner("Running advanced retrieval..."):
                st.session_state["evidence_results"] = retrieve_local(evidence_question, evidence_top_k)
                st.session_state["evidence_mode_label"] = "Local advanced retrieval inspector"

        render_evidence_table(st.session_state.get("evidence_results", []))
        if st.session_state.get("evidence_mode_label"):
            st.caption(st.session_state["evidence_mode_label"])

    with evaluation_tab:
        st.markdown("<div class='section-title'>Evaluation</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p class='section-intro'>
              Compare experiment artifacts, benchmark metrics, and latency behavior from the saved evaluation runs.
            </p>
            """,
            unsafe_allow_html=True,
        )
        experiments = list_experiments(base_url, api_available)
        if experiments:
            experiment_options = {
                f"{item['experiment_type']} :: {item['experiment_id']}": item["experiment_id"] for item in experiments
            }
            selected_label = st.selectbox("Experiment selector", list(experiment_options.keys()))
            selected_id = experiment_options[selected_label]
            detail = get_experiment_detail(base_url, selected_id, api_available)
            mode_label = "Live API artifact browser" if api_available else "Local experiment browser"
            render_eval_dashboard(detail, mode_label)
        else:
            st.info("No experiments were found.")

    with documents_tab:
        st.markdown("<div class='section-title'>Documents</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <p class='section-intro'>
              Inspect the corpus inventory, source authority, parsing status, and chunk coverage for each document.
            </p>
            """,
            unsafe_allow_html=True,
        )
        documents = load_documents(base_url, api_available)
        if documents:
            document_ids = [item["doc_id"] for item in documents]
            selected_doc_id = st.selectbox("Document selector", document_ids)
            selected_detail = load_document_detail(base_url, selected_doc_id, api_available)
            render_document_table(documents, selected_detail=selected_detail)
        else:
            st.info("No document inventory is available.")


if __name__ == "__main__":
    main()
