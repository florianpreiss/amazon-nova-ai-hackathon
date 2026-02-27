"""
KODA — Streamlit Chat Interface.

Warm, approachable design. Uses native Streamlit components and theming.
No CSS injection hacks — everything uses Streamlit's built-in systems.
"""

import html as html_lib
import uuid

import streamlit as st
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


# ── Minimal CSS for chat bubbles only ──────────────────

st.markdown(
    """
<style>
    /* Hide default Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Chat bubbles */
    .msg-user {
        background: #1a8a6e; color: white;
        padding: 0.8rem 1.1rem; border-radius: 16px 16px 4px 16px;
        margin: 0.4rem 0 0.4rem 4rem; line-height: 1.6; font-size: 0.9rem;
    }
    .msg-koda {
        background: white; color: #2d3436; border: 1px solid #e8e4df;
        padding: 0.8rem 1.1rem; border-radius: 16px 16px 16px 4px;
        margin: 0.4rem 4rem 0.4rem 0; line-height: 1.6; font-size: 0.9rem;
    }
    .msg-koda .badge {
        font-size: 0.7rem; color: #e8853a; font-weight: 700;
        letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem;
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


def _safe(text: str) -> str:
    """Escape HTML to prevent XSS, convert newlines to <br>."""
    return html_lib.escape(text).replace("\n", "<br>")


def _send(msg_key: str):
    """Queue a quick-action message."""
    st.session_state._pending_msg = t(msg_key, lang)
    st.session_state.show_welcome = False


# ── Language toggle — proper segmented control ─────────

col_header, col_lang = st.columns([4, 1])

with col_header:
    st.title("🧭 KODA")

with col_lang:
    selected_lang = st.segmented_control(
        label="Language",
        options=["🇩🇪 DE", "🇬🇧 EN"],
        default="🇩🇪 DE" if lang == "de" else "🇬🇧 EN",
        label_visibility="collapsed",
        key="lang_toggle",
    )
    new_lang = "de" if selected_lang == "🇩🇪 DE" else "en"
    if new_lang != lang:
        st.session_state.lang = new_lang
        st.rerun()

# ── Tagline ────────────────────────────────────────────

st.caption(t("subtitle", lang))

# ── Welcome screen ─────────────────────────────────────

if st.session_state.show_welcome and not st.session_state.messages:
    st.divider()

    # Stats — using native st.columns and st.metric
    col_left, col_right = st.columns(2)

    with col_left:
        if lang == "de":
            st.metric(
                label="Nicht-Akademikerkinder",
                value="27 von 100",
                delta="beginnen ein Studium",
                delta_color="inverse",
            )
        else:
            st.metric(
                label="Non-academic families",
                value="27 of 100",
                delta="start university",
                delta_color="inverse",
            )

    with col_right:
        if lang == "de":
            st.metric(
                label="Akademikerkinder",
                value="79 von 100",
                delta="beginnen ein Studium",
                delta_color="normal",
            )
        else:
            st.metric(
                label="Academic families",
                value="79 of 100",
                delta="start university",
                delta_color="normal",
            )

    st.divider()

    # Welcome text
    st.markdown(f"**{t('welcome_body', lang)}**")

    st.write("")  # spacing

    # Quick actions — 2 rows of 3
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

    st.write("")  # spacing

# ── Chat history ───────────────────────────────────────

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-user">{_safe(msg["content"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        label = get_agent_label(msg.get("agent", "COMPASS"), lang)
        st.markdown(
            f'<div class="msg-koda">'
            f'<div class="badge">{label}</div>'
            f'{_safe(msg["content"])}'
            f'</div>',
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
        f'<div class="msg-user">{_safe(user_input)}</div>',
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

st.divider()
st.caption(t("footer", lang))
