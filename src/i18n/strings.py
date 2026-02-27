"""
UI string translations.

Agents already respond in the user's language (auto-detect via BaseAgent).
This module handles the STATIC UI elements: buttons, labels, welcome text.
"""

STRINGS = {
    "en": {
        "title": "KODA",
        "subtitle": "You've arrived. And you're not alone.",
        "welcome_stat_left": "out of 100 non-academic children start university",
        "welcome_stat_right": "out of 100 academic children start university",
        "welcome_body": "KODA is your AI companion for navigating higher education.\n\nNo question is too basic. Nobody explains this automatically.",
        "input_placeholder": "Ask KODA anything about studying, finances, or university life...",
        "quick_bafoeg": "💰 What is BAföG?",
        "quick_study": "🎓 Study or apprenticeship?",
        "quick_overwhelmed": "😟 I feel overwhelmed",
        "quick_ects": "📖 What is ECTS?",
        "quick_scholarships": "🔍 Find scholarships",
        "quick_rolemodels": "⭐ Role models",
        "thinking": "KODA is thinking...",
        "crisis_banner": "I notice you may be going through a difficult time. Here are immediate resources:",
        "footer": "KODA provides orientation, not legal or financial advice.\n\nNo data is stored. Your session is private and ephemeral.",
        "lang_toggle": "🇩🇪 Deutsch",
    },
    "de": {
        "title": "KODA",
        "subtitle": "Du bist angekommen. Und du bist nicht allein.",
        "welcome_stat_left": "von 100 Nicht-Akademikerkindern beginnen ein Studium",
        "welcome_stat_right": "von 100 Akademikerkindern beginnen ein Studium",
        "welcome_body": "KODA ist dein KI-Begleiter für den Weg ins Studium.\n\nKeine Frage ist zu einfach. Niemand erklärt das automatisch.",
        "input_placeholder": "Frag KODA alles über Studium, Finanzierung oder Uni-Leben...",
        "quick_bafoeg": "💰 Was ist BAföG?",
        "quick_study": "🎓 Studium oder Ausbildung?",
        "quick_overwhelmed": "😟 Ich fühle mich überfordert",
        "quick_ects": "📖 Was bedeutet ECTS?",
        "quick_scholarships": "🔍 Stipendien finden",
        "quick_rolemodels": "⭐ Vorbilder",
        "thinking": "KODA denkt nach...",
        "crisis_banner": "Ich merke, dass es dir gerade nicht gut geht. Hier sind sofortige Anlaufstellen:",
        "footer": "KODA bietet Orientierung, keine Rechts- oder Finanzberatung.\n\nEs werden keine Daten gespeichert. Deine Sitzung ist privat.",
        "lang_toggle": "🇬🇧 English",
    },
}


DEFAULT_LANGUAGE = "en"
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
