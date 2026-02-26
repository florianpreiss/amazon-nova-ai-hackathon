"""
KODA — Streamlit Chat Interface.

A warm, welcoming chat UI for first-generation academics.
Supports German/English toggle. Agents respond in user's language automatically.
"""

import uuid

import streamlit as st
from src.i18n import DEFAULT_LANGUAGE, get_agent_label, t

# ── Page config ────────────────────────────────────────

st.set_page_config(
    page_title="KODA — Your Academic Companion",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,700;1,9..144,400&display=swap');

    .stApp {
        background: linear-gradient(175deg, #0a0f1a 0%, #111827 50%, #0d1520 100%);
    }
    .block-container { max-width: 720px; padding-top: 2rem; }

    .koda-header { text-align: center; padding: 2rem 0 1rem 0; }
    .koda-title {
        font-family: 'Fraunces', serif;
        font-size: 3.2rem; font-weight: 300; letter-spacing: 0.15em;
        background: linear-gradient(135deg, #ffffff 0%, #0d9488 60%, #d97706 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .koda-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem; color: #6b8090; margin-top: 0.3rem; font-style: italic;
    }
    .koda-divider {
        width: 60px; height: 2px;
        background: linear-gradient(90deg, #0d9488, #d97706);
        margin: 1rem auto; border-radius: 2px;
    }

    .chat-msg {
        font-family: 'DM Sans', sans-serif;
        padding: 1rem 1.2rem; border-radius: 16px;
        margin: 0.5rem 0; line-height: 1.65; font-size: 0.92rem;
    }
    .msg-user {
        background: rgba(13, 148, 136, 0.12);
        border: 1px solid rgba(13, 148, 136, 0.2);
        color: #d1e8e5; margin-left: 2rem;
    }
    .msg-koda {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        color: #c8d0d8; margin-right: 2rem;
    }
    .msg-koda .agent-badge {
        font-size: 0.7rem; color: #d97706; font-weight: 500;
        letter-spacing: 0.08em; text-transform: uppercase;
        margin-bottom: 0.4rem; font-family: 'DM Sans', sans-serif;
    }

    .welcome-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px; padding: 1.5rem; margin: 1rem 0; text-align: center;
    }
    .welcome-card p {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.88rem; color: #8a9aaa; line-height: 1.7;
    }
    .stats-row { display: flex; justify-content: center; gap: 2rem; margin: 1rem 0; }
    .stat-item { text-align: center; }
    .stat-number {
        font-family: 'Fraunces', serif; font-size: 1.6rem;
        font-weight: 300; color: #0d9488;
    }
    .stat-label {
        font-family: 'DM Sans', sans-serif; font-size: 0.7rem;
        color: #6b8090; margin-top: 0.2rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
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

# Shorthand for current language
lang = st.session_state.lang

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
    """Call agents directly (no FastAPI backend needed)."""
    system = load_agents()

    # Build Bedrock message history
    bedrock_messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in history]
    bedrock_messages.append({"role": "user", "content": [{"text": user_message}]})

    # Crisis scan
    crisis = system["crisis"].scan(user_message)

    # Route to agent
    agent_key = system["router"].route(user_message)
    agent = system["agents"].get(agent_key, system["agents"]["COMPASS"])

    # Get response
    response_text = agent.respond(bedrock_messages)

    # Prepend crisis resources if triggered
    if crisis["is_crisis"] and crisis["resources"]:
        prefix = t("crisis_banner", lang) + "\n"
        for v in crisis["resources"].values():
            prefix += f"• {v}\n"
        response_text = prefix + "\n" + response_text

    return {"response": response_text, "agent": agent_key, "crisis": crisis["is_crisis"]}


# ── Helper ─────────────────────────────────────────────


def _send_quick_message(key: str):
    """Queue a quick-action message for processing."""
    st.session_state._pending_msg = t(key, lang)
    st.session_state.show_welcome = False


# ── Header + language toggle ───────────────────────────

col_title, col_lang = st.columns([5, 1])

with col_title:
    st.markdown(
        f"""
    <div class="koda-header">
        <h1 class="koda-title">{t("title", lang)}</h1>
        <p class="koda-subtitle">{t("subtitle", lang)}</p>
        <div class="koda-divider"></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col_lang:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button(t("lang_toggle", lang), key="lang_btn"):
        st.session_state.lang = "de" if lang == "en" else "en"
        st.rerun()

# ── Welcome screen ─────────────────────────────────────

if st.session_state.show_welcome and not st.session_state.messages:
    st.markdown(
        f"""
    <div class="welcome-card">
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-number">{t("stat_left_number", lang)}</div>
                <div class="stat-label">{t("stat_left_label", lang)}</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{t("stat_right_number", lang)}</div>
                <div class="stat-label">{t("stat_right_label", lang)}</div>
            </div>
        </div>
        <p style="margin-top: 1rem;">{t("welcome_body", lang)}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Quick action buttons — row 1
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(t("quick_bafoeg", lang), use_container_width=True):
            _send_quick_message("quick_bafoeg_msg")
    with c2:
        if st.button(t("quick_study", lang), use_container_width=True):
            _send_quick_message("quick_study_msg")
    with c3:
        if st.button(t("quick_overwhelmed", lang), use_container_width=True):
            _send_quick_message("quick_overwhelmed_msg")

    # Quick action buttons — row 2
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button(t("quick_ects", lang), use_container_width=True):
            _send_quick_message("quick_ects_msg")
    with c5:
        if st.button(t("quick_scholarships", lang), use_container_width=True):
            _send_quick_message("quick_scholarships_msg")
    with c6:
        if st.button(t("quick_rolemodels", lang), use_container_width=True):
            _send_quick_message("quick_rolemodels_msg")

# ── Chat history ───────────────────────────────────────

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-msg msg-user">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        label = get_agent_label(msg.get("agent", "COMPASS"), lang)
        st.markdown(
            f'<div class="chat-msg msg-koda">'
            f'<div class="agent-badge">{label}</div>'
            f"{msg['content']}"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Input handling ─────────────────────────────────────

user_input = None

# Check for quick-action button press
if "_pending_msg" in st.session_state:
    user_input = st.session_state._pending_msg
    del st.session_state._pending_msg

# Chat input box
chat_input = st.chat_input(t("input_placeholder", lang))
if chat_input:
    user_input = chat_input
    st.session_state.show_welcome = False

# Process input
if user_input:
    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(
        f'<div class="chat-msg msg-user">{user_input}</div>',
        unsafe_allow_html=True,
    )

    # Get agent response
    with st.spinner(t("thinking", lang)):
        result = get_response(user_input, st.session_state.messages[:-1])

    # Store assistant message
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
<div style="text-align: center; margin-top: 3rem; padding: 1rem;">
    <p style="font-family: 'DM Sans', sans-serif; font-size: 0.7rem; color: #4a5568;">
        {t("footer", lang)}
    </p>
</div>
""",
    unsafe_allow_html=True,
)
