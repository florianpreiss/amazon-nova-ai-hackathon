"""
KODA — Streamlit Chat Interface.
"""

import html as html_lib
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.i18n import DEFAULT_LANGUAGE, get_agent_label, t

# ── Page config ────────────────────────────────────────

st.set_page_config(
    page_title="KODA — Dein Studienbegleiter | Your Study Companion",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Session state ──────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True
if "lang" not in st.session_state:
    st.session_state.lang = DEFAULT_LANGUAGE

lang = st.session_state.lang

# ── CSS ────────────────────────────────────────────────

st.markdown(
    """
<style>
    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Background images on edges ───────────── */
    .stApp::before, .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        bottom: 0;
        width: 280px;
        background-size: cover;
        background-repeat: no-repeat;
        pointer-events: none;
        z-index: 0;
        opacity: 0.7;
    }
    .stApp::before {
        left: 0;
        background-image: url('app/static/left-bg.jpeg');
        background-position: right center;
        -webkit-mask-image: linear-gradient(to right, rgba(0,0,0,1) 0%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0) 100%);
        mask-image: linear-gradient(to right, rgba(0,0,0,1) 0%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0) 100%);
    }
    .stApp::after {
        right: 0;
        background-image: url('app/static/right-bg.jpeg');
        background-position: left center;
        -webkit-mask-image: linear-gradient(to left, rgba(0,0,0,1) 0%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0) 100%);
        mask-image: linear-gradient(to left, rgba(0,0,0,1) 0%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0) 100%);
    }
    @media (max-width: 1024px) {
        .stApp::before, .stApp::after { display: none; }
    }

    .block-container {
        position: relative;
        z-index: 1;
        padding-top: 0.5rem !important;
    }

    /* ── K · O · D · A title ──────────────────── */
    .koda-title {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 4rem;
        font-weight: 700;
        letter-spacing: 0.22em;
        text-align: center;
        color: rgba(125, 122, 201, 1);
        margin: 0.3rem 0 0.15rem 0;
        line-height: 1;
    }
    .koda-tagline {
        text-align: center;
        font-family: 'Nunito', sans-serif;
        font-size: 1rem;
        color: #636e72;
        margin: 0 0 0.15rem 0;
        font-weight: 400;
        font-style: italic;
    }
    .koda-heritage {
        text-align: center;
        font-family: 'Nunito', sans-serif;
        font-size: 0.72rem;
        color: #b2bec3;
        margin: 0 0 1rem 0;
        letter-spacing: 0.04em;
    }

    /* ── Stat boxes ───────────────────────────── */
    .stat-box {
        background: rgba(222, 176, 215, 0.25);
        border: 1px solid rgba(222, 176, 215, 0.5);
        border-radius: 16px;
        padding: 1.2rem 1rem;
        text-align: center;
        margin: 0.3rem 0;
    }
    .stat-label {
        font-family: 'Nunito', sans-serif;
        font-size: 0.78rem;
        color: #636e72;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
    }
    .stat-value {
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }
    .stat-value.low { color: #d63031; }
    .stat-value.high { color: #00b894; }
    .stat-delta {
        font-family: 'Nunito', sans-serif;
        font-size: 0.8rem;
        color: #636e72;
    }

    /* ── Chat input bar — light mode ─────────── */
    .stBottom, .stBottom > div, .stBottom > div > div {
        background: transparent !important;
    }
    .stChatInput {
        background: transparent !important;
    }
    .stChatInput > div {
        background: #f0ebe4 !important;
        border: 2px solid rgba(125, 122, 201, 0.25) !important;
        border-radius: 24px !important;
    }
    .stChatInput textarea {
        background: #f0ebe4 !important;
        background-color: #f0ebe4 !important;
        color: #2d3436 !important;
        padding: 0.5rem !important;
        caret-color: rgba(125, 122, 201, 1) !important;
        -webkit-text-fill-color: #2d3436 !important;
    }
    .stChatInput textarea:focus {
        background: #f0ebe4 !important;
        background-color: #f0ebe4 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .stChatInput textarea::selection {
        background: rgba(125, 122, 201, 0.25) !important;
        color: #2d3436 !important;
    }
    .stChatInput > div > div {
        background: transparent !important;
    }
    /* Send button — subtle when empty, purple when ready */
    .stChatInput button {
        border-radius: 50% !important;
        border: none !important;
        transition: all 0.2s !important;
    }
    .stChatInput button[disabled] {
        background: #ddd !important;
        opacity: 0.4 !important;
    }
    .stChatInput button:not([disabled]) {
        background: rgba(125, 122, 201, 1) !important;
        color: white !important;
        box-shadow: 0 2px 6px rgba(125, 122, 201, 0.4) !important;
    }
    .stChatInput button:not([disabled]):hover {
        background: rgba(105, 102, 181, 1) !important;
        box-shadow: 0 3px 10px rgba(125, 122, 201, 0.5) !important;
    }
    .stChatInput button svg {
        fill: currentColor !important;
        stroke: currentColor !important;
        width: 20px !important;
        height: 20px !important;
    }
    .stChatInput button > div {
        background: none !important;
        border: none !important;
    }

    /* ── Chat bubbles — light mode ────────────── */
    /* User messages: right-aligned purple bubble */
    .msg-user {
        background: rgba(125, 122, 201, 1);
        color: white;
        padding: 0.8rem 1.1rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0.4rem 0 0.4rem 4rem;
        line-height: 1.6;
        font-size: 0.9rem;
    }

    /* KODA messages: native st.chat_message styled to warm-white theme */
    [data-testid="stChatMessage"] {
        background: #ffffff;
        border: 1px solid #e8e4df;
        border-radius: 16px 16px 16px 4px;
        padding: 0.8rem 1.1rem;
        margin: 0.4rem 4rem 0.4rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        color: #2d3436;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    /* Agent label badge */
    [data-testid="stChatMessage"] small {
        font-size: 0.7rem !important;
        color: rgba(125, 122, 201, 0.8) !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }
    /* Hide default Streamlit avatar — we use the title emoji instead */
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
        display: none;
    }

    /* Legacy class kept for backward-compat with any static references */
    .msg-koda {
        background: white; color: #2d3436; border: 1px solid #e8e4df;
        padding: 0.8rem 1.1rem; border-radius: 16px 16px 16px 4px;
        margin: 0.4rem 4rem 0.4rem 0; line-height: 1.6; font-size: 0.9rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .msg-koda .badge {
        font-size: 0.7rem; color: rgba(125, 122, 201, 0.8); font-weight: 700;
        letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem;
    }

    /* ── Quick-action section header ────────────── */
    .qa-header {
        text-align: center;
        margin: 0.6rem 0 0.9rem 0;
    }
    .qa-header-title {
        font-family: 'Nunito', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: rgba(125, 122, 201, 1);
        letter-spacing: 0.01em;
        margin: 0 0 0.2rem 0;
    }
    .qa-header-sub {
        font-family: 'Nunito', sans-serif;
        font-size: 0.78rem;
        color: #636e72;
        margin: 0;
    }

    /* ── Quick action pill-card buttons ──────────── */
    [data-testid="baseButton-secondary"] {
        border-radius: 22px !important;
        border: 1.5px solid rgba(125, 122, 201, 0.32) !important;
        background: rgba(125, 122, 201, 0.05) !important;
        color: #2d3436 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.42rem 0.75rem !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease,
                    border-color 0.15s ease, background 0.15s ease !important;
        letter-spacing: 0.01em !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    [data-testid="baseButton-secondary"]:hover {
        border-color: rgba(125, 122, 201, 0.72) !important;
        background: rgba(125, 122, 201, 0.13) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(125, 122, 201, 0.22) !important;
    }
    [data-testid="baseButton-secondary"]:active {
        transform: translateY(0px) !important;
        box-shadow: none !important;
    }

    /* ── Reset button — ghost pill, right-of-input ─ */
    [data-testid="baseButton-primary"] {
        border-radius: 20px !important;
        border: 1.5px solid rgba(125, 122, 201, 0.45) !important;
        background: transparent !important;
        color: rgba(125, 122, 201, 0.9) !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        padding: 0.3rem 0.85rem !important;
        transition: all 0.15s ease !important;
        letter-spacing: 0.01em !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background: rgba(125, 122, 201, 0.1) !important;
        border-color: rgba(125, 122, 201, 0.8) !important;
        box-shadow: 0 2px 8px rgba(125, 122, 201, 0.25) !important;
    }

    /* ════════════════════════════════════════════
       DARK MODE  (respects OS / browser setting)
       All hardcoded light-mode colours are
       overridden here.  Purple accent (#7d7ac9)
       is kept so the brand identity is consistent.
       ════════════════════════════════════════════ */
    @media (prefers-color-scheme: dark) {

        /* ── App background ───────────────────── */
        .stApp {
            background-color: #1a1a2e !important;
        }

        /* ── Text colours ─────────────────────── */
        .koda-tagline {
            color: #a0a8b8 !important;
        }
        .koda-heritage {
            color: #5a6070 !important;
        }

        /* ── Stat boxes ───────────────────────── */
        .stat-box {
            background: rgba(125, 122, 201, 0.12) !important;
            border-color: rgba(125, 122, 201, 0.3) !important;
        }
        .stat-label {
            color: #a0a8b8 !important;
        }
        .stat-delta {
            color: #a0a8b8 !important;
        }

        /* ── Welcome body & footer text ───────── */
        p[style*="color:#636e72"] {
            color: #a0a8b8 !important;
        }

        /* ── User bubble (stays purple — readable on dark) */
        .msg-user {
            background: rgba(125, 122, 201, 0.85) !important;
            color: #ffffff !important;
        }

        /* ── KODA assistant bubble ────────────── */
        [data-testid="stChatMessage"] {
            background: #252540 !important;
            border-color: rgba(125, 122, 201, 0.2) !important;
            color: #e8e4f0 !important;
            box-shadow: 0 1px 6px rgba(0,0,0,0.3) !important;
        }
        /* Ensure all text inside the bubble is light */
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] code {
            color: #e8e4f0 !important;
        }
        /* Inline code blocks */
        [data-testid="stChatMessage"] code {
            background: rgba(125, 122, 201, 0.15) !important;
            border-radius: 4px;
            padding: 0.1em 0.35em;
        }
        /* Agent label keeps the purple accent */
        [data-testid="stChatMessage"] small {
            color: rgba(160, 155, 220, 0.9) !important;
        }

        /* Legacy bubble */
        .msg-koda {
            background: #252540 !important;
            color: #e8e4f0 !important;
            border-color: rgba(125, 122, 201, 0.2) !important;
        }

        /* ── Chat input ──────────────────────── */
        .stChatInput > div {
            background: #252540 !important;
            border-color: rgba(125, 122, 201, 0.35) !important;
        }
        .stChatInput textarea {
            background: #252540 !important;
            background-color: #252540 !important;
            color: #e8e4f0 !important;
            -webkit-text-fill-color: #e8e4f0 !important;
            caret-color: rgba(160, 155, 220, 1) !important;
        }
        .stChatInput textarea:focus {
            background: #252540 !important;
            background-color: #252540 !important;
        }
        .stChatInput button[disabled] {
            background: #3a3a5c !important;
        }

        /* ── Quick-action section header ───────── */
        .qa-header-title {
            color: rgba(160, 155, 220, 1) !important;
        }
        .qa-header-sub {
            color: #6a7280 !important;
        }

        /* ── Quick action pill-card buttons ──────── */
        [data-testid="baseButton-secondary"] {
            border-color: rgba(125, 122, 201, 0.4) !important;
            background: rgba(125, 122, 201, 0.07) !important;
            color: #c8c4e8 !important;
        }
        [data-testid="baseButton-secondary"]:hover {
            border-color: rgba(160, 155, 220, 0.8) !important;
            background: rgba(125, 122, 201, 0.22) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.35) !important;
        }

        /* ── Reset button dark mode ───────────────── */
        [data-testid="baseButton-primary"] {
            border-color: rgba(125, 122, 201, 0.5) !important;
            color: rgba(160, 155, 220, 0.9) !important;
        }
        [data-testid="baseButton-primary"]:hover {
            background: rgba(125, 122, 201, 0.18) !important;
            border-color: rgba(160, 155, 220, 0.85) !important;
        }

        /* ── Divider ─────────────────────────── */
        hr {
            border-color: rgba(125, 122, 201, 0.15) !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── Language toggle ───────────


def _set_lang(new_lang: str):
    st.session_state.lang = new_lang


def _reset_chat() -> None:
    """
    Clear all conversation state and return to the welcome screen.

    Resets messages, session ID, and welcome flag.  A new session ID is
    generated so any server-side session store would treat this as a fresh
    session.  The language preference is intentionally preserved — the user
    should not have to re-select it after resetting.

    Privacy note: no persistent storage exists, so "reset" is purely
    in-memory.  Compliant with the ephemeral-session guarantee in the footer.
    """
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.show_welcome = True
    # Clear any pending quick-action message
    st.session_state.pop("_pending_msg", None)


# ── Language toggle ─────────────────────────────────────
st.pills(
    label="Language",
    options=["🇩🇪 Deutsch", "🇬🇧 English"],
    default="🇩🇪 Deutsch" if lang == "de" else "🇬🇧 English",
    on_change=lambda: _set_lang("de" if st.session_state._lang_pills == "🇩🇪 Deutsch" else "en"),
    key="_lang_pills",
    label_visibility="collapsed",
)
# Apply the language if changed via pills
if "_lang_pills" in st.session_state:
    new = "de" if st.session_state._lang_pills == "🇩🇪 Deutsch" else "en"
    if new != lang:
        st.session_state.lang = new
        st.rerun()


# ── Agent loader ───────────────────────────────────────


@st.cache_resource
def load_agents():
    """Initialize agents once and cache them."""
    from src.agents.academic_basics.hidden_curriculum import HiddenCurriculumAgent
    from src.agents.compass import CompassAgent
    from src.agents.crisis import CrisisRadar
    from src.agents.financing.student_aid import StudentAidAgent
    from src.agents.role_models.anti_impostor import AntiImpostorAgent
    from src.agents.router import RouterAgent
    from src.agents.study_choice.degree_explorer import DegreeExplorerAgent

    return {
        "router": RouterAgent(),
        "crisis": CrisisRadar(),
        "agents": {
            "COMPASS": CompassAgent(),
            "FINANCING": StudentAidAgent(),
            "STUDY_CHOICE": DegreeExplorerAgent(),
            "ACADEMIC_BASICS": HiddenCurriculumAgent(),
            "ROLE_MODELS": AntiImpostorAgent(),
        },
    }


def get_response(user_message: str, history: list, ui_lang: str = "de") -> dict:
    """
    Orchestrate agent routing, crisis scanning and response generation.

    Args:
        user_message: The raw text submitted by the user.
        history: Previous Bedrock-formatted message turns.
        ui_lang: The UI language chosen by the user (used for the
                 crisis banner only; agent responses auto-detect language).

    Returns:
        dict with keys: ``response`` (str), ``agent`` (str), ``crisis`` (bool).
    """
    system = load_agents()
    bedrock_messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in history]
    bedrock_messages.append({"role": "user", "content": [{"text": user_message}]})

    crisis = system["crisis"].scan(user_message)
    agent_key = system["router"].route(user_message)
    agent = system["agents"].get(agent_key, system["agents"]["COMPASS"])
    response_text = agent.respond(bedrock_messages)

    if crisis["is_crisis"] and crisis["resources"]:
        # Crisis banner uses the UI language; agent body already auto-detected
        prefix = t("crisis_banner", ui_lang) + "\n"
        for v in crisis["resources"].values():
            prefix += f"\u2022 {v}\n"
        response_text = prefix + "\n" + response_text

    return {"response": response_text, "agent": agent_key, "crisis": crisis["is_crisis"]}


def get_response_stream(user_message: str, history: list, ui_lang: str = "de"):
    """
    Streaming variant of get_response().

    Yields text chunks from the agent's token stream so the caller can
    render them progressively (e.g. via ``st.write_stream()``).

    The *last* item yielded is always a sentinel dict::

        {"agent": str, "crisis": bool, "response": str}

    containing the fully assembled response and routing metadata.
    Callers must pop this final dict before displaying.
    """
    system = load_agents()
    bedrock_messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in history]
    bedrock_messages.append({"role": "user", "content": [{"text": user_message}]})

    crisis = system["crisis"].scan(user_message)
    agent_key = system["router"].route(user_message)
    agent = system["agents"].get(agent_key, system["agents"]["COMPASS"])

    # If crisis, prepend the banner as the very first streamed chunk
    crisis_prefix = ""
    if crisis["is_crisis"] and crisis["resources"]:
        crisis_prefix = t("crisis_banner", ui_lang) + "\n"
        for v in crisis["resources"].values():
            crisis_prefix += f"\u2022 {v}\n"
        crisis_prefix += "\n"
        yield crisis_prefix

    collected: list[str] = [crisis_prefix]
    replace_text: str | None = None

    for chunk in agent.respond_stream(bedrock_messages):
        if chunk.startswith("\x00REPLACE\x00"):
            # Anti-shame filter rewrote the text; store corrected version
            replace_text = crisis_prefix + chunk[len("\x00REPLACE\x00") :]
        else:
            collected.append(chunk)
            yield chunk

    full_response = replace_text if replace_text is not None else "".join(collected)

    # Final sentinel — caller must consume and not display this
    yield {"response": full_response, "agent": agent_key, "crisis": crisis["is_crisis"]}


def _safe_user(text: str) -> str:
    """Escape HTML for user-supplied bubble text (plain text, no markdown)."""
    return html_lib.escape(text)


def _send(msg_key: str):
    st.session_state._pending_msg = t(msg_key, lang)
    st.session_state.show_welcome = False


def _render_quick_actions(current_lang: str) -> None:
    """
    Render the six quick-action suggestion buttons.

    Extracted into a named function so the buttons can be displayed
    persistently below the chat history — not only on the welcome screen.
    Each button pre-fills the chat input with a full question so the user
    never has to type for common topics.

    Args:
        current_lang: Active UI language code ("de" or "en").
    """
    heading = t("quick_actions_heading", current_lang)
    sub = t("quick_actions_sub", current_lang)
    st.markdown(
        f'<div class="qa-header">'
        f'<div class="qa-header-title">{heading}</div>'
        f'<div class="qa-header-sub">{sub}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(t("quick_bafoeg", current_lang), use_container_width=True, key="qa_bafoeg"):
            _send("quick_bafoeg_msg")
    with c2:
        if st.button(t("quick_study", current_lang), use_container_width=True, key="qa_study"):
            _send("quick_study_msg")
    with c3:
        if st.button(
            t("quick_overwhelmed", current_lang), use_container_width=True, key="qa_overwhelmed"
        ):
            _send("quick_overwhelmed_msg")

    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button(t("quick_ects", current_lang), use_container_width=True, key="qa_ects"):
            _send("quick_ects_msg")
    with c5:
        if st.button(
            t("quick_scholarships", current_lang),
            use_container_width=True,
            key="qa_scholarships",
        ):
            _send("quick_scholarships_msg")
    with c6:
        if st.button(
            t("quick_rolemodels", current_lang), use_container_width=True, key="qa_rolemodels"
        ):
            _send("quick_rolemodels_msg")


# ── Title: KODA ──────────────────────────────

dot = chr(183)
if lang == "de":
    heritage_text = f"Japanisch: \u201ehier, an diesem Punkt\u201c {dot} Dakota Sioux: \u201eFreund, Verb\u00fcndeter\u201c"
else:
    heritage_text = (
        f"Japanese: \u2018here, at this point\u2019 {dot} Dakota Sioux: \u2018friend, ally\u2019"
    )

st.markdown(
    """<div class="koda-title">K\u2009\u00b7\u2009O\u2009\u00b7\u2009D\u2009\u00b7\u2009A</div>""",
    unsafe_allow_html=True,
)
st.markdown(f"""<div class="koda-tagline">{t("subtitle", lang)}</div>""", unsafe_allow_html=True)
st.markdown(f"""<div class="koda-heritage">{heritage_text}</div>""", unsafe_allow_html=True)


# ── Welcome screen ─────────────────────────────────────

if st.session_state.show_welcome and not st.session_state.messages:
    col_left, col_right = st.columns(2)

    with col_left:
        if lang == "de":
            st.markdown(
                """
            <div class="stat-box">
                <div class="stat-label">Nicht-Akademikerkinder</div>
                <div class="stat-value low">27 von 100</div>
                <div class="stat-delta">beginnen ein Studium</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="stat-box">
                <div class="stat-label">Non-academic families</div>
                <div class="stat-value low">27 of 100</div>
                <div class="stat-delta">start university</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col_right:
        if lang == "de":
            st.markdown(
                """
            <div class="stat-box">
                <div class="stat-label">Akademikerkinder</div>
                <div class="stat-value high">79 von 100</div>
                <div class="stat-delta">beginnen ein Studium</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class="stat-box">
                <div class="stat-label">Academic families</div>
                <div class="stat-value high">79 of 100</div>
                <div class="stat-delta">start university</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.write("")

    welcome_text = t("welcome_body", lang).replace(
        "\n\n",
        '</p><p style="text-align:center; color:#636e72; font-size:0.93rem; line-height:1.7; margin:0.5rem 0 0 0;">',
    )
    st.markdown(
        f"<p style='text-align:center; color:#636e72; font-size:0.93rem; line-height:1.7; margin:0;'>{welcome_text}</p>",
        unsafe_allow_html=True,
    )

    st.write("")


# ── Chat history ───────────────────────────────────────

for msg in st.session_state.messages:
    if msg["role"] == "user":
        # User text is plain — escape HTML to prevent XSS injection
        st.markdown(
            f'<div class="msg-user">{_safe_user(msg["content"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        # Agent response: use Streamlit's native chat_message so that
        # st.markdown() inside it renders all markdown formatting correctly
        # (headers, bold, lists, code blocks, etc.)
        label = get_agent_label(msg.get("agent", "COMPASS"), lang)
        with st.chat_message("assistant", avatar="🧭"):
            st.caption(label)
            st.markdown(msg["content"])


# ── Quick actions (persistent) ─────────────────────────
# Rendered after every chat turn so users can always select a topic
# without typing.  Unique widget keys prevent Streamlit duplicate-key
# errors across re-renders.
_render_quick_actions(lang)


# ── Reset button — sits right above the chat input ────────
# Only shown once the user has started a conversation.
if st.session_state.messages:
    _space_col, _reset_col = st.columns([6, 2])
    with _reset_col:
        if st.button(
            t("reset_chat", lang),
            help=t("reset_chat_tooltip", lang),
            key="_reset_btn",
            type="primary",
            use_container_width=True,
        ):
            _reset_chat()
            st.rerun()

# ── Input handling ─────────────────────────────────────

user_input = None
if "_pending_msg" in st.session_state:
    user_input = st.session_state._pending_msg
    del st.session_state._pending_msg

chat_input = st.chat_input(t("input_placeholder", lang))
if chat_input:
    user_input = chat_input
    st.session_state.show_welcome = False

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(
        f'<div class="msg-user">{_safe_user(user_input)}</div>',
        unsafe_allow_html=True,
    )

    # ── Streaming response ─────────────────────────────────
    # Route + scan crisis first (fast, non-streaming), then stream agent tokens.
    # st.write_stream() renders each yielded chunk as it arrives.
    # The final yielded item is a metadata dict — we pop it before display.
    stream = get_response_stream(user_input, st.session_state.messages[:-1], ui_lang=lang)

    label_placeholder = None
    # Use a single-element list so the nested generator can write to it
    # without a nonlocal that ruff flags as "assigned but never used".
    meta_box: list[dict] = [{}]

    def _filtered_stream():
        """Yield only string chunks to st.write_stream; capture the final dict."""
        for item in stream:
            if isinstance(item, dict):
                meta_box[0] = item
            else:
                yield item

    with st.chat_message("assistant", avatar="\U0001f9ed"):
        label_placeholder = st.empty()
        full_text = st.write_stream(_filtered_stream())

    metadata = meta_box[0]
    agent_label = get_agent_label(metadata.get("agent", "COMPASS"), lang)
    if label_placeholder:
        label_placeholder.caption(agent_label)

    # Use metadata response if anti-shame filter replaced the streamed text
    final_text = metadata.get("response", full_text)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_text,
            "agent": metadata.get("agent", "COMPASS"),
        }
    )


# ── Footer ─────────────────────────────────────────────

st.divider()
footer_text = t("footer", lang)
footer_html = footer_text.replace(
    "\n\n",
    '</p><p style="text-align:center; color:#636e72; font-size:0.85rem; line-height:1.6; margin:0;">',
)
st.markdown(
    f"<p style='text-align:center; color:#636e72; font-size:0.85rem; line-height:1.6; margin:0;'>"
    f"{footer_html}</p>",
    unsafe_allow_html=True,
)
