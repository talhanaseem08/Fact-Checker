import html
from textwrap import dedent
from typing import Iterable

import streamlit as st

from config import APP_TITLE, MAX_SEARCH_RESULTS
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
        dedent(
            """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {
            --bg: #071111;
            --panel: rgba(14, 26, 28, 0.88);
            --panel-2: rgba(18, 33, 37, 0.94);
            --panel-3: rgba(8, 18, 20, 0.82);
            --line: rgba(148, 163, 184, 0.17);
            --line-bright: rgba(125, 211, 252, 0.36);
            --text: #f8fafc;
            --muted: #a8b3c7;
            --faint: #6f7d96;
            --green: #42e8a6;
            --cyan: #5bc8ff;
            --amber: #ffc861;
            --red: #ff6f91;
            --shadow: rgba(0, 0, 0, 0.34);
            --body: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            --display: "Space Grotesk", var(--body);
        }

        #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
            display: none;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .stApp {
            background:
                radial-gradient(circle at 16% 0%, rgba(66, 232, 166, 0.14), transparent 28rem),
                radial-gradient(circle at 88% 6%, rgba(91, 200, 255, 0.10), transparent 24rem),
                linear-gradient(180deg, rgba(255, 255, 255, 0.016), transparent 22rem),
                var(--bg);
            color: var(--text);
            font-family: var(--body);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.6rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, h5, h6, p, li, label, span, div {
            color: var(--text);
            letter-spacing: 0;
        }

        h1, h2, h3 {
            font-family: var(--display);
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {
            color: var(--muted);
        }

        .topbar {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            gap: 1rem;
            min-height: 2.5rem;
            color: var(--faint);
            font-size: 0.82rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            font-weight: 800;
        }

        .brand strong {
            color: var(--text);
            font-family: var(--display);
            font-size: 1.08rem;
            letter-spacing: 0;
        }

        .brand-mark {
            display: inline-grid;
            place-items: center;
            width: 2rem;
            height: 2rem;
            border-radius: 8px;
            background: linear-gradient(135deg, var(--cyan), var(--green));
            color: #07111f;
            font-weight: 900;
        }

        .status-dot {
            display: inline-block;
            width: 0.4rem;
            height: 0.4rem;
            border-radius: 999px;
            background: var(--green);
            box-shadow: 0 0 14px rgba(50, 214, 154, 0.9);
        }

        .hero-panel,
        .section-panel {
            border: 1px solid var(--line);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.045), rgba(255, 255, 255, 0.01)),
                var(--panel);
            border-radius: 8px;
            box-shadow: 0 22px 70px var(--shadow);
            backdrop-filter: blur(18px);
        }

        .hero-panel {
            margin: 1.1rem 0 0.9rem;
            overflow: hidden;
        }

        .hero-title {
            padding: 1.8rem 1.65rem 1.35rem;
            border-bottom: 1px solid var(--line);
        }

        .hero-title h1 {
            margin: 0;
            max-width: 740px;
            font-size: clamp(2.3rem, 5vw, 4.6rem);
            line-height: 0.98;
            letter-spacing: -0.03em;
        }

        .hero-copy {
            max-width: 34rem;
            margin-top: 0.8rem;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.65;
        }

        .telemetry-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            padding: 1rem;
        }

        .telemetry {
            min-height: 5rem;
            padding: 0.9rem 1rem;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel-3);
            position: relative;
        }

        .telemetry::after {
            content: "";
            position: absolute;
            top: 0.9rem;
            right: 0.9rem;
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 99px;
            background: var(--cyan);
            opacity: 0.85;
        }

        .telemetry small,
        .panel-label,
        .eyebrow {
            display: block;
            color: var(--faint);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .telemetry strong {
            display: block;
            margin-top: 0.65rem;
            color: var(--text);
            font-size: 1.15rem;
            font-weight: 700;
        }

        .telemetry strong.cyan {
            color: var(--cyan);
        }

        .section-panel {
            padding: 1.05rem;
            margin: 0.9rem 0;
        }

        .section-heading {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.65rem;
            border-bottom: 1px solid var(--line);
            padding-bottom: 0.6rem;
        }

        .section-heading h3 {
            margin: 0;
            font-size: 1.02rem;
            line-height: 1.2;
        }

        .hint {
            color: var(--faint);
            font-size: 0.78rem;
        }

        .claim-readout {
            padding: 0.95rem;
            background: var(--panel-3);
            border: 1px solid var(--line);
            border-radius: 8px;
            color: var(--text);
            font-size: 0.95rem;
            line-height: 1.65;
            white-space: pre-wrap;
        }

        .metric-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            margin-top: 0.55rem;
        }

        .metric-cell {
            padding: 0.85rem 0.95rem;
            border-right: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.024);
        }

        .metric-cell:last-child {
            border-right: 0;
        }

        .metric-cell b {
            display: block;
            margin-top: 0.45rem;
            font-family: var(--display);
            font-size: 2.1rem;
            line-height: 1;
        }

        .green { color: var(--green); }
        .cyan { color: var(--cyan); }
        .amber { color: var(--amber); }
        .red { color: var(--red); }
        .muted { color: var(--muted); }

        .verdict-grid {
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 0.9rem;
            margin: 0.9rem 0;
        }

        .signal-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background:
                linear-gradient(145deg, rgba(91, 200, 255, 0.055), rgba(66, 232, 166, 0.035)),
                var(--panel-2);
            padding: 1.15rem;
            min-height: 10rem;
            overflow: hidden;
        }

        .verdict-word {
            margin: 0.75rem 0 0.5rem;
            font-family: var(--display);
            font-size: clamp(2rem, 5vw, 3.2rem);
            line-height: 1;
        }

        .confidence-word {
            margin-top: 0.65rem;
            font-family: var(--display);
            font-size: 2.6rem;
            line-height: 1;
        }

        .bar-grid {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 0.35rem;
            margin: 0.85rem 0 0.55rem;
        }

        .bar-segment {
            height: 0.55rem;
            border-radius: 99px;
            background: rgba(255, 255, 255, 0.075);
        }

        .bar-segment.on {
            background: var(--green);
            box-shadow: 0 0 12px rgba(50, 214, 154, 0.24);
        }

        .answer-block {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel-3);
            padding: 1rem;
            white-space: pre-wrap;
            line-height: 1.7;
            color: #dbe5ea;
            font-size: 0.95rem;
        }

        .verdict-supported {
            color: var(--green);
        }

        .verdict-contradicted {
            color: var(--red);
        }

        .verdict-mixed {
            color: var(--amber);
        }

        .verdict-insufficient {
            color: var(--muted);
        }

        .evidence-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
        }

        .evidence-lane {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel-3);
            min-height: 14rem;
            overflow: hidden;
        }

        .lane-head {
            display: flex;
            justify-content: space-between;
            gap: 0.5rem;
            padding: 0.72rem 0.8rem;
            border-bottom: 1px solid var(--line);
            color: var(--text);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .evidence-item {
            border-bottom: 1px solid rgba(35, 41, 54, 0.8);
            padding: 0.78rem 0.8rem;
            background: rgba(255, 255, 255, 0.012);
            line-height: 1.55;
            font-size: 0.86rem;
        }

        .evidence-item:last-child {
            border-bottom: 0;
        }

        .evidence-item strong,
        .source-title {
            color: var(--text);
        }

        .evidence-item a, .source-link a {
            color: var(--cyan);
            text-decoration: none;
        }

        .evidence-meta {
            margin-top: 0.55rem;
            color: var(--faint);
            font-size: 0.7rem;
            text-transform: uppercase;
        }

        .empty-state {
            padding: 0.9rem 0.8rem;
            color: var(--faint);
            font-size: 0.84rem;
            line-height: 1.5;
        }

        .source-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }

        .source-link {
            min-height: 6rem;
            padding: 0.95rem;
            border-right: 1px solid var(--line);
            border-bottom: 1px solid var(--line);
            background: var(--panel-3);
        }

        .source-link:nth-child(2n) {
            border-right: 0;
        }

        .warning-box {
            border: 1px solid rgba(255, 191, 87, 0.38);
            background: rgba(255, 191, 87, 0.055);
            padding: 0.75rem 0.85rem;
            border-radius: 8px;
            margin: 0.55rem 0;
            color: var(--text);
            font-size: 0.86rem;
        }

        .examples-title {
            margin: 1.35rem 0 0.55rem;
            color: var(--faint);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .composer-heading {
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 1rem;
            margin: 1.35rem 0 0.75rem;
            padding: 0 0.15rem;
        }

        .composer-heading h2 {
            margin: 0.25rem 0 0;
            font-size: clamp(1.35rem, 2vw, 1.75rem);
            line-height: 1.15;
        }

        .composer-note {
            color: var(--muted);
            font-size: 0.88rem;
            text-align: right;
        }

        div[data-testid="stTextArea"] {
            margin-top: 0.15rem;
        }

        div[data-testid="stTextArea"] > div {
            border-radius: 14px;
            background:
                linear-gradient(135deg, rgba(91, 200, 255, 0.25), rgba(66, 232, 166, 0.2)),
                rgba(255, 255, 255, 0.025);
            padding: 1px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
        }

        div[data-testid="stTextArea"] textarea {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0)),
                #071617 !important;
            border: 1px solid rgba(148, 163, 184, 0.12) !important;
            color: var(--text);
            border-radius: 14px;
            min-height: 154px;
            padding: 1.1rem 1.15rem !important;
            font-family: var(--body);
            font-size: 1rem;
            line-height: 1.6;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextArea"] textarea:disabled {
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
        }

        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--cyan);
            box-shadow:
                0 0 0 1px rgba(91, 200, 255, 0.38),
                0 0 28px rgba(66, 232, 166, 0.10);
        }

        div[data-testid="stTextArea"] label p,
        div[data-testid="stTextArea"] label {
            color: var(--faint);
            font-family: var(--body);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        div.stButton > button {
            border-radius: 14px;
            border: 1px solid var(--line);
            background: var(--panel-2);
            color: var(--text);
            min-height: 2.65rem;
            white-space: normal;
            font-family: var(--body);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0;
        }

        div.stButton > button p {
            color: inherit;
            font: inherit;
            letter-spacing: inherit;
        }

        div.stButton > button:not([kind="primary"]) {
            min-height: 4.2rem;
            justify-content: flex-start;
            text-align: left;
            padding: 0.9rem 1rem 0.9rem 1.15rem;
            background:
                linear-gradient(90deg, rgba(66, 232, 166, 0.12), transparent 0.35rem),
                linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)),
                rgba(11, 30, 32, 0.88);
            border-color: rgba(148, 163, 184, 0.18);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
        }

        div.stButton > button:not([kind="primary"]):hover {
            border-color: var(--cyan);
            background:
                linear-gradient(90deg, rgba(91, 200, 255, 0.32), transparent 0.35rem),
                linear-gradient(180deg, rgba(91, 200, 255, 0.10), rgba(66, 232, 166, 0.04)),
                rgba(11, 30, 32, 0.98);
            color: var(--text);
            transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--cyan), var(--green));
            border-color: transparent;
            color: #03101b;
            font-weight: 700;
            min-height: 3rem;
            border-radius: 999px;
            box-shadow: 0 14px 34px rgba(66, 232, 166, 0.18);
        }

        div.stButton > button[kind="primary"]:hover {
            filter: brightness(1.05);
            transform: translateY(-1px);
        }

        [data-testid="stExpander"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
        }

        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] p {
            font-family: var(--body);
        }

        [data-testid="stProgress"] > div > div > div {
            background-color: var(--green);
        }

        hr {
            border-color: var(--line);
        }

        .footer-line {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            color: var(--faint);
            font-size: 0.78rem;
        }

        @media (max-width: 900px) {
            .hero-title,
            .topbar,
            .footer-line,
            .composer-heading {
                align-items: flex-start;
                flex-direction: column;
            }

            .composer-note {
                text-align: left;
            }

            .telemetry-grid,
            .metric-strip,
            .evidence-grid,
            .source-grid,
            .verdict-grid {
                grid-template-columns: 1fr;
            }

            .telemetry,
            .metric-cell,
            .source-link {
                border-right: 0;
            }
        }
        </style>
        """
        ).strip(),
        unsafe_allow_html=True,
    )


