"""
UI string translations.

Agents already respond in the user's language (auto-detect via BaseAgent).
This module handles the STATIC UI elements: buttons, labels, welcome text.
"""

STRINGS = {
    "en": {
        "title": "KODA",
        "subtitle": "You've arrived. And you're not alone.",
        "ai_disclaimer": "AI can make mistakes. For important decisions, check the cited sources and official offices.",
        "welcome_stat_left": "out of 100 non-academic children start university",
        "welcome_stat_right": "out of 100 academic children start university",
        "welcome_body": "KODA is your AI companion for navigating higher education.\n\nNo question is too basic. Nothing is self-explanatory.",
        "input_placeholder": "Ask KODA anything about studying, finances, or university life...",
        "quick_bafoeg": "💰 What is BAföG?",
        "quick_bafoeg_msg": "What is BAföG and how do I apply for it?",
        "quick_study": "🎓 Study or apprenticeship?",
        "quick_study_msg": "How do I decide between university and a vocational apprenticeship?",
        "quick_overwhelmed": "😟 I feel overwhelmed",
        "quick_overwhelmed_msg": "I feel overwhelmed and don't know where to start with university.",
        "quick_ects": "📖 What is ECTS?",
        "quick_ects_msg": "What does ECTS mean and how do credit points work at university?",
        "quick_scholarships": "🔍 Find scholarships",
        "quick_scholarships_msg": "What scholarships are available for first-generation students in Germany?",
        "quick_rolemodels": "⭐ Role models",
        "quick_rolemodels_msg": "Can you show me role models who were the first in their family to study?",
        "thinking": "KODA is thinking...",
        "crisis_banner": "I notice you may be going through a difficult time. Here are immediate resources:",
        "provenance_source_registry": "Verified Sources",
        "provenance_source_registry_and_web": "Verified Sources + Web",
        "provenance_web_grounding": "Web Search",
        "provenance_model": "AI knowledge",
        "provenance_document": "Your document",
        "sources_label": "Sources",
        "source_tag_registry": "Verified",
        "source_tag_web_grounding": "Web",
        "source_tag_document": "Document",
        "quick_actions_label": "Quick questions",
        "quick_actions_heading": "What would you like to explore?",
        "quick_actions_sub": "Pick a topic to get started — or type your own question",
        "sidebar_kicker": "Session memory",
        "sidebar_title": "Temporary profile",
        "sidebar_note": "This summary exists only during the current chat session. Reset any time to clear it.",
        "sidebar_empty": "Start chatting and KODA will summarize your goals, context, and sources here.",
        "sidebar_stat_profile": "Your profile",
        "sidebar_stat_messages": "Chat history",
        "sidebar_stat_language": "Language",
        "sidebar_pending": "Listening",
        "sidebar_profile_pending": "Building up",
        "sidebar_section_focus": "Your interests",
        "sidebar_section_summary": "Conversation summary",
        "sidebar_section_goals": "Your questions so far",
        "sidebar_section_identity": "About you",
        "sidebar_section_documents": "Documents in this session",
        "sidebar_section_sources": "Sources used this session",
        "sidebar_portability": "Save or continue chat",
        "sidebar_portability_note": "Download a chat file or continue from one you saved earlier.",
        "session_download": "Download chat file",
        "session_import_label": "Continue from chat file",
        "session_import_help": "Only upload a JSON file that you previously downloaded from KODA.",
        "session_import_button": "Load session",
        "session_import_missing": "Choose a session file first.",
        "session_import_success": "Session loaded into a new private chat.",
        "session_import_error": "This session file could not be loaded.",
        "sidebar_crisis_note": "KODA noticed that this conversation may need urgent support. Use the crisis resources shown in the chat.",
        "onboarding_pending_title": "Before we begin...",
        "onboarding_pending_body": (
            "KODA can start with a short, gentle onboarding chat so the guidance and "
            "suggested questions fit your situation better."
        ),
        "onboarding_start_btn": "Start onboarding",
        "onboarding_skip_btn": "Skip for now",
        "onboarding_skip_hint": "You can jump straight into the chat if you prefer.",
        "onboarding_input_placeholder": "Your answer...",
        "document_hint": "Optional: use the plus sign in the chat field to upload a document.",
        "document_popover_button": "Documents",
        "document_popover_help": "Supported formats, limits, and privacy note for document uploads.",
        "document_popover_title": "Use documents in chat",
        "document_popover_body": (
            "Attach a document directly in the chat field. KODA can explain it in plain language "
            "and help you understand what matters next."
        ),
        "document_popover_limits": (
            "Supported: PDF, DOCX, TXT, MD, CSV, XLSX. Up to 5 documents per message. "
            "Text files up to 4.5 MB each. Uploaded media documents must stay within 25 MB total."
        ),
        "document_popover_privacy": (
            "Documents are only used in the current session unless you explicitly export your session memory."
        ),
        "document_popover_disclaimer": (
            "AI can make mistakes. Please check important decisions with official offices and cited sources."
        ),
        "document_uploaded_placeholder": "Uploaded document for explanation.",
        "reset_chat": "Restart chat",
        "reset_chat_tooltip": "Clear the conversation and start fresh",
        "footer": "KODA provides orientation, not legal or financial advice.\n\nNo data is stored. Your session is private and ephemeral.",
        "lang_toggle": "🇩🇪 Deutsch",
    },
    "de": {
        "title": "KODA",
        "subtitle": "Du bist angekommen. Und du bist nicht allein.",
        "ai_disclaimer": "KI kann Fehler machen. Bitte prüfe wichtige Informationen mit den zitierten Quellen und offiziellen Stellen.",
        "welcome_stat_left": "von 100 Nicht-Akademikerkindern beginnen ein Studium",
        "welcome_stat_right": "von 100 Akademikerkindern beginnen ein Studium",
        "welcome_body": "KODA ist dein KI-Begleiter für den Weg ins Studium.\n\nKeine Frage ist zu einfach. Nichts erklärt sich von selbst.",
        "input_placeholder": "Frag KODA alles über Studium, Finanzierung oder Uni-Leben...",
        "quick_bafoeg": "💰 Was ist BAföG?",
        "quick_bafoeg_msg": "Was ist BAföG und wie beantrage ich es?",
        "quick_study": "🎓 Studium oder Ausbildung?",
        "quick_study_msg": "Wie entscheide ich mich zwischen Studium und Ausbildung?",
        "quick_overwhelmed": "😟 Ich fühle mich überfordert",
        "quick_overwhelmed_msg": "Ich fühle mich überfordert und weiß nicht, wo ich anfangen soll.",
        "quick_ects": "📖 Was bedeutet ECTS?",
        "quick_ects_msg": "Was bedeutet ECTS und wie funktionieren Leistungspunkte an der Uni?",
        "quick_scholarships": "🔍 Stipendien finden",
        "quick_scholarships_msg": "Welche Stipendien gibt es für Studierende aus Nicht-Akademikerfamilien?",
        "quick_rolemodels": "⭐ Vorbilder",
        "quick_rolemodels_msg": "Zeig mir Vorbilder, die als Erste in ihrer Familie studiert haben.",
        "thinking": "KODA denkt nach...",
        "crisis_banner": "Ich merke, dass es dir gerade nicht gut geht. Hier sind sofortige Anlaufstellen:",
        "provenance_source_registry": "Mit verifizierten Quellen aufbereitet",
        "provenance_source_registry_and_web": "Mit verifizierten Quellen + Web aufbereitet",
        "provenance_web_grounding": "Web-Suche",
        "provenance_model": "KI-Wissen",
        "provenance_document": "Aus deinem Dokument erklärt",
        "sources_label": "Quellen",
        "source_tag_registry": "Geprüft",
        "source_tag_web_grounding": "Web",
        "source_tag_document": "Dokument",
        "quick_actions_label": "Schnellfragen",
        "quick_actions_heading": "Was möchtest du erkunden?",
        "quick_actions_sub": "Wähle ein Thema zum Starten — oder stelle deine eigene Frage",
        "sidebar_kicker": "Sitzungsspeicher",
        "sidebar_title": "Temporäres Profil",
        "sidebar_note": "Diese Zusammenfassung existiert nur in der aktuellen Sitzung. Du kannst sie jederzeit zurücksetzen.",
        "sidebar_empty": "Starte ein Gespräch und KODA fasst hier deine Ziele, deinen Kontext und genutzte Quellen zusammen.",
        "sidebar_stat_profile": "Dein Profil",
        "sidebar_stat_messages": "Chatverlauf",
        "sidebar_stat_language": "Sprache",
        "sidebar_pending": "Hört zu",
        "sidebar_profile_pending": "Im Aufbau",
        "sidebar_section_focus": "Deine Interessengebiete",
        "sidebar_section_summary": "Gesprächszusammenfassung",
        "sidebar_section_goals": "Deine bisherigen Fragen",
        "sidebar_section_identity": "Über dich",
        "sidebar_section_documents": "Dokumente in dieser Sitzung",
        "sidebar_section_sources": "Quellen dieser Sitzung",
        "sidebar_portability": "Chat speichern oder fortsetzen",
        "sidebar_portability_note": "Lade eine Chat-Datei herunter oder setze ein früheres Gespräch mit einer gespeicherten Datei fort.",
        "session_download": "Chat-Datei herunterladen",
        "session_import_label": "Mit Chat-Datei fortsetzen",
        "session_import_help": "Lade nur eine JSON-Datei hoch, die du zuvor von KODA heruntergeladen hast.",
        "session_import_button": "Sitzung laden",
        "session_import_missing": "Wähle zuerst eine Sitzungsdatei aus.",
        "session_import_success": "Sitzung in einen neuen privaten Chat geladen.",
        "session_import_error": "Diese Sitzungsdatei konnte nicht geladen werden.",
        "sidebar_crisis_note": "KODA hat erkannt, dass dieses Gespräch möglicherweise sofortige Unterstützung braucht. Nutze die Hilfsangebote im Chat.",
        "onboarding_pending_title": "Bevor wir starten...",
        "onboarding_pending_body": (
            "KODA kann mit einem kurzen, behutsamen Onboarding beginnen, damit die "
            "Begleitung und die vorgeschlagenen Fragen besser zu deiner Situation passen."
        ),
        "onboarding_start_btn": "Onboarding starten",
        "onboarding_skip_btn": "Vorerst überspringen",
        "onboarding_skip_hint": "Wenn du möchtest, kannst du auch direkt in den Chat gehen.",
        "onboarding_input_placeholder": "Deine Antwort...",
        "document_hint": "Optional: Über das Plus im Chatfeld kannst du ein Dokument hochladen.",
        "document_popover_button": "Dokumente",
        "document_popover_help": "Unterstützte Formate, Limits und Datenschutzhinweis für Dokument-Uploads.",
        "document_popover_title": "Dokumente im Chat nutzen",
        "document_popover_body": (
            "Hänge ein Dokument direkt im Chatfeld an. KODA kann es in einfacher Sprache erklären "
            "und dir sagen, was als Nächstes wichtig ist."
        ),
        "document_popover_limits": (
            "Unterstützt: PDF, DOCX, TXT, MD, CSV, XLSX. Bis zu 5 Dokumente pro Nachricht. "
            "Textdateien bis 4,5 MB pro Datei. Hochgeladene Mediendokumente zusammen bis 25 MB."
        ),
        "document_popover_privacy": (
            "Dokumente werden nur in der aktuellen Sitzung verwendet, außer du exportierst deine Sitzung ausdrücklich."
        ),
        "document_popover_disclaimer": (
            "KI kann Fehler machen. Bitte prüfe wichtige Entscheidungen mit offiziellen Stellen und zitierten Quellen."
        ),
        "document_uploaded_placeholder": "Dokument zur Erklärung hochgeladen.",
        "reset_chat": "Chat neustarten",
        "reset_chat_tooltip": "Gespräch löschen und neu beginnen",
        "footer": "KODA bietet Orientierung, keine Rechts- oder Finanzberatung.\n\nEs werden keine Daten gespeichert. Deine Sitzung ist privat.",
        "lang_toggle": "🇬🇧 English",
    },
}


# Default matches the pill pre-selection in the Streamlit UI ("🇩🇪 Deutsch")
DEFAULT_LANGUAGE = "de"
SUPPORTED_LANGUAGES = ["en", "de"]

AGENT_LABELS = {
    "en": {
        "COMPASS": "KODA Compass",
        "CRISIS": "Crisis Support",
        "FINANCING": "Study Funding",
        "STUDY_CHOICE": "Study Info",
        "ACADEMIC_BASICS": "Academic Coach",
        "ROLE_MODELS": "Role Models",
        "ONBOARDING": "KODA Onboarding",
    },
    "de": {
        "COMPASS": "KODA Kompass",
        "CRISIS": "Krisenstützung",
        "FINANCING": "Studienfinanzierung",
        "STUDY_CHOICE": "Studieninfo",
        "ACADEMIC_BASICS": "Akademischer Coach",
        "ROLE_MODELS": "Vorbilder",
        "ONBOARDING": "KODA Onboarding",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Get a translated string."""
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


def get_agent_label(agent: str, lang: str = "en") -> str:
    """Get agent label in the specified language."""
    return AGENT_LABELS.get(lang, AGENT_LABELS["en"]).get(agent, agent)
