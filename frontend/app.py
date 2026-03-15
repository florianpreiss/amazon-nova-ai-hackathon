"""
KODA — Streamlit Chat Interface.
"""

import html as html_lib
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.provenance import ResponseProvenance
from src.core.session_bundle import serialize_session_bundle
from src.i18n import DEFAULT_LANGUAGE, get_agent_label, t
from src.orchestration import ChatTurnResult, build_default_chat_service
from src.ui import build_session_profile_view

# ── Page config ────────────────────────────────────────

st.set_page_config(
    page_title="KODA — Dein Studienbegleiter | Your Study Companion",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True
if "lang" not in st.session_state:
    st.session_state.lang = DEFAULT_LANGUAGE
if "memory_import_revision" not in st.session_state:
    st.session_state.memory_import_revision = 0

lang = st.session_state.lang

# ── CSS ────────────────────────────────────────────────

st.markdown(
    """
<style>
    /* Hide Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    .stDeployButton { display: none; }
    header, [data-testid="stHeader"] {
        visibility: visible !important;
        background: transparent !important;
    }
    [data-testid="stToolbar"] {
        background: transparent !important;
        padding: 0.35rem 0.5rem 0 0.45rem !important;
    }
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"] button {
        align-items: center !important;
        background: rgba(244, 236, 248, 0.94) !important;
        border: 1px solid rgba(154, 129, 186, 0.24) !important;
        border-radius: 999px !important;
        box-shadow: 0 10px 24px rgba(143, 121, 180, 0.2) !important;
        color: #73619b !important;
        display: inline-flex !important;
        justify-content: center !important;
        transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease !important;
    }
    [data-testid="stExpandSidebarButton"] {
        margin-left: 0.05rem !important;
    }
    [data-testid="stExpandSidebarButton"]:hover,
    [data-testid="stSidebarCollapseButton"] button:hover {
        background: rgba(251, 244, 253, 0.98) !important;
        box-shadow: 0 12px 28px rgba(143, 121, 180, 0.26) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="stSidebarCollapseButton"] svg {
        color: #73619b !important;
        fill: currentColor !important;
    }

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
    .ai-disclaimer {
        background: rgba(125, 122, 201, 0.08);
        border: 1px solid rgba(125, 122, 201, 0.18);
        border-radius: 14px;
        color: #5f6470;
        font-family: 'Nunito', sans-serif;
        font-size: 0.78rem;
        line-height: 1.5;
        margin: 0 auto 1rem auto;
        max-width: 760px;
        padding: 0.75rem 0.95rem;
        text-align: center;
    }
    .welcome-copy,
    .footer-copy {
        color: #636e72;
        font-family: 'Nunito', sans-serif;
        margin: 0;
        text-align: center;
    }
    .welcome-copy {
        font-size: 0.93rem;
        line-height: 1.7;
    }
    .footer-copy {
        font-size: 0.85rem;
        line-height: 1.6;
    }
    .welcome-copy p,
    .footer-copy p {
        margin: 0.5rem 0 0 0;
    }
    .welcome-copy p:first-child,
    .footer-copy p:first-child {
        margin-top: 0;
    }

    /* ── Sidebar session profile ────────────── */
    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(240, 231, 246, 0.95) 0%, rgba(228, 224, 248, 0.94) 100%);
        border-right: 1px solid rgba(154, 129, 186, 0.18);
        overflow: hidden;
        position: relative;
    }
    [data-testid="stSidebar"]::before {
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.5) 0%, rgba(241, 233, 248, 0.36) 100%),
            url('app/static/left-bg.jpeg');
        background-position: center center;
        background-repeat: no-repeat;
        background-size: cover;
        content: "";
        inset: 0;
        opacity: 0.96;
        pointer-events: none;
        position: absolute;
    }
    [data-testid="stSidebar"]::after {
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.18) 0%, rgba(192, 181, 241, 0.14) 100%);
        content: "";
        inset: 0;
        opacity: 0.55;
        pointer-events: none;
        position: absolute;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding-top: 1rem;
        position: relative;
        z-index: 1;
    }
    .sidebar-shell {
        font-family: 'Nunito', sans-serif;
        padding-top: 0.2rem;
    }
    .sidebar-kicker {
        color: #876fb2;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }
    .sidebar-title {
        color: #58426d;
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 1.45rem;
        font-weight: 700;
        line-height: 1.1;
        margin: 0 0 0.55rem 0;
    }
    .sidebar-note,
    .sidebar-empty,
    .sidebar-alert {
        border-radius: 16px;
        font-family: 'Nunito', sans-serif;
        font-size: 0.83rem;
        line-height: 1.55;
        padding: 0.85rem 0.9rem;
    }
    .sidebar-note {
        background: rgba(255, 255, 255, 0.58);
        border: 1px solid rgba(154, 129, 186, 0.16);
        color: #6c5a86;
        margin-bottom: 0.9rem;
    }
    .sidebar-empty {
        background: rgba(255, 255, 255, 0.74);
        border: 1px dashed rgba(154, 129, 186, 0.24);
        color: #6d6188;
        margin-top: 0.2rem;
    }
    .sidebar-alert {
        background: rgba(214, 48, 49, 0.08);
        border: 1px solid rgba(214, 48, 49, 0.16);
        color: #8b2d2d;
        margin-top: 0.4rem;
    }
    .sidebar-stats {
        display: grid;
        gap: 0.55rem;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin: 0.95rem 0 1rem 0;
    }
    .sidebar-stat {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(154, 129, 186, 0.14);
        border-radius: 14px;
        padding: 0.62rem 0.72rem;
    }
    .sidebar-stat.wide {
        grid-column: 1 / -1;
    }
    .sidebar-stat-label {
        color: #947aac;
        font-family: 'Nunito', sans-serif;
        font-size: 0.64rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 0.16rem;
        text-transform: uppercase;
    }
    .sidebar-stat-value {
        color: #58426d;
        font-family: 'Source Serif 4', Georgia, serif;
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.25;
    }
    .sidebar-section {
        margin-top: 0.9rem;
    }
    .sidebar-section-label {
        color: #7e69a0;
        font-family: 'Nunito', sans-serif;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        margin-bottom: 0.45rem;
        text-transform: uppercase;
    }
    .sidebar-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.38rem;
    }
    .sidebar-chip {
        background: rgba(154, 129, 186, 0.08);
        border: 1px solid rgba(154, 129, 186, 0.15);
        border-radius: 999px;
        color: #755f96;
        display: inline-block;
        font-family: 'Nunito', sans-serif;
        font-size: 0.74rem;
        font-weight: 700;
        line-height: 1.25;
        padding: 0.28rem 0.62rem;
    }
    .sidebar-list,
    .sidebar-source-list {
        margin: 0;
        padding-left: 1rem;
    }
    .sidebar-list li,
    .sidebar-source-list li {
        color: #58426d;
        font-family: 'Nunito', sans-serif;
        font-size: 0.84rem;
        line-height: 1.55;
        margin-bottom: 0.4rem;
    }
    .sidebar-list.compact li {
        margin-bottom: 0.28rem;
    }
    .sidebar-gap {
        height: 0.5rem;
    }
    .sidebar-source-list {
        list-style: none;
        padding-left: 0;
    }
    .sidebar-source-list li {
        margin-bottom: 0.55rem;
    }
    .sidebar-source-tag {
        border-radius: 999px;
        display: inline-block;
        font-family: 'Nunito', sans-serif;
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        margin-right: 0.35rem;
        padding: 0.14rem 0.42rem;
        text-transform: uppercase;
    }
    .sidebar-source-tag.registry {
        background: rgba(0, 184, 148, 0.12);
        color: #0b7d68;
    }
    .sidebar-source-tag.web {
        background: rgba(9, 132, 227, 0.12);
        color: #0c6fbe;
    }
    .sidebar-source-link {
        color: #735894;
        text-decoration: none;
    }
    .sidebar-source-link:hover {
        text-decoration: underline;
    }
    .sidebar-source-domain {
        color: #8b79a9;
        display: block;
        font-size: 0.74rem;
        margin-top: 0.08rem;
        overflow-wrap: anywhere;
    }
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.42);
        border: 1px solid rgba(154, 129, 186, 0.14);
        border-radius: 14px;
        overflow: hidden;
    }
    [data-testid="stExpander"] details summary p {
        color: #755f96 !important;
        font-family: 'Nunito', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stExpander"] details > div {
        background: transparent !important;
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
    .stChatInput > div:focus-within {
        border-color: rgba(125, 122, 201, 0.58) !important;
        box-shadow: 0 0 0 4px rgba(125, 122, 201, 0.12) !important;
    }
    .stChatInput textarea {
        background: #f0ebe4 !important;
        background-color: #f0ebe4 !important;
        color: #2d3436 !important;
        padding: 0.5rem !important;
        caret-color: rgba(125, 122, 201, 1) !important;
        -webkit-text-fill-color: #2d3436 !important;
    }
    .stChatInput textarea::placeholder {
        color: #7a8388 !important;
        opacity: 1 !important;
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
        font-family: 'Nunito', sans-serif;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] a,
    [data-testid="stChatMessage"] em,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] blockquote {
        font-family: 'Nunito', sans-serif !important;
    }
    [data-testid="stChatMessage"] p {
        margin: 0 0 0.65rem 0;
    }
    [data-testid="stChatMessage"] p:last-child,
    [data-testid="stChatMessage"] ul:last-child,
    [data-testid="stChatMessage"] ol:last-child,
    [data-testid="stChatMessage"] pre:last-child,
    [data-testid="stChatMessage"] blockquote:last-child {
        margin-bottom: 0 !important;
    }
    [data-testid="stChatMessage"] h1,
    [data-testid="stChatMessage"] h2,
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4,
    [data-testid="stChatMessage"] h5,
    [data-testid="stChatMessage"] h6 {
        color: #2d3436 !important;
        font-family: 'Nunito', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em;
        line-height: 1.3;
        margin: 0.35rem 0 0.55rem 0 !important;
    }
    [data-testid="stChatMessage"] h1 { font-size: 1.2rem !important; }
    [data-testid="stChatMessage"] h2 { font-size: 1.08rem !important; }
    [data-testid="stChatMessage"] h3,
    [data-testid="stChatMessage"] h4,
    [data-testid="stChatMessage"] h5,
    [data-testid="stChatMessage"] h6 { font-size: 0.98rem !important; }
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] ol {
        margin: 0.15rem 0 0.8rem 0;
        padding-left: 1.2rem;
    }
    [data-testid="stChatMessage"] strong {
        color: #1f2527 !important;
        font-weight: 800 !important;
    }
    [data-testid="stChatMessage"] a {
        color: rgba(96, 88, 185, 1) !important;
        text-decoration: underline;
        text-decoration-color: rgba(125, 122, 201, 0.35);
        text-underline-offset: 0.12em;
    }
    [data-testid="stChatMessage"] blockquote {
        border-left: 3px solid rgba(125, 122, 201, 0.28);
        color: #5f6470 !important;
        margin: 0.3rem 0 0.8rem 0;
        padding-left: 0.85rem;
    }
    [data-testid="stChatMessage"] pre {
        background: #f6f2ec !important;
        border: 1px solid #ece5de !important;
        border-radius: 12px;
        margin: 0.35rem 0 0.85rem 0;
        overflow-x: auto;
        padding: 0.8rem 0.9rem !important;
    }
    /* Agent label badge */
    [data-testid="stChatMessage"] small {
        font-size: 0.7rem !important;
        color: rgba(125, 122, 201, 0.8) !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }
    .provenance-row {
        margin: 0.1rem 0 0.65rem 0;
    }
    .provenance-pill {
        display: inline-block;
        border-radius: 999px;
        font-family: 'Nunito', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 0.25rem 0.6rem;
    }
    .provenance-pill.registry {
        background: rgba(0, 184, 148, 0.12);
        color: #0b7d68;
    }
    .provenance-pill.registry-web {
        background: rgba(125, 122, 201, 0.12);
        color: rgba(96, 88, 185, 1);
    }
    .provenance-pill.web {
        background: rgba(9, 132, 227, 0.12);
        color: #0c6fbe;
    }
    .provenance-pill.model {
        background: rgba(99, 110, 114, 0.12);
        color: #5f6470;
    }
    .source-list {
        margin-top: 0.85rem;
    }
    .source-list-label {
        color: #636e72;
        font-family: 'Nunito', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
    }
    .source-list ul {
        margin: 0;
        padding-left: 0;
        list-style: none;
    }
    .source-list li {
        color: #2d3436;
        display: flex;
        font-size: 0.88rem;
        flex-wrap: wrap;
        gap: 0.2rem 0.4rem;
        line-height: 1.5;
        margin-bottom: 0.35rem;
    }
    .source-tag {
        display: inline-block;
        border-radius: 999px;
        font-family: 'Nunito', sans-serif;
        font-size: 0.66rem;
        font-weight: 700;
        margin-right: 0.1rem;
        padding: 0.1rem 0.4rem;
    }
    .source-tag.registry {
        background: rgba(0, 184, 148, 0.12);
        color: #0b7d68;
    }
    .source-tag.web {
        background: rgba(9, 132, 227, 0.12);
        color: #0c6fbe;
    }
    .source-list a {
        color: rgba(96, 88, 185, 1);
        overflow-wrap: anywhere;
        text-decoration: none;
    }
    .source-list a:hover {
        text-decoration: underline;
    }
    .source-domain {
        color: #7a8388;
        font-size: 0.76rem;
        margin-left: 0.1rem;
        overflow-wrap: anywhere;
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
        display: flex !important;
        align-items: center !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        justify-content: center !important;
        line-height: 1.25 !important;
        min-height: 3.1rem !important;
        padding: 0.42rem 0.75rem !important;
        text-align: center !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease,
                    border-color 0.15s ease, background 0.15s ease !important;
        letter-spacing: 0.01em !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: initial !important;
    }
    [data-testid="baseButton-secondary"] p,
    [data-testid="baseButton-primary"] p {
        line-height: 1.25 !important;
        margin: 0 !important;
        white-space: normal !important;
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
        display: flex !important;
        align-items: center !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        justify-content: center !important;
        padding: 0.3rem 0.85rem !important;
        transition: all 0.15s ease !important;
        letter-spacing: 0.01em !important;
        text-align: center !important;
    }
    [data-testid="baseButton-primary"]:hover {
        background: rgba(125, 122, 201, 0.1) !important;
        border-color: rgba(125, 122, 201, 0.8) !important;
        box-shadow: 0 2px 8px rgba(125, 122, 201, 0.25) !important;
    }
    .stChatInput button:focus-visible,
    [data-testid="baseButton-secondary"]:focus-visible,
    [data-testid="baseButton-primary"]:focus-visible {
        outline: 3px solid rgba(125, 122, 201, 0.22) !important;
        outline-offset: 2px !important;
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
            color: #8790a3 !important;
        }
        .ai-disclaimer {
            background: rgba(125, 122, 201, 0.14) !important;
            border-color: rgba(125, 122, 201, 0.25) !important;
            color: #a0a8b8 !important;
        }
        .welcome-copy,
        .footer-copy {
            color: #aeb6c8 !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #31253c 0%, #271f34 100%) !important;
            border-right-color: rgba(212, 181, 235, 0.18) !important;
        }
        [data-testid="stSidebar"]::before {
            background:
                linear-gradient(180deg, rgba(38, 27, 50, 0.5) 0%, rgba(47, 34, 63, 0.42) 100%),
                url('app/static/left-bg.jpeg') !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-size: cover !important;
        }
        [data-testid="stSidebar"]::after {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(190, 177, 243, 0.08) 100%) !important;
            opacity: 0.48 !important;
        }
        .sidebar-title {
            color: #f7eefc !important;
        }
        .sidebar-note {
            background: rgba(244, 233, 250, 0.08) !important;
            border-color: rgba(212, 181, 235, 0.16) !important;
            color: #ead8f5 !important;
        }
        .sidebar-empty {
            background: rgba(17, 35, 48, 0.78) !important;
            border-color: rgba(212, 181, 235, 0.22) !important;
            color: #eedff7 !important;
        }
        .sidebar-alert {
            background: rgba(214, 48, 49, 0.14) !important;
            border-color: rgba(214, 48, 49, 0.24) !important;
            color: #ffb3b0 !important;
        }
        .sidebar-stat {
            background: rgba(48, 34, 63, 0.82) !important;
            border-color: rgba(212, 181, 235, 0.16) !important;
        }
        .sidebar-stat-label {
            color: #ceb4e4 !important;
        }
        .sidebar-stat-value,
        .sidebar-list li,
        .sidebar-source-list li {
            color: #f7eefc !important;
        }
        .sidebar-section-label {
            color: #decaef !important;
        }
        .sidebar-chip {
            background: rgba(212, 181, 235, 0.12) !important;
            border-color: rgba(212, 181, 235, 0.2) !important;
            color: #f2e2fb !important;
        }
        .sidebar-source-tag.registry {
            background: rgba(0, 184, 148, 0.2) !important;
            color: #7ce3cb !important;
        }
        .sidebar-source-tag.web {
            background: rgba(9, 132, 227, 0.2) !important;
            color: #88c7ff !important;
        }
        .sidebar-source-link {
            color: #f2e2fb !important;
        }
        .sidebar-source-domain {
            color: #d2bcdf !important;
        }
        [data-testid="stExpander"] {
            background: rgba(54, 38, 70, 0.54) !important;
            border-color: rgba(212, 181, 235, 0.14) !important;
        }
        [data-testid="stExpander"] details summary p {
            color: #f2e2fb !important;
        }
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapseButton"] button {
            background: rgba(68, 49, 89, 0.92) !important;
            border-color: rgba(212, 181, 235, 0.22) !important;
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28) !important;
            color: #f2e2fb !important;
        }
        [data-testid="stExpandSidebarButton"]:hover,
        [data-testid="stSidebarCollapseButton"] button:hover {
            background: rgba(92, 68, 118, 0.96) !important;
        }
        [data-testid="stExpandSidebarButton"] svg,
        [data-testid="stSidebarCollapseButton"] svg {
            color: #f2e2fb !important;
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
        [data-testid="stChatMessage"] code,
        [data-testid="stChatMessage"] a {
            color: #e8e4f0 !important;
        }
        [data-testid="stChatMessage"] h1,
        [data-testid="stChatMessage"] h2,
        [data-testid="stChatMessage"] h3,
        [data-testid="stChatMessage"] h4,
        [data-testid="stChatMessage"] h5,
        [data-testid="stChatMessage"] h6 {
            color: #f4f0fb !important;
        }
        /* Inline code blocks */
        [data-testid="stChatMessage"] code {
            background: rgba(125, 122, 201, 0.15) !important;
            border-radius: 4px;
            padding: 0.1em 0.35em;
        }
        [data-testid="stChatMessage"] pre {
            background: rgba(125, 122, 201, 0.12) !important;
            border-color: rgba(125, 122, 201, 0.24) !important;
        }
        [data-testid="stChatMessage"] strong {
            color: #ffffff !important;
        }
        [data-testid="stChatMessage"] blockquote {
            border-left-color: rgba(160, 155, 220, 0.45) !important;
            color: #b9c0cf !important;
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
        .stChatInput > div:focus-within {
            border-color: rgba(160, 155, 220, 0.72) !important;
            box-shadow: 0 0 0 4px rgba(125, 122, 201, 0.2) !important;
        }
        .stChatInput textarea {
            background: #252540 !important;
            background-color: #252540 !important;
            color: #e8e4f0 !important;
            -webkit-text-fill-color: #e8e4f0 !important;
            caret-color: rgba(160, 155, 220, 1) !important;
        }
        .stChatInput textarea::placeholder {
            color: #9ea8b4 !important;
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
            color: #aeb6c8 !important;
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

        .provenance-pill.registry {
            background: rgba(0, 184, 148, 0.2) !important;
            color: #7ce3cb !important;
        }
        .provenance-pill.registry-web {
            background: rgba(125, 122, 201, 0.22) !important;
            color: #c8c4e8 !important;
        }
        .provenance-pill.web {
            background: rgba(9, 132, 227, 0.2) !important;
            color: #88c7ff !important;
        }
        .provenance-pill.model {
            background: rgba(99, 110, 114, 0.2) !important;
            color: #b7bec8 !important;
        }
        .source-list-label,
        .source-list li {
            color: #c8c4e8 !important;
        }
        .source-tag.registry {
            background: rgba(0, 184, 148, 0.2) !important;
            color: #7ce3cb !important;
        }
        .source-tag.web {
            background: rgba(9, 132, 227, 0.2) !important;
            color: #88c7ff !important;
        }
        .source-list a {
            color: #d8d3ff !important;
            text-decoration-color: rgba(216, 211, 255, 0.35) !important;
        }
        .source-domain {
            color: #9ea8b4 !important;
        }

        /* ── Divider ─────────────────────────── */
        hr {
            border-color: rgba(125, 122, 201, 0.15) !important;
        }
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 0.35rem !important;
        }
        .koda-title {
            font-size: 3rem;
            letter-spacing: 0.16em;
            margin-top: 0.15rem;
        }
        .koda-tagline {
            font-size: 0.93rem;
            padding: 0 0.25rem;
        }
        .koda-heritage {
            font-size: 0.68rem;
            margin-bottom: 0.85rem;
            padding: 0 0.3rem;
        }
        .ai-disclaimer {
            font-size: 0.74rem;
            margin-bottom: 0.85rem;
            padding: 0.7rem 0.8rem;
        }
        .sidebar-title {
            font-size: 1.45rem;
        }
        .sidebar-note,
        .sidebar-empty,
        .sidebar-alert {
            font-size: 0.8rem;
            padding: 0.8rem 0.82rem;
        }
        .sidebar-stats {
            gap: 0.45rem;
        }
        .sidebar-stat {
            padding: 0.7rem 0.75rem;
        }
        .sidebar-stat-value {
            font-size: 0.91rem;
        }
        .welcome-copy {
            font-size: 0.89rem;
        }
        .footer-copy {
            font-size: 0.81rem;
        }
        .stat-box {
            padding: 1rem 0.85rem;
        }
        .stat-value {
            font-size: 1.85rem;
        }
        .msg-user {
            font-size: 0.88rem;
            margin-left: 1.35rem;
            padding: 0.74rem 0.95rem;
        }
        [data-testid="stChatMessage"],
        .msg-koda {
            font-size: 0.88rem;
            margin-right: 1.35rem;
            padding: 0.78rem 0.95rem;
        }
        [data-testid="stChatMessage"] h1 {
            font-size: 1.08rem !important;
        }
        [data-testid="stChatMessage"] h2 {
            font-size: 1rem !important;
        }
        [data-testid="stChatMessage"] h3,
        [data-testid="stChatMessage"] h4,
        [data-testid="stChatMessage"] h5,
        [data-testid="stChatMessage"] h6 {
            font-size: 0.92rem !important;
        }
        .source-list {
            margin-top: 0.75rem;
        }
        .source-domain {
            display: block;
            margin-left: 0;
            width: 100%;
        }
        .stChatInput > div {
            border-radius: 20px !important;
        }
        .stChatInput textarea {
            font-size: 0.94rem !important;
            padding: 0.45rem !important;
        }
        [data-testid="baseButton-secondary"] {
            font-size: 0.8rem !important;
            min-height: 3.35rem !important;
            padding: 0.48rem 0.7rem !important;
        }
        [data-testid="baseButton-primary"] {
            min-height: 2.65rem !important;
            padding: 0.36rem 0.8rem !important;
        }
    }
    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
        }
        .sidebar-title {
            font-size: 1.32rem;
        }
        .sidebar-stat-value {
            font-size: 0.9rem;
        }
        .koda-title {
            font-size: 2.35rem;
            letter-spacing: 0.11em;
        }
        .koda-tagline {
            font-size: 0.88rem;
        }
        .koda-heritage {
            font-size: 0.64rem;
        }
        .msg-user {
            margin-left: 0.55rem;
        }
        [data-testid="stChatMessage"],
        .msg-koda {
            margin-right: 0.55rem;
        }
        [data-testid="stChatMessage"] pre {
            padding: 0.7rem 0.75rem !important;
        }
        .provenance-pill,
        .source-tag {
            font-size: 0.62rem;
        }
        .source-list li {
            font-size: 0.83rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── Language toggle ───────────


def _lang_option_for_code(code: str) -> str:
    return "🇩🇪 Deutsch" if code == "de" else "🇬🇧 English"


def _lang_code_for_option(option: str | None) -> str:
    return "de" if option == "🇩🇪 Deutsch" else "en"


def _reset_chat() -> None:
    """
    Clear all conversation state and return to the welcome screen.

    Deletes the active in-memory session, resets local messages and session ID,
    and returns to the welcome screen. The next chat turn will receive a fresh
    ephemeral server-side session. The language preference is intentionally
    preserved — the user should not have to re-select it after resetting.

    Privacy note: no persistent storage exists, so "reset" is purely
    in-memory.  Compliant with the ephemeral-session guarantee in the footer.
    """
    session_id = st.session_state.session_id
    if session_id:
        load_chat_service().end_session(session_id)
    st.session_state.messages = []
    st.session_state.session_id = None
    st.session_state.show_welcome = True
    # Clear any pending quick-action message
    st.session_state.pop("_pending_msg", None)


# ── Language toggle ─────────────────────────────────────
if "_lang_pills" not in st.session_state:
    st.session_state._lang_pills = _lang_option_for_code(lang)

selected_lang_option = st.pills(
    label="Language",
    options=["🇩🇪 Deutsch", "🇬🇧 English"],
    key="_lang_pills",
    label_visibility="collapsed",
)
selected_lang = _lang_code_for_option(selected_lang_option or st.session_state._lang_pills)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()


# ── Shared chat service ────────────────────────────────


@st.cache_resource
def load_chat_service():
    """Initialize the shared chat service once and cache it."""

    return build_default_chat_service()


def _normalize_provenance(value: dict | ResponseProvenance | None) -> ResponseProvenance | None:
    """Convert stored provenance payloads back into a typed object."""

    if value is None:
        return None
    if isinstance(value, ResponseProvenance):
        return value
    if isinstance(value, dict):
        return ResponseProvenance.model_validate(value)
    return None


def _provenance_css_class(provenance: ResponseProvenance) -> str:
    mapping = {
        "source_registry": "registry",
        "source_registry_and_web": "registry-web",
        "web_grounding": "web",
        "model": "model",
    }
    return mapping[provenance.mode]


def _get_provenance_label(provenance: ResponseProvenance, current_lang: str) -> str:
    return t(f"provenance_{provenance.mode}", current_lang)


def _render_provenance_contents(provenance: ResponseProvenance, current_lang: str) -> None:
    """Render provenance badge and source links inside the active container."""

    label = html_lib.escape(_get_provenance_label(provenance, current_lang))
    pill_class = _provenance_css_class(provenance)
    st.markdown(
        f"<div class='provenance-row'><span class='provenance-pill {pill_class}'>{label}</span></div>",
        unsafe_allow_html=True,
    )

    if not provenance.sources:
        return

    items: list[str] = []
    for source in provenance.sources:
        tag_key = (
            "source_tag_registry"
            if source.origin == "source_registry"
            else "source_tag_web_grounding"
        )
        tag_label = html_lib.escape(t(tag_key, current_lang))
        tag_class = "registry" if source.origin == "source_registry" else "web"
        title = html_lib.escape(source.title)
        url = html_lib.escape(source.url, quote=True)
        domain = html_lib.escape(source.domain)
        items.append(
            "<li>"
            f"<span class='source-tag {tag_class}'>{tag_label}</span>"
            f"<a href='{url}' target='_blank' rel='noopener noreferrer'>{title}</a>"
            f"<span class='source-domain'>{domain}</span>"
            "</li>"
        )

    st.markdown(
        f"<div class='source-list'>"
        f"<div class='source-list-label'>{html_lib.escape(t('sources_label', current_lang))}</div>"
        f"<ul>{''.join(items)}</ul>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_provenance_block(
    provenance: dict | ResponseProvenance | None,
    current_lang: str,
    placeholder=None,
) -> None:
    """Render provenance either inline or into a placeholder container."""

    normalized = _normalize_provenance(provenance)
    if normalized is None:
        return

    if placeholder is None:
        _render_provenance_contents(normalized, current_lang)
        return

    with placeholder.container():
        _render_provenance_contents(normalized, current_lang)


def _render_sidebar_section_label(label: str) -> None:
    st.markdown(
        f"<div class='sidebar-section'><div class='sidebar-section-label'>{html_lib.escape(label)}</div></div>",
        unsafe_allow_html=True,
    )


def _render_sidebar_stats(stats: list[tuple[str, str]]) -> None:
    cards = "".join(
        f"<div class='sidebar-stat{' wide' if index == 0 else ''}'>"
        f"<div class='sidebar-stat-label'>{html_lib.escape(label)}</div>"
        f"<div class='sidebar-stat-value'>{html_lib.escape(value)}</div>"
        "</div>"
        for index, (label, value) in enumerate(stats)
    )
    st.markdown(f"<div class='sidebar-stats'>{cards}</div>", unsafe_allow_html=True)


def _render_sidebar_chip_list(items: tuple[str, ...]) -> None:
    chips = "".join(f"<span class='sidebar-chip'>{html_lib.escape(item)}</span>" for item in items)
    st.markdown(f"<div class='sidebar-chip-row'>{chips}</div>", unsafe_allow_html=True)


def _render_sidebar_list(items: tuple[str, ...], *, compact: bool = False) -> None:
    rendered = "".join(f"<li>{html_lib.escape(item)}</li>" for item in items)
    class_name = "sidebar-list compact" if compact else "sidebar-list"
    st.markdown(f"<ul class='{class_name}'>{rendered}</ul>", unsafe_allow_html=True)


def _render_sidebar_sources(sources: tuple, current_lang: str) -> None:
    items: list[str] = []
    for source in sources:
        tag_key = (
            "source_tag_registry"
            if source.origin == "source_registry"
            else "source_tag_web_grounding"
        )
        tag_label = html_lib.escape(t(tag_key, current_lang))
        tag_class = "registry" if source.origin == "source_registry" else "web"
        title = html_lib.escape(source.title)
        url = html_lib.escape(source.url, quote=True)
        domain = html_lib.escape(source.domain)
        items.append(
            "<li>"
            f"<span class='sidebar-source-tag {tag_class}'>{tag_label}</span>"
            f"<a class='sidebar-source-link' href='{url}' target='_blank' rel='noopener noreferrer'>{title}</a>"
            f"<span class='sidebar-source-domain'>{domain}</span>"
            "</li>"
        )

    st.markdown(
        f"<ul class='sidebar-source-list'>{''.join(items)}</ul>",
        unsafe_allow_html=True,
    )


def _history_message_to_ui(message: dict) -> dict[str, str | dict]:
    role = str(message.get("role", "user")).strip().lower()
    content = message.get("content", "")
    if isinstance(content, list):
        text = " ".join(
            str(block.get("text", "")).strip() for block in content if isinstance(block, dict)
        )
    else:
        text = str(content).strip()

    if role == "assistant":
        entry: dict[str, str | dict] = {
            "role": "assistant",
            "content": _normalize_assistant_markdown(text),
        }
        agent = message.get("agent")
        if isinstance(agent, str) and agent.strip():
            entry["agent"] = agent.strip()
        provenance = _normalize_provenance(message.get("provenance"))
        if provenance is not None:
            entry["provenance"] = provenance.model_dump(mode="python")
        return entry

    return {
        "role": "user",
        "content": text,
    }


def _apply_imported_session(imported_session, current_lang: str) -> None:
    existing_session_id = st.session_state.session_id
    if existing_session_id and existing_session_id != imported_session.session_id:
        load_chat_service().end_session(existing_session_id)

    next_lang = imported_session.ui_language or current_lang
    st.session_state.session_id = imported_session.session_id
    st.session_state.messages = [
        _history_message_to_ui(message) for message in imported_session.messages
    ]
    st.session_state.show_welcome = False
    st.session_state.lang = next_lang
    st.session_state._lang_pills = _lang_option_for_code(next_lang)
    st.session_state.memory_import_revision += 1


def _render_session_portability(current_lang: str, session_id: str | None) -> None:
    bundle = load_chat_service().export_session_bundle(session_id) if session_id else None
    upload_key = f"session_bundle_upload_{st.session_state.memory_import_revision}"

    with st.expander(
        t("sidebar_portability", current_lang),
        expanded=False,
        icon=":material/save:",
    ):
        st.caption(t("sidebar_portability_note", current_lang))

        if bundle is not None:
            filename = f"koda-session-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.json"
            st.download_button(
                label=t("session_download", current_lang),
                data=serialize_session_bundle(bundle),
                file_name=filename,
                mime="application/json",
                use_container_width=True,
            )

        uploaded = st.file_uploader(
            t("session_import_label", current_lang),
            type=["json"],
            key=upload_key,
            help=t("session_import_help", current_lang),
        )
        if st.button(
            t("session_import_button", current_lang),
            key=f"session_import_button_{st.session_state.memory_import_revision}",
            use_container_width=True,
        ):
            if uploaded is None:
                st.warning(t("session_import_missing", current_lang))
                return

            try:
                imported = load_chat_service().import_session_bundle(
                    uploaded.getvalue(),
                    ui_language=current_lang,
                )
            except ValueError as exc:
                st.error(f"{t('session_import_error', current_lang)} {exc}")
                return

            _apply_imported_session(imported, current_lang)
            st.toast(t("session_import_success", st.session_state.lang))
            st.rerun()


def _render_profile_sidebar(current_lang: str) -> None:
    session_id = st.session_state.session_id
    snapshot = load_chat_service().get_session_snapshot(session_id) if session_id else None
    profile = build_session_profile_view(snapshot, ui_language=current_lang)

    with st.sidebar:
        st.markdown(
            "<div class='sidebar-shell'>"
            f"<div class='sidebar-kicker'>{html_lib.escape(t('sidebar_kicker', current_lang))}</div>"
            f"<div class='sidebar-title'>{html_lib.escape(t('sidebar_title', current_lang))}</div>"
            f"<div class='sidebar-note'>{html_lib.escape(t('sidebar_note', current_lang))}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        if not profile.has_content:
            st.markdown(
                f"<div class='sidebar-empty'>{html_lib.escape(t('sidebar_empty', current_lang))}</div>",
                unsafe_allow_html=True,
            )
        else:
            recognized_facts = getattr(
                profile,
                "recognized_facts",
                getattr(profile, "identity_labels", ()),
            )
            profile_preview = t("sidebar_profile_pending", current_lang)
            if recognized_facts:
                preview_items = list(recognized_facts[:3])
                if len(recognized_facts) > 3:
                    preview_items.append(f"+{len(recognized_facts) - 3}")
                profile_preview = " · ".join(preview_items)
            stats = [
                (t("sidebar_stat_profile", current_lang), profile_preview),
                (
                    t("sidebar_stat_language", current_lang),
                    profile.response_language_label or current_lang.upper(),
                ),
                (t("sidebar_stat_messages", current_lang), str(profile.message_count)),
            ]
            _render_sidebar_stats(stats)

            if profile.crisis_detected:
                st.markdown(
                    f"<div class='sidebar-alert'>{html_lib.escape(t('sidebar_crisis_note', current_lang))}</div>",
                    unsafe_allow_html=True,
                )

            if profile.topic_labels:
                _render_sidebar_section_label(t("sidebar_section_focus", current_lang))
                _render_sidebar_chip_list(profile.topic_labels)
                st.markdown("<div class='sidebar-gap'></div>", unsafe_allow_html=True)

            if profile.goal_summaries:
                with st.expander(
                    t("sidebar_section_goals", current_lang),
                    expanded=False,
                    icon=":material/question_answer:",
                ):
                    _render_sidebar_list(profile.goal_summaries)

            conversation_summary_points = getattr(profile, "conversation_summary_points", ())
            if conversation_summary_points:
                with st.expander(
                    t("sidebar_section_summary", current_lang),
                    expanded=False,
                    icon=":material/notes:",
                ):
                    _render_sidebar_list(conversation_summary_points)

            if profile.cited_sources:
                with st.expander(
                    t("sidebar_section_sources", current_lang),
                    expanded=False,
                    icon=":material/library_books:",
                ):
                    _render_sidebar_sources(profile.cited_sources, current_lang)

        st.markdown("<div class='sidebar-gap'></div>", unsafe_allow_html=True)
        _render_session_portability(current_lang, session_id)


def get_response_stream(
    user_message: str,
    *,
    session_id: str | None,
    ui_lang: str = "de",
):
    """
    Streaming wrapper around the shared chat service.

    Yields text chunks first and finishes with a ``ChatTurnResult`` so the
    caller can render progressively and still capture the structured metadata.
    """
    yield from load_chat_service().respond_stream(
        user_message,
        session_id=session_id,
        ui_language=ui_lang,
    )


def _safe_user(text: str) -> str:
    """Escape HTML for user-supplied bubble text (plain text, no markdown)."""
    return html_lib.escape(text)


def _paragraph_block(text: str, css_class: str) -> str:
    """Render plain text as a paragraph block with consistent styling hooks."""

    paragraphs = [html_lib.escape(part.strip()) for part in text.split("\n\n") if part.strip()]
    body = "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    return f"<div class='{css_class}'>{body}</div>"


def _normalize_assistant_markdown(text: str) -> str:
    """Repair common markdown formatting issues before rendering assistant text."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\\n", "\n")
    # Assistant emphasis markers are often malformed in streamed output and can
    # cause large sections to render bold. Keep the text, drop the markers.
    normalized = normalized.replace("**", "").replace("__", "")

    normalized = re.sub(r"\s*---\s*", "\n\n---\n\n", normalized)
    normalized = re.sub(r"([:.;!?])\s+(#{1,6}\s+)", r"\1\n\n\2", normalized)
    normalized = re.sub(r"---\s+(#{1,6}\s+)", r"---\n\n\1", normalized)

    repaired_lines: list[str] = []
    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            repaired_lines.append("")
            continue

        if re.match(r"^\d+\.\s", line) and " - " in line:
            line = re.sub(r"\s-\s+(?=[A-ZÄÖÜ])", "\n   - ", line)
        elif not line.startswith("- ") and (
            "? - " in line or ": - " in line or line.count(" - ") >= 2
        ):
            line = re.sub(r"\s-\s+(?=[A-ZÄÖÜ])", "\n- ", line)

        repaired_lines.append(line)

    normalized = "\n".join(repaired_lines)
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _stream_markdown_response(stream) -> tuple[str, ChatTurnResult | None]:
    """Render streamed assistant chunks as markdown instead of plain text."""

    content_placeholder = st.empty()
    chunks: list[str] = []
    result: ChatTurnResult | None = None

    for item in stream:
        if isinstance(item, ChatTurnResult):
            result = item
            continue

        chunks.append(item)
        content_placeholder.markdown(_normalize_assistant_markdown("".join(chunks)))

    full_text = _normalize_assistant_markdown("".join(chunks))
    if full_text:
        content_placeholder.markdown(full_text)

    return full_text, result


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


_render_profile_sidebar(lang)


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

    st.markdown(_paragraph_block(t("welcome_body", lang), "welcome-copy"), unsafe_allow_html=True)

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
            st.markdown(_normalize_assistant_markdown(msg["content"]))
            _render_provenance_block(msg.get("provenance"), lang)


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
    # Render markdown progressively via a placeholder so formatting survives
    # during the live response, not only after the rerun from chat history.
    stream = get_response_stream(
        user_input,
        session_id=st.session_state.session_id,
        ui_lang=lang,
    )

    label_placeholder = None
    provenance_placeholder = None

    with st.chat_message("assistant", avatar="\U0001f9ed"):
        label_placeholder = st.empty()
        provenance_placeholder = st.empty()
        full_text, result = _stream_markdown_response(stream)

    if result is None:
        result = ChatTurnResult(
            session_id=st.session_state.session_id or "",
            response=full_text,
            agent="COMPASS",
            crisis=False,
            provenance=ResponseProvenance(
                mode="model",
                source_registry_used=False,
                web_grounding_used=False,
                sources=(),
            ),
        )

    st.session_state.session_id = result.session_id or st.session_state.session_id
    display_response = _normalize_assistant_markdown(result.response)
    agent_label = get_agent_label(result.agent, lang)
    if label_placeholder:
        label_placeholder.caption(agent_label)
    if provenance_placeholder:
        _render_provenance_block(result.provenance, lang, provenance_placeholder)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": display_response,
            "agent": result.agent,
            "provenance": result.provenance.model_dump(),
        }
    )

    # Rerun so the script executes top-to-bottom with the fully-updated
    # message list.  Without this, _render_quick_actions() and the reset
    # button were already committed to the page before the new messages
    # were appended — making them invisible until the next user interaction
    # (e.g. a language switch) happened to trigger its own st.rerun().
    st.rerun()


# ── Footer ─────────────────────────────────────────────

st.divider()
footer_text = t("footer", lang)
st.markdown(_paragraph_block(footer_text, "footer-copy"), unsafe_allow_html=True)

st.write("")
st.write("")

st.markdown(
    f"""<div class="ai-disclaimer">{html_lib.escape(t("ai_disclaimer", lang))}</div>""",
    unsafe_allow_html=True,
)