def html_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def clean_html(markup: str) -> str:
    return dedent(markup).strip()


def render_html(markup: str) -> None:
    markup = clean_html(markup)
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def verdict_class(verdict: str) -> str:
    key = verdict.lower().replace(" ", "-")
    if key not in {"supported", "contradicted", "mixed", "insufficient-evidence"}:
        return "verdict-insufficient"
    return f"verdict-{key.replace('-evidence', '')}"


def verdict_color_class(verdict: str) -> str:
    key = verdict.lower()
    if "contradict" in key:
        return "red"
    if "mixed" in key:
        return "amber"
    if "support" in key:
        return "green"
    return "muted"


def confidence_bar(confidence: int) -> str:
    active = round(max(0, min(confidence, 100)) / 10)
    segments = [
        f'<span class="bar-segment{" on" if index < active else ""}"></span>'
        for index in range(10)
    ]
    return '<div class="bar-grid">' + "".join(segments) + "</div>"


def render_header() -> None:
    st.markdown(
        clean_html(
            """
        <div class="topbar">
            <div class="brand"><span class="brand-mark">T</span><strong>TruthLens Studio</strong></div>
        </div>
        <div class="hero-panel">
            <div class="hero-title">
                <div>
                    <h1>Fact-check statements with evidence you can inspect.</h1>
                    <div class="hero-copy">Enter a statement, review the sources, compare supporting and contradicting evidence, and get a grounded answer with confidence scoring.</div>
                </div>
            </div>
            <div class="telemetry-grid">
                <div class="telemetry"><small>Sources checked</small><strong>Up to {max_sources}</strong></div>
                <div class="telemetry"><small>Model</small><strong>Local Qwen</strong></div>
                <div class="telemetry"><small>Search</small><strong class="cyan">Live web</strong></div>
                <div class="telemetry"><small>Keys needed</small><strong>None</strong></div>
            </div>
        </div>
        """.format(max_sources=MAX_SEARCH_RESULTS)
        ),
        unsafe_allow_html=True,
    )


