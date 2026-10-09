"""Streamlit chat interface for the local FastAPI service."""
import os

import httpx
import streamlit as st

st.set_page_config(
    page_title="Ops Copilot | Retail Operations",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #142a3b;
        --muted: #607486;
        --teal: #087e78;
        --line: #dce6ec;
        --surface: #ffffff;
        --canvas: #f3f7f8;
    }
    [data-testid="stAppViewContainer"] { background: var(--canvas); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stMainBlockContainer"] {
        max-width: 1080px;
        padding-top: 2.3rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3, p, label { color: var(--ink); }
    .brand-kicker {
        color: var(--teal);
        font-size: .76rem;
        font-weight: 750;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }
    .brand-title {
        color: var(--ink) !important;
        font-size: clamp(2rem, 4vw, 2.8rem);
        font-weight: 760;
        letter-spacing: -.045em;
        line-height: 1.08;
        margin: 0;
    }
    .brand-copy {
        color: var(--muted);
        font-size: 1.05rem;
        margin-top: .7rem;
        max-width: 650px;
    }
    .trust-note {
        background: #e8f3f2;
        border: 1px solid #cde4e1;
        border-radius: 12px;
        color: #245e5c;
        font-size: .88rem;
        line-height: 1.5;
        padding: .9rem 1rem;
        margin: 1.15rem 0 1.7rem;
    }
    [data-testid="stForm"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1.25rem 1.35rem 1rem;
        box-shadow: 0 8px 24px rgba(20, 42, 59, .045);
    }
    [data-testid="stTextArea"] textarea {
        background: #fbfdfe;
        border-color: #cbd8e0;
        border-radius: 10px;
        color: var(--ink);
        line-height: 1.5;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--teal);
        box-shadow: 0 0 0 1px var(--teal);
    }
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stButton"] button[kind="primary"] {
        background: var(--teal);
        border: 1px solid var(--teal);
        border-radius: 9px;
        color: #fff;
        font-weight: 650;
        min-height: 2.7rem;
    }
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stButton"] button[kind="primary"]:hover {
        background: #066963;
        border-color: #066963;
        color: #fff;
    }
    [data-testid="stButton"] button[kind="secondary"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 9px;
        color: #304b5e;
        min-height: 2.55rem;
    }
    [data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: var(--teal);
        color: var(--teal);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--line);
        border-radius: 14px;
    }
    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: .8rem 1rem;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stExpander"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 10px;
    }
    .section-label {
        color: var(--muted);
        font-size: .76rem;
        font-weight: 700;
        letter-spacing: .1em;
        margin: 2rem 0 .6rem;
        text-transform: uppercase;
    }
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] {
            padding: 1.4rem 1rem 3rem;
        }
        [data-testid="stForm"] { padding: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="brand-kicker">Retail operations · AI assistant</div>
    <h1 class="brand-title">Make the next decision<br>with confidence.</h1>
    <p class="brand-copy">
        Ask about store policy or operations data. Get a clear answer with the
        plan, results, and evidence behind it.
    </p>
    <div class="trust-note">
        <strong>Evidence first.</strong> Responses are grounded in policy or
        operations data. If the assistant cannot verify an answer, it will
        recommend human review.
    </div>
    """,
    unsafe_allow_html=True,
)

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

st.markdown('<div class="section-label">Try an example</div>', unsafe_allow_html=True)
examples = [
    "What is the return window?",
    "Can an order be changed after it ships?",
    "When should I escalate a safety concern?",
]
example_columns = st.columns(3)
for index, (column, example) in enumerate(zip(example_columns, examples)):
    with column:
        if st.button(example, key=f"example_{index}", use_container_width=True):
            st.session_state.question_input = example
            st.session_state.pop("assistant_result", None)
            st.session_state.pop("assistant_error", None)
            st.rerun()

with st.form("ask_form", clear_on_submit=False):
    question = st.text_area(
        "Your question",
        key="question_input",
        placeholder="For example: What is the return window for an online order?",
        height=105,
        max_chars=2000,
        help="Ask one clear question about a store policy, order, or operations metric.",
    )
    left, right = st.columns([3, 1])
    with left:
        confirmed = st.checkbox(
            "I confirm any requested ticket action",
            help="Required in addition to the service's ticket-action setting. It does not enable ticket actions by itself.",
        )
    with right:
        submitted = st.form_submit_button(
            "Get an answer  →",
            type="primary",
            use_container_width=True,
        )

if submitted:
    if not question.strip():
        st.warning("Enter a question to get started.")
    else:
        try:
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            if "://" not in api_base:
                if "." not in api_base:
                    api_base = f"{api_base}.onrender.com"
                api_base = f"https://{api_base}"
            response = httpx.post(
                f"{api_base.rstrip('/')}/ask",
                json={"question": question, "confirm": confirmed},
                timeout=120,
            )
            response.raise_for_status()
            st.session_state.assistant_result = response.json()
            st.session_state.assistant_question = question.strip()
            st.session_state.assistant_error = None
        except httpx.HTTPError as exc:
            st.session_state.assistant_result = None
            st.session_state.assistant_error = str(exc)

if st.session_state.get("assistant_error"):
    st.error(
        "The assistant could not complete your request. Check that the service "
        "is available, then try again."
    )
    with st.expander("Technical details"):
        st.code(st.session_state.assistant_error)

result = st.session_state.get("assistant_result")
if result:
    st.markdown('<div class="section-label">Assistant response</div>', unsafe_allow_html=True)
    st.caption(f"Your question: {st.session_state.assistant_question}")

    if result["handed_off"]:
        st.warning("Human review recommended. Please verify the details before taking action.")

    with st.container(border=True):
        st.markdown("### Answer")
        st.markdown(result["answer"])

    metric_columns = st.columns(3)
    metric_columns[0].metric("Confidence", f"{result['confidence']:.0%}")
    metric_columns[1].metric("Evidence sources", len(result["sources"]))
    metric_columns[2].metric("Tool calls", len(result["tool_calls"]))

    if result["sources"]:
        st.markdown("#### Evidence")
        for source in result["sources"]:
            st.markdown(f"- `{source}`")
    else:
        st.caption("No source citations were returned for this response.")

    with st.expander("View the assistant's plan"):
        st.json(result["plan"])
    with st.expander(f"View tool calls and results ({len(result['tool_calls'])})"):
        for index, call in enumerate(result["tool_calls"], start=1):
            st.markdown(f"**Tool call {index} · `{call['tool']}`**")
            st.json(call)
