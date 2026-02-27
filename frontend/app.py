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

    /* ── Chat input bar ───────────────────────── */
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
        background: transparent !important;
        color: #2d3436 !important;
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
    }

    /* ── Chat bubbles ─────────────────────────── */
    .msg-user {
        background: rgba(125, 122, 201, 1); color: white;
        padding: 0.8rem 1.1rem; border-radius: 16px 16px 4px 16px;
        margin: 0.4rem 0 0.4rem 4rem; line-height: 1.6; font-size: 0.9rem;
    }
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

    /* ── Quick action buttons ─────────────────── */
    .stButton > button {
        border-color: rgba(125, 122, 201, 0.3) !important;
    }
    .stButton > button:hover {
        border-color: rgba(125, 122, 201, 0.7) !important;
        background: rgba(125, 122, 201, 0.08) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── Language toggle ───────────


def _set_lang(new_lang: str):
    st.session_state.lang = new_lang


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
            prefix += f"\u2022 {v}\n"
        response_text = prefix + "\n" + response_text

    return {"response": response_text, "agent": agent_key, "crisis": crisis["is_crisis"]}


def _safe(text: str) -> str:
    return html_lib.escape(text).replace("\n", "<br>")


def _send(msg_key: str):
    st.session_state._pending_msg = t(msg_key, lang)
    st.session_state.show_welcome = False


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

    st.markdown(
        f"<p style='text-align:center; color:#636e72; font-size:0.93rem; line-height:1.7; margin:0;'>"
        f"{t('welcome_body', lang).replace(chr(10)+chr(10), '<br>')}</p>",
        unsafe_allow_html=True,
    )

    st.write("")

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