def set_example_claim(claim: str) -> None:
    st.session_state.claim_input = claim


def render_examples() -> None:
    st.markdown('<div class="examples-title">Try an example statement</div>', unsafe_allow_html=True)
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


def render_evidence_lane(title: str, items: Iterable[dict], empty_text: str, color_class: str) -> str:
    items = list(items)
    output = [
        '<div class="evidence-lane">',
        f'<div class="lane-head"><span>{html_escape(title)}</span><span class="{color_class}">{len(items)}</span></div>',
    ]
    if not items:
        output.append(f'<div class="empty-state">{html_escape(empty_text)}</div>')
    for item in items:
        sentence = html_escape(item.get("sentence", ""))
        source_title = html_escape(item.get("title", "Untitled source"))
        url = html_escape(item.get("url", ""))
        score = html_escape(item.get("score", ""))
        output.append(
            clean_html(
                f"""
            <div class="evidence-item">
                <div>{sentence}</div>
                <div class="evidence-meta">
                    <strong>{source_title}</strong> / rel {score}
                    / <a href="{url}" target="_blank">open source</a>
                </div>
            </div>
            """
            )
        )
    output.append("</div>")
    return "".join(output)


def render_sources(sources: Iterable[dict]) -> None:
    sources = list(sources)
    output = [
        '<div class="section-panel">',
        '<div class="section-heading"><h3>Source attribution</h3><span class="hint">ranked web results</span></div>',
        '<div class="source-grid">',
    ]
    for source in sources:
        title = html_escape(source.get("title", "Untitled source"))
        url = html_escape(source.get("url", ""))
        domain = html_escape(source.get("domain", ""))
        snippet = html_escape(source.get("snippet", ""))
        output.append(
            clean_html(
                f"""
            <div class="source-link">
                <a class="source-title" href="{url}" target="_blank">{title}</a>
                <div class="evidence-meta">{domain}</div>
                <div class="muted">{snippet}</div>
            </div>
            """
            )
        )
    if not sources:
        output.append('<div class="empty-state">No sources were returned.</div>')
    output.extend(["</div>", "</div>"])
    render_html("".join(output))


