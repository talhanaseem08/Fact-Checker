import html
from typing import Iterable

import streamlit as st

from config import APP_TITLE
from src.fact_checker import check_claim
from src.llm_utils import load_local_llm


EXAMPLE_CLAIMS = [
    "Drinking 8 glasses of water daily is necessary for everyone.",
    "AI will completely replace all programmers.",
    "The Earth is flat.",
    "Exercise can improve mental health.",
    "Electric cars produce zero emissions.",
    "Coffee is always bad for health.",
]


@st.cache_resource(show_spinner=False)
def get_model_bundle():
    try:
        return load_local_llm(), None
    except Exception as exc:
        return None, str(exc)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0f1117;
            --card: #171b24;
            --card-2: #1f2533;
            --border: #2a3040;
            --accent: #4f8cff;
            --success: #27c93f;
            --warning: #ffbd2e;
            --danger: #ff5f56;
            --text: #f5f7fb;
            --muted: #b8bdc9;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2.25rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, h5, h6, p, li, label, span {
            color: var(--text);
            letter-spacing: 0;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {
            color: var(--muted);
        }

        .hero {
            border: 1px solid var(--border);
            background:
                linear-gradient(135deg, rgba(79, 140, 255, 0.18), rgba(39, 201, 63, 0.08)),
                var(--card);
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 1.25rem;
        }

        .hero h1 {
            margin: 0 0 0.65rem 0;
            font-size: clamp(2rem, 4vw, 3.25rem);
            line-height: 1.05;
        }

        .hero p {
            margin: 0;
            color: var(--muted);
            font-size: 1.05rem;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1.2rem;
        }

        .pill {
            border: 1px solid var(--border);
            background: rgba(31, 37, 51, 0.9);
            color: var(--text);
            padding: 0.42rem 0.72rem;
            border-radius: 999px;
            font-size: 0.85rem;
            white-space: nowrap;
        }

        .card {
            border: 1px solid var(--border);
            background: var(--card);
            border-radius: 8px;
            padding: 1.15rem;
            margin: 0.8rem 0;
        }

        .card.secondary {
            background: var(--card-2);
        }

        .card h3 {
            margin: 0 0 0.8rem 0;
            font-size: 1.05rem;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 750;
            line-height: 1.1;
            margin: 0.2rem 0;
        }

        .muted {
            color: var(--muted);
        }

        .verdict-supported {
            color: var(--success);
        }

        .verdict-contradicted {
            color: var(--danger);
        }

        .verdict-mixed {
            color: var(--warning);
        }

        .verdict-insufficient {
            color: var(--muted);
        }

        .evidence-item {
            border-left: 3px solid var(--accent);
            padding: 0.72rem 0 0.72rem 0.85rem;
            margin: 0.72rem 0;
            background: rgba(255, 255, 255, 0.015);
        }

        .evidence-item strong {
            color: var(--text);
        }

        .evidence-item a, .source-link a {
            color: var(--accent);
            text-decoration: none;
        }

        .source-link {
            border-bottom: 1px solid var(--border);
            padding: 0.65rem 0;
        }

        .source-link:last-child {
            border-bottom: none;
        }

        .warning-box {
            border-left: 4px solid var(--warning);
            background: rgba(255, 189, 46, 0.08);
            padding: 0.75rem 0.95rem;
            border-radius: 6px;
            margin: 0.55rem 0;
            color: var(--text);
        }

        div[data-testid="stTextArea"] textarea {
            background: var(--card-2);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 8px;
            min-height: 130px;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 1px rgba(79, 140, 255, 0.3);
        }

        div.stButton > button {
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--card-2);
            color: var(--text);
            min-height: 2.5rem;
            white-space: normal;
        }

        div.stButton > button:hover {
            border-color: var(--accent);
            color: var(--text);
        }

        div.stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: white;
            font-weight: 700;
        }

        [data-testid="stExpander"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
        }

        [data-testid="stProgress"] > div > div > div {
            background-color: var(--accent);
        }

        hr {
            border-color: var(--border);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def html_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def verdict_class(verdict: str) -> str:
    key = verdict.lower().replace(" ", "-")
    if key not in {"supported", "contradicted", "mixed", "insufficient-evidence"}:
        return "verdict-insufficient"
    return f"verdict-{key.replace('-evidence', '')}"


def render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Fact-Checking Chatbot</h1>
            <p>Live Web Search + Local Qwen LLM + Evidence-Based Confidence Scoring</p>
            <div class="pill-row">
                <span class="pill">No API Key Required</span>
                <span class="pill">Local LLM</span>
                <span class="pill">Live Evidence</span>
                <span class="pill">NLP Project</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def set_example_claim(claim: str) -> None:
    st.session_state.claim_input = claim


def render_examples() -> None:
    st.markdown("#### Try an example claim")
    rows = [st.columns(3), st.columns(3)]
    for index, claim in enumerate(EXAMPLE_CLAIMS):
        with rows[index // 3][index % 3]:
            st.button(
                claim,
                key=f"example_{index}",
                on_click=set_example_claim,
                args=(claim,),
                use_container_width=True,
            )


def render_evidence(title: str, items: Iterable[dict], empty_text: str) -> None:
    items = list(items)
    st.markdown(
        f'<div class="card"><h3>{html_escape(title)}</h3>',
        unsafe_allow_html=True,
    )
    if not items:
        st.markdown(f'<p class="muted">{html_escape(empty_text)}</p>', unsafe_allow_html=True)
    for item in items:
        sentence = html_escape(item.get("sentence", ""))
        source_title = html_escape(item.get("title", "Untitled source"))
        url = html_escape(item.get("url", ""))
        score = html_escape(item.get("score", ""))
        st.markdown(
            f"""
            <div class="evidence-item">
                <div>{sentence}</div>
                <div class="muted">
                    <strong>{source_title}</strong> | relevance {score}
                    | <a href="{url}" target="_blank">open source</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_sources(sources: Iterable[dict]) -> None:
    st.markdown('<div class="card"><h3>Sources</h3>', unsafe_allow_html=True)
    for source in sources:
        title = html_escape(source.get("title", "Untitled source"))
        url = html_escape(source.get("url", ""))
        domain = html_escape(source.get("domain", ""))
        snippet = html_escape(source.get("snippet", ""))
        st.markdown(
            f"""
            <div class="source-link">
                <a href="{url}" target="_blank"><strong>{title}</strong></a>
                <div class="muted">{domain}</div>
                <div class="muted">{snippet}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_result(result: dict) -> None:
    verdict = result.get("verdict", "Insufficient Evidence")
    confidence = int(result.get("confidence", 0))
    label = result.get("confidence_label", "Low")
    timestamp = result.get("timestamp", "")

    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            f"""
            <div class="card secondary">
                <h3>Verdict</h3>
                <div class="metric-value {verdict_class(verdict)}">{html_escape(verdict)}</div>
                <div class="muted">Search timestamp: {html_escape(timestamp)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="card secondary">
                <h3>Confidence Score</h3>
                <div class="metric-value">{confidence}/100</div>
                <div class="muted">{html_escape(label)} confidence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(confidence / 100)

    st.markdown(
        f"""
        <div class="card">
            <h3>Final Answer</h3>
            <div style="white-space: pre-wrap;">{html_escape(result.get("answer", ""))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_evidence(
        "Supporting Evidence",
        result.get("supporting_evidence", []),
        "No direct supporting evidence was extracted.",
    )
    render_evidence(
        "Contradicting Evidence",
        result.get("contradicting_evidence", []),
        "No direct contradicting evidence was extracted.",
    )
    render_evidence(
        "Neutral or Related Evidence",
        result.get("neutral_evidence", []),
        "No neutral evidence was extracted.",
    )
    render_sources(result.get("sources", []))

    warnings = result.get("warnings", [])
    if warnings:
        st.markdown('<div class="card"><h3>Warnings</h3>', unsafe_allow_html=True)
        for warning in warnings:
            st.markdown(
                f'<div class="warning-box">{html_escape(warning)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_project_info() -> None:
    with st.expander("About this Project"):
        st.write(
            "This Natural Language Processing project combines information retrieval, "
            "evidence ranking, rule-based evidence classification, confidence scoring, "
            "and a single local Hugging Face LLM. It does not use OpenAI, Gemini, "
            "Claude, paid APIs, or API keys."
        )

    with st.expander("How It Works"):
        st.write(
            "Search -> Evidence Extraction -> Evidence Classification -> "
            "Local LLM Explanation -> Confidence Score"
        )
        st.write(
            "The chatbot searches the live web, reads accessible pages, extracts "
            "relevant evidence sentences, classifies them as supporting, "
            "contradicting, or neutral, and then asks Qwen/Qwen2.5-0.5B-Instruct "
            "to write a concise explanation grounded only in that evidence."
        )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="?", layout="wide")
    inject_css()
    render_header()

    if "claim_input" not in st.session_state:
        st.session_state.claim_input = ""

    st.text_area(
        "Enter a claim or question to fact-check",
        key="claim_input",
        placeholder="Example: Exercise can improve mental health.",
    )

    button_left, button_right = st.columns([1, 3])
    with button_left:
        submitted = st.button("Check Claim", type="primary", use_container_width=True)
    with button_right:
        st.markdown(
            '<p class="muted">Results are grounded in live web evidence. Weak evidence is reported as insufficient.</p>',
            unsafe_allow_html=True,
        )

    render_examples()

    if submitted:
        claim = st.session_state.claim_input.strip()
        if not claim:
            st.error("Please enter a claim or question first.")
        else:
            with st.spinner("Searching the web, extracting evidence, and generating a grounded answer..."):
                model_bundle, model_error = get_model_bundle()
                result = check_claim(
                    claim,
                    model_bundle=model_bundle,
                    generate_with_llm=model_bundle is not None,
                )
                if model_error:
                    result.setdefault("warnings", []).append(
                        "The local Qwen model could not be loaded. A deterministic evidence-based fallback answer was used."
                    )
                    result.setdefault("warnings", []).append(model_error)
            render_result(result)

    render_project_info()

    st.markdown("---")
    st.markdown(
        '<p class="muted" style="text-align:center;">Academic NLP Project - Fact Checking, Information Retrieval, Evidence Ranking, Local LLM</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

