"""
KODA — Streamlit Chat Interface.

A warm, welcoming chat UI for first-generation academics.
Connects to the KODA FastAPI backend or runs agents directly.
"""

import streamlit as st
import requests
import uuid
import time

# ── Page config ────────────────────────────────────────

st.set_page_config(
    page_title="KODA — Your Academic Companion",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,700;1,9..144,400&display=swap');

    /* Global */
    .stApp {
        background: linear-gradient(175deg, #0a0f1a 0%, #111827 50%, #0d1520 100%);
    }
    .block-container {
        max-width: 720px;
        padding-top: 2rem;
    }

    /* Header */
    .koda-header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .koda-title {
        font-family: 'Fraunces', serif;
        font-size: 3.2rem;
        font-weight: 300;
        letter-spacing: 0.15em;
        background: linear-gradient(135deg, #ffffff 0%, #0d9488 60%, #d97706 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .koda-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #6b8090;
        margin-top: 0.3rem;
        font-style: italic;
    }
    .koda-divider {
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, #0d9488, #d97706);
        margin: 1rem auto;
        border-radius: 2px;
    }

    /* Chat messages */
    .chat-msg {
        font-family: 'DM Sans', sans-serif;
        padding: 1rem 1.2rem;
        border-radius: 16px;
        margin: 0.5rem 0;
        line-height: 1.65;
        font-size: 0.92rem;
    }
    .msg-user {
        background: rgba(13, 148, 136, 0.12);
        border: 1px solid rgba(13, 148, 136, 0.2);
        color: #d1e8e5;
        margin-left: 2rem;
    }
    .msg-koda {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        color: #c8d0d8;
        margin-right: 2rem;
    }
    .msg-koda .agent-badge {
        font-size: 0.7rem;
        color: #d97706;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
        font-family: 'DM Sans', sans-serif;
    }

    /* Quick action buttons */
    .quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        margin: 1.5rem 0;
    }
    .quick-btn {
        font-family: 'DM Sans', sans-serif;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #8a9aaa;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-btn:hover {
        background: rgba(13, 148, 136, 0.1);
        border-color: rgba(13, 148, 136, 0.3);
        color: #d1e8e5;
    }

    /* Welcome card */
    .welcome-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
    }
    .welcome-card p {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.88rem;
        color: #8a9aaa;
        line-height: 1.7;
    }
    .welcome-card .stat {
        font-family: 'Fraunces', serif;
        font-size: 1.8rem;
        font-weight: 300;
        color: #0d9488;
    }

    /* Stats row */
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin: 1rem 0;
    }
    .stat-item {
        text-align: center;
    }
    .stat-number {
        font-family: 'Fraunces', serif;
        font-size: 1.6rem;
        font-weight: 300;
        color: #0d9488;
    }
    .stat-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        color: #6b8090;
        margin-top: 0.2rem;
    }

    /* Input styling */
    .stChatInput > div {
        border-radius: 24px !important;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Crisis banner */
    .crisis-banner {
        background: rgba(220, 38, 38, 0.08);
        border: 1px solid rgba(220, 38, 38, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #f8a0a0;
    }
</style>
""", unsafe_allow_html=True)

# ── Configuration ──────────────────────────────────────

API_URL = "http://localhost:8000/api/chat"
USE_DIRECT_AGENTS = True  # Set to False to use FastAPI backend instead

# ── Session state initialization ───────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

# ── Agent initialization (direct mode) ─────────────────

@st.cache_resource
def load_agents():
    """Initialize agents once and cache them."""
    from src.agents.router import RouterAgent
    from src.agents.crisis import CrisisRadar
    from src.agents.compass import CompassAgent
    from src.agents.financing.student_aid import StudentAidAgent
    from src.agents.financing.scholarships import ScholarshipAgent
    from src.agents.financing.cost_of_living import CostOfLivingAgent
    from src.agents.study_choice.degree_explorer import DegreeExplorerAgent
    from src.agents.academic_basics.hidden_curriculum import HiddenCurriculumAgent
    from src.agents.academic_basics.study_vs_apprenticeship import StudyVsApprenticeshipAgent
    from src.agents.role_models.anti_impostor import AntiImpostorAgent
    from src.agents.role_models.matching import RoleModelAgent

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

# ── Chat logic ─────────────────────────────────────────

def get_response_direct(user_message: str, history: list) -> dict:
    """Call agents directly (no FastAPI backend needed)."""
    system = load_agents()

    # Build message history in Bedrock format
    bedrock_messages = []
    for msg in history:
        bedrock_messages.append({
            "role": msg["role"],
            "content": [{"text": msg["content"]}],
        })
    bedrock_messages.append({
        "role": "user",
        "content": [{"text": user_message}],
    })

    # Crisis scan
    crisis = system["crisis"].scan(user_message)

    # Route
    agent_key = system["router"].route(user_message)
    agent = system["agents"].get(agent_key, system["agents"]["COMPASS"])

    # Get response
    text = agent.respond(bedrock_messages)

    # Prepend crisis resources
    if crisis["is_crisis"] and crisis["resources"]:
        prefix = "⚠️ I notice you may be going through a difficult time. Here are immediate resources:\n"
        for v in crisis["resources"].values():
            prefix += f"• {v}\n"
        text = prefix + "\n" + text

    return {"response": text, "agent": agent_key, "crisis": crisis["is_crisis"]}


def get_response_api(user_message: str) -> dict:
    """Call the FastAPI backend."""
    try:
        resp = requests.post(API_URL, json={
            "session_id": st.session_state.session_id,
            "message": user_message,
        }, timeout=120)
        data = resp.json()
        return {
            "response": data["response"],
            "agent": data["agent_used"],
            "crisis": data["crisis_detected"],
        }
    except Exception as e:
        return {
            "response": f"Connection error: {e}. Make sure the backend is running.",
            "agent": "ERROR",
            "crisis": False,
        }

# ── Agent name mapping for display ─────────────────────

AGENT_LABELS = {
    "COMPASS": "🧭 Compass",
    "FINANCING": "💰 Financing",
    "STUDY_CHOICE": "🎓 Study Choice",
    "ACADEMIC_BASICS": "📖 Academic Basics",
    "ROLE_MODELS": "⭐ Role Models",
}

# ── UI Layout ──────────────────────────────────────────

# Header
st.markdown("""
<div class="koda-header">
    <h1 class="koda-title">KODA</h1>
    <p class="koda-subtitle">You've arrived. And you're not alone.</p>
    <div class="koda-divider"></div>
</div>
""", unsafe_allow_html=True)

# Welcome screen (shown only before first message)
if st.session_state.show_welcome and not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <div class="stats-row">
            <div class="stat-item">
                <div class="stat-number">27</div>
                <div class="stat-label">out of 100 non-academic<br>children start university</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">79</div>
                <div class="stat-label">out of 100 academic<br>children start university</div>
            </div>
        </div>
        <p style="margin-top: 1rem;">
            KODA is your AI companion for navigating higher education.<br>
            No question is too basic. Nobody explains this automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💰 What is BAföG?", use_container_width=True):
            st.session_state.quick_msg = "What is BAföG and could I be eligible?"
    with col2:
        if st.button("🎓 Study or apprenticeship?", use_container_width=True):
            st.session_state.quick_msg = "Should I study at university or do an apprenticeship?"
    with col3:
        if st.button("😟 I feel overwhelmed", use_container_width=True):
            st.session_state.quick_msg = "Everyone else seems to know what they're doing and I feel lost"

    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("📖 What is ECTS?", use_container_width=True):
            st.session_state.quick_msg = "What does ECTS mean?"
    with col5:
        if st.button("🔍 Find scholarships", use_container_width=True):
            st.session_state.quick_msg = "Are there scholarships for first-generation students?"
    with col6:
        if st.button("⭐ Role models", use_container_width=True):
            st.session_state.quick_msg = "Who are famous people who were first in their family to study?"


# Render chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-msg msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        agent_label = AGENT_LABELS.get(msg.get("agent", ""), "🧭 KODA")
        st.markdown(
            f'<div class="chat-msg msg-koda">'
            f'<div class="agent-badge">{agent_label}</div>'
            f'{msg["content"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Handle input ───────────────────────────────────────

# Check for quick action button press
user_input = None
if "quick_msg" in st.session_state:
    user_input = st.session_state.quick_msg
    del st.session_state.quick_msg
    st.session_state.show_welcome = False

# Chat input
chat_input = st.chat_input("Ask KODA anything about studying, finances, or university life...")
if chat_input:
    user_input = chat_input
    st.session_state.show_welcome = False

# Process input
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f'<div class="chat-msg msg-user">{user_input}</div>', unsafe_allow_html=True)

    # Get response
    with st.spinner("KODA is thinking..."):
        if USE_DIRECT_AGENTS:
            result = get_response_direct(user_input, st.session_state.messages[:-1])
        else:
            result = get_response_api(user_input)

    # Add assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["response"],
        "agent": result["agent"],
    })

    # Render response
    agent_label = AGENT_LABELS.get(result["agent"], "🧭 KODA")
    st.markdown(
        f'<div class="chat-msg msg-koda">'
        f'<div class="agent-badge">{agent_label}</div>'
        f'{result["response"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.rerun()

# ── Footer ─────────────────────────────────────────────

st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 1rem;">
    <p style="font-family: 'DM Sans', sans-serif; font-size: 0.7rem; color: #4a5568;">
        KODA provides orientation, not legal or financial advice.
        No data is stored. Your session is private and ephemeral.
    </p>
</div>
""", unsafe_allow_html=True)