def render_result(result: dict) -> None:
    verdict = result.get("verdict", "Insufficient Evidence")
    confidence = int(result.get("confidence", 0))
    label = result.get("confidence_label", "Low")
    timestamp = result.get("timestamp", "")
    support = list(result.get("supporting_evidence", []))
    contradict = list(result.get("contradicting_evidence", []))
    neutral = list(result.get("neutral_evidence", []))
    sources = list(result.get("sources", []))
    color_class = verdict_color_class(verdict)

    render_html(
        clean_html(
            f"""
        <div class="section-panel">
            <div class="section-heading"><h3>Statement under review</h3><span class="hint">{html_escape(timestamp)}</span></div>
            <div class="claim-readout">{html_escape(result.get("claim", ""))}</div>
            <div class="metric-strip">
                <div class="metric-cell"><span class="panel-label">Sources</span><b>{len(sources)}</b></div>
                <div class="metric-cell"><span class="panel-label">Supports</span><b class="green">{len(support)}</b></div>
                <div class="metric-cell"><span class="panel-label">Contradicts</span><b class="red">{len(contradict)}</b></div>
                <div class="metric-cell"><span class="panel-label">Neutral</span><b class="muted">{len(neutral)}</b></div>
                <div class="metric-cell"><span class="panel-label">Confidence</span><b class="cyan">{confidence}%</b></div>
            </div>
        </div>

        <div class="verdict-grid">
            <div class="signal-card">
                <span class="panel-label">Verdict</span>
                <div class="verdict-word {verdict_class(verdict)}">{html_escape(verdict)}</div>
                <div class="muted">Most relevant evidence is classified, balanced, and scored before the final explanation is generated.</div>
            </div>
            <div class="signal-card">
                <span class="panel-label">Confidence</span>
                <div class="confidence-word {color_class}">{confidence}%</div>
                {confidence_bar(confidence)}
                <div class="muted">{html_escape(label)} confidence based on source count, evidence agreement, diversity, and overlap.</div>
            </div>
        </div>

        <div class="section-panel">
            <div class="section-heading"><h3>Grounded answer</h3><span class="hint">generated from retrieved evidence</span></div>
            <div class="answer-block">{html_escape(result.get("answer", ""))}</div>
        </div>
        """,
        )
    )

    render_html(
        clean_html(
            """
        <div class="section-panel">
            <div class="section-heading"><h3>Evidence board</h3><span class="hint">classified sentences</span></div>
            <div class="evidence-grid">
        """
        + render_evidence_lane(
            "Supporting",
            support,
            "No direct supporting evidence was extracted.",
            "green",
        )
        + render_evidence_lane(
            "Contradicting",
            contradict,
            "No direct contradicting evidence was extracted.",
            "red",
        )
        + render_evidence_lane(
            "Neutral",
            neutral,
            "No neutral evidence was extracted.",
            "muted",
        )
        + """
            </div>
        </div>
        """,
        )
    )
    render_sources(sources)

    warnings = result.get("warnings", [])
    if warnings:
        warning_output = [
            '<div class="section-panel">',
            '<div class="section-heading"><h3>Warnings</h3><span class="hint">pipeline notes</span></div>',
        ]
        for warning in warnings:
            warning_output.append(f'<div class="warning-box">{html_escape(warning)}</div>')
        warning_output.append("</div>")
        render_html("".join(warning_output))


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

    render_html(
        """
        <div class="composer-heading">
            <div>
                <span class="eyebrow">Statement workspace</span>
                <h2>Drop in a statement to verify</h2>
            </div>
            <div class="composer-note">Live sources, evidence labels, and confidence scoring.</div>
        </div>
        """
    )
    st.text_area(
        "Statement or question",
        key="claim_input",
        placeholder="Example: Exercise can improve mental health.",
    )

    button_left, _ = st.columns([1, 3])
    with button_left:
        submitted = st.button("Run Check", type="primary", use_container_width=True)

    render_examples()

    if submitted:
        claim = st.session_state.claim_input.strip()
        if not claim:
            st.error("Please enter a statement or question first.")
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
        '<div class="footer-line"><span>TruthLens Studio</span><span>Search + Evidence + Qwen</span></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
