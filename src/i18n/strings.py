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
        "provenance_source_registry": "Curated Germany sources",
        "provenance_source_registry_and_web": "Curated Germany sources + web grounding",
        "provenance_web_grounding": "Web-grounded",
        "provenance_model": "AI knowledge",
        "sources_label": "Sources",
        "source_tag_registry": "Registry",
        "source_tag_web_grounding": "Web",
        "quick_actions_label": "Quick questions",
        "quick_actions_heading": "What would you like to explore?",
        "quick_actions_sub": "Pick a topic to get started — or type your own question",
        "reset_chat": "↺  New chat",
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
        "provenance_source_registry": "Kuratiertes Deutschland-Register",
        "provenance_source_registry_and_web": "Kuratiertes Deutschland-Register + Web Grounding",
        "provenance_web_grounding": "Web-grounded",
        "provenance_model": "KI-Wissen",
        "sources_label": "Quellen",
        "source_tag_registry": "Register",
        "source_tag_web_grounding": "Web",
        "quick_actions_label": "Schnellfragen",
        "quick_actions_heading": "Was möchtest du erkunden?",
        "quick_actions_sub": "Wähle ein Thema zum Starten — oder stelle deine eigene Frage",
        "reset_chat": "↺  Neu starten",
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
        "FINANCING": "Finance Advisor",
        "STUDY_CHOICE": "Study Advisor",
        "ACADEMIC_BASICS": "Academic Coach",
        "ROLE_MODELS": "Role Models",
    },
    "de": {
        "COMPASS": "KODA Kompass",
        "CRISIS": "Krisenstützung",
        "FINANCING": "Finanzberater",
        "STUDY_CHOICE": "Studienberater",
        "ACADEMIC_BASICS": "Akademischer Coach",
        "ROLE_MODELS": "Vorbilder",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Get a translated string."""
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


def get_agent_label(agent: str, lang: str = "en") -> str:
    """Get agent label in the specified language."""
    return AGENT_LABELS.get(lang, AGENT_LABELS["en"]).get(agent, agent)
