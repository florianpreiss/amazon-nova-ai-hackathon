"""
KODA — Streamlit Chat Interface.
"""

import html as html_lib
import uuid

import streamlit as st
from src.i18n import DEFAULT_LANGUAGE, get_agent_label, t

# ── Page config ────────────────────────────────────────

st.set_page_config(
    page_title="KODA — Your AI Companion for University Orientation",
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

# ── Custom CSS — warm, approachable, ArbeiterKind-inspired ──

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Nunito+Sans:ital,opsz,wght@0,6..12,300;0,6..12,400;0,6..12,500;0,6..12,600;0,6..12,700;1,6..12,400&display=swap');

    :root {
        --koda-green: #1a8a6e;
        --koda-green-light: #e8f5f0;
        --koda-green-dark: #146b55;
        --koda-orange: #e8853a;
        --koda-orange-light: #fef3e8;
        --koda-cream: #faf8f5;
        --koda-warm-gray: #f5f2ee;
        --koda-text: #2d3436;
        --koda-text-light: #636e72;
        --koda-white: #ffffff;
        --koda-border: #e8e4df;
        --font-display: 'Source Serif 4', Georgia, serif;
        --font-body: 'Nunito Sans', -apple-system, sans-serif;
    }

    /* Global — warm cream background */
    .stApp {
        background: var(--koda-cream) !important;
    }
    .block-container {
        max-width: 760px;
        padding-top: 1rem !important;
        padding-bottom: 2rem;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Language toggle ──────────────────────── */
    .lang-toggle {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 0;
        padding: 0.5rem 0;
    }
    .lang-btn {
        font-family: var(--font-body);
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.4rem 0.8rem;
        border: 2px solid var(--koda-border);
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        color: var(--koda-text-light);
        background: var(--koda-white);
    }
    .lang-btn:first-child { border-radius: 20px 0 0 20px; border-right: 1px solid var(--koda-border); }
    .lang-btn:last-child { border-radius: 0 20px 20px 0; border-left: 1px solid var(--koda-border); }
    .lang-btn.active {
        background: var(--koda-green);
        color: white;
        border-color: var(--koda-green);
    }

    /* ── Header ───────────────────────────────── */
    .koda-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .koda-logo {
        font-family: var(--font-display);
        font-size: 3rem;
        font-weight: 700;
        color: var(--koda-green);
        letter-spacing: 0.08em;
        margin: 0;
    }
    .koda-tagline {
        font-family: var(--font-body);
        font-size: 1rem;
        color: var(--koda-text-light);
        margin-top: 0.2rem;
        font-weight: 400;
    }

    /* ── Stats cards ──────────────────────────── */
    .stats-container {
        display: flex;
        gap: 1.2rem;
        justify-content: center;
        margin: 1.5rem 0;
    }
    .stat-card {
        flex: 1;
        max-width: 240px;
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        transition: transform 0.2s;
    }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-card.green {
        background: var(--koda-green-light);
        border: 2px solid rgba(26, 138, 110, 0.15);
    }
    .stat-card.orange {
        background: var(--koda-orange-light);
        border: 2px solid rgba(232, 133, 58, 0.15);
    }
    .stat-number {
        font-family: var(--font-display);
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.4rem;
    }
    .stat-card.green .stat-number { color: var(--koda-green); }
    .stat-card.orange .stat-number { color: var(--koda-orange); }
    .stat-label {
        font-family: var(--font-body);
        font-size: 0.8rem;
        color: var(--koda-text-light);
        line-height: 1.4;
    }

    /* ── Welcome card ─────────────────────────── */
    .welcome-text {
        text-align: center;
        font-family: var(--font-body);
        font-size: 0.95rem;
        color: var(--koda-text-light);
        line-height: 1.7;
        max-width: 520px;
        margin: 0.5rem auto 1.5rem auto;
    }

    /* ── Quick action buttons ─────────────────── */
    .stButton > button {
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: 2px solid var(--koda-border) !important;
        background: var(--koda-white) !important;
        color: var(--koda-text) !important;
        padding: 0.6rem 0.5rem !important;
        transition: all 0.2s !important;
        font-size: 0.82rem !important;
    }
    .stButton > button:hover {
        border-color: var(--koda-green) !important;
        background: var(--koda-green-light) !important;
        color: var(--koda-green-dark) !important;
        transform: translateY(-1px);
    }

    /* ── Chat messages ────────────────────────── */
    .chat-msg {
        font-family: var(--font-body);
        padding: 1rem 1.2rem;
        border-radius: 16px;
        margin: 0.6rem 0;
        line-height: 1.7;
        font-size: 0.9rem;
        animation: fadeIn 0.3s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .msg-user {
        background: var(--koda-green);
        color: white;
        margin-left: 3rem;
        border-bottom-right-radius: 4px;
    }
    .msg-koda {
        background: var(--koda-white);
        color: var(--koda-text);
        margin-right: 3rem;
        border: 1px solid var(--koda-border);
        border-bottom-left-radius: 4px;
    }
    .agent-badge {
        font-size: 0.7rem;
        color: var(--koda-orange);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
        font-family: var(--font-body);
    }

    /* ── Footer ───────────────────────────────── */
    .koda-footer {
        text-align: center;
        margin-top: 2rem;
        padding: 1.5rem;
        border-top: 1px solid var(--koda-border);
    }
    .koda-footer p {
        font-family: var(--font-body);
        font-size: 0.75rem;
        color: var(--koda-text-light);
        margin: 0;
    }

    /* ── Chat input styling ───────────────────── */
    .stChatInput {
        position: relative;
    }
    .stChatInput textarea {
        font-family: var(--font-body) !important;
        border-radius: 16px !important;
        border: 2px solid var(--koda-border) !important;
        background: var(--koda-white) !important;
    }
    .stChatInput textarea:focus {
        border-color: var(--koda-green) !important;
        box-shadow: 0 0 0 3px rgba(26, 138, 110, 0.1) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

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


def get_response(user_message: str, history: list) -> dict:
    """Call agents directly."""
    system = load_agents()
    bedrock_messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in history]
    bedrock_messages.append({"role": "user", "content": [{"text": user_message}]})

    crisis = system["crisis"].scan(user_message)
    agent_key = system["router"].route(user_message)
    agent = system["agents"].get(agent_key, system["agents"]["COMPASS"])
    response_text = agent.respond(bedrock_messages)

    if crisis["is_crisis"] and crisis["resources"]:
        prefix = t("crisis_banner", lang) + "\n"
        for v in crisis["resources"].values():
            prefix += f"• {v}\n"
        response_text = prefix + "\n" + response_text

    return {"response": response_text, "agent": agent_key, "crisis": crisis["is_crisis"]}


def _send(key: str):
    st.session_state._pending_msg = t(key, lang)
    st.session_state.show_welcome = False


def _safe(text: str) -> str:
    """Escape HTML to prevent XSS, then convert newlines to <br>."""
    return html_lib.escape(text).replace("\n", "<br>")


# ── Language toggle (flag-based, intuitive) ────────────

st.markdown(
    f"""
<div class="lang-toggle">
    <span class="lang-btn {"active" if lang == "de" else ""}"
          id="lang-de">🇩🇪 Deutsch</span>
    <span class="lang-btn {"active" if lang == "en" else ""}"
          id="lang-en">🇬🇧 English</span>
</div>
""",
    unsafe_allow_html=True,
)

# Streamlit button workaround for the toggle
col_spacer, col_de, col_en = st.columns([6, 1, 1])
with col_de:
    if st.button("🇩🇪", key="btn_de", help="Deutsch"):
        st.session_state.lang = "de"
        st.rerun()
with col_en:
    if st.button("🇬🇧", key="btn_en", help="English"):
        st.session_state.lang = "en"
        st.rerun()

# ── Header ─────────────────────────────────────────────

st.markdown(
    f"""
<div class="koda-header">
    <h1 class="koda-logo">KODA</h1>
    <p class="koda-tagline">{t("subtitle", lang)}</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Welcome screen ─────────────────────────────────────

if st.session_state.show_welcome and not st.session_state.messages:
    # Stats cards
    st.markdown(
        f"""
    <div class="stats-container">
        <div class="stat-card orange">
            <div class="stat-number">27</div>
            <div class="stat-label">{t("stat_left_label", lang).replace(chr(10), "<br>")}</div>
        </div>
        <div class="stat-card green">
            <div class="stat-number">79</div>
            <div class="stat-label">{t("stat_right_label", lang).replace(chr(10), "<br>")}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Welcome text
    st.markdown(
        f"""
    <p class="welcome-text">{t("welcome_body", lang).replace(chr(10), "<br>")}</p>
    """,
        unsafe_allow_html=True,
    )

    # Quick action buttons
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(t("quick_bafoeg", lang), use_container_width=True):
            _send("quick_bafoeg_msg")
    with c2:
        if st.button(t("quick_study", lang), use_container_width=True):
            _send("quick_study_msg")
    with c3:
        if st.button(t("quick_overwhelmed", lang), use_container_width=True):
            _send("quick_overwhelmed_msg")

    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button(t("quick_ects", lang), use_container_width=True):
            _send("quick_ects_msg")
    with c5:
        if st.button(t("quick_scholarships", lang), use_container_width=True):
            _send("quick_scholarships_msg")
    with c6:
        if st.button(t("quick_rolemodels", lang), use_container_width=True):
            _send("quick_rolemodels_msg")

# ── Chat history ───────────────────────────────────────

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-msg msg-user">{_safe(msg["content"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        label = get_agent_label(msg.get("agent", "COMPASS"), lang)
        st.markdown(
            f'<div class="chat-msg msg-koda">'
            f'<div class="agent-badge">{label}</div>'
            f"{_safe(msg['content'])}"
            f"</div>",
            unsafe_allow_html=True,
        )

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
        f'<div class="chat-msg msg-user">{_safe(user_input)}</div>',
        unsafe_allow_html=True,
    )

    with st.spinner(t("thinking", lang)):
        result = get_response(user_input, st.session_state.messages[:-1])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["response"],
            "agent": result["agent"],
        }
    )
    st.rerun()

# ── Footer ─────────────────────────────────────────────

st.markdown(
    f"""
<div class="koda-footer">
    <p>{t("footer", lang)}</p>
</div>
""",
    unsafe_allow_html=True,
)
