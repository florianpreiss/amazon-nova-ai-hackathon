"""Helpers for adaptive quick-action suggestions in the Streamlit app."""

from __future__ import annotations

from src.core.conversation import PersonalizedPrompt, SessionMemorySnapshot

_FINANCING_TOPICS = {"BAfoeG", "scholarships", "semester fees", "financing"}
_STUDY_CHOICE_TOPICS = {
    "study choice",
    "general guidance",
    "Ausbildung",
    "dual study",
}
_ACADEMIC_TOPICS = {"ECTS", "applications", "deadlines", "module handbook", "academic basics"}
_SUPPORT_TOPICS = {"self-doubt", "role models"}
_MAX_PROMPTS = 6


def build_quick_action_prompts(
    snapshot: SessionMemorySnapshot | None,
    *,
    ui_language: str,
    limit: int = _MAX_PROMPTS,
) -> tuple[PersonalizedPrompt, ...]:
    """Build adaptive quick-action prompts from the current session memory."""

    if snapshot is None:
        return ()

    prompts: list[PersonalizedPrompt] = []
    latest_goal = _latest_goal(snapshot)
    latest_topic = snapshot.topics[-1] if snapshot.topics else None
    current_agent = snapshot.current_agent or ""

    if latest_goal:
        prompts.append(
            _prompt(
                label_de="Nächster Schritt",
                message_de=f"Was ist für mich jetzt der beste nächste Schritt in Bezug auf: {latest_goal}?",
                label_en="Next step",
                message_en=f"What is the best next step for me regarding: {latest_goal}?",
                ui_language=ui_language,
            )
        )

    prompts.extend(
        _topic_prompts(
            latest_topic=latest_topic,
            current_agent=current_agent,
            ui_language=ui_language,
        )
    )

    for prompt in snapshot.personalized_prompts:
        prompts.append(prompt)

    if latest_goal:
        prompts.append(
            _prompt(
                label_de="Offene Fragen",
                message_de=(
                    f"Kannst du meine offenen Fragen zu '{latest_goal}' kurz ordnen "
                    "und sagen, womit ich anfangen sollte?"
                ),
                label_en="Open questions",
                message_en=(
                    f"Can you briefly organize my open questions about '{latest_goal}' "
                    "and tell me what I should start with?"
                ),
                ui_language=ui_language,
            )
        )

    deduped: list[PersonalizedPrompt] = []
    seen: set[str] = set()
    for prompt in prompts:
        key = f"{prompt.label.casefold()}::{prompt.message.casefold()}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(prompt)

    return tuple(deduped[:limit])


def _latest_goal(snapshot: SessionMemorySnapshot) -> str | None:
    if not snapshot.active_goals:
        return None
    latest = str(snapshot.active_goals[-1]).strip()
    return latest or None


def _topic_prompts(
    *,
    latest_topic: str | None,
    current_agent: str,
    ui_language: str,
) -> tuple[PersonalizedPrompt, ...]:
    if latest_topic in _FINANCING_TOPICS or current_agent == "FINANCING":
        return (
            _prompt(
                label_de="Finanzcheck",
                message_de="Welche Finanzierungsmöglichkeiten sind für meine Situation gerade realistisch?",
                label_en="Funding check",
                message_en="Which funding options are realistic for my situation right now?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Stipendien",
                message_de="Welche Stipendien oder Zuschüsse passen gerade am besten zu meiner Situation?",
                label_en="Scholarships",
                message_en="Which scholarships or grants fit my situation best right now?",
                ui_language=ui_language,
            ),
        )

    if latest_topic in _STUDY_CHOICE_TOPICS or current_agent in {"STUDY_CHOICE", "COMPASS"}:
        return (
            _prompt(
                label_de="Optionen prüfen",
                message_de=(
                    "Kannst du mit mir vergleichen, ob Studium, Ausbildung oder "
                    "duales Studium gerade besser zu mir passt?"
                ),
                label_en="Compare paths",
                message_en=(
                    "Can you compare whether university, an apprenticeship, or a "
                    "dual study path fits me better right now?"
                ),
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Interessen klären",
                message_de=(
                    "Wie finde ich heraus, welche Studienfelder oder Berufsrichtungen "
                    "wirklich zu mir passen?"
                ),
                label_en="Clarify interests",
                message_en=(
                    "How can I find out which study fields or career directions actually fit me?"
                ),
                ui_language=ui_language,
            ),
        )

    if latest_topic in _ACADEMIC_TOPICS or current_agent == "ACADEMIC_BASICS":
        focus = latest_topic or ("Uni-Grundlagen" if ui_language == "de" else "academic basics")
        return (
            _prompt(
                label_de="Einfach erklärt",
                message_de=f"Kannst du mir {focus} in einfachen Worten erklären und sagen, was jetzt wichtig ist?",
                label_en="Explain simply",
                message_en=f"Can you explain {focus} in simple words and tell me what matters right now?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Wichtigstes",
                message_de=f"Was sind die wichtigsten Punkte, die ich zu {focus} jetzt verstehen sollte?",
                label_en="Key points",
                message_en=f"What are the most important things I should understand about {focus} right now?",
                ui_language=ui_language,
            ),
        )

    if latest_topic in _SUPPORT_TOPICS or current_agent == "ROLE_MODELS":
        return (
            _prompt(
                label_de="Mutmacher",
                message_de="Kannst du mir Vorbilder oder Geschichten von Menschen mit ähnlichem Hintergrund zeigen?",
                label_en="Role models",
                message_en="Can you show me role models or stories from people with a similar background?",
                ui_language=ui_language,
            ),
            _prompt(
                label_de="Zweifel ordnen",
                message_de="Wie kann ich mit meinen Zweifeln umgehen, ohne vorschnell aufzugeben?",
                label_en="Handle doubts",
                message_en="How can I deal with my doubts without giving up too quickly?",
                ui_language=ui_language,
            ),
        )

    return ()


def _prompt(
    *,
    label_de: str,
    message_de: str,
    label_en: str,
    message_en: str,
    ui_language: str,
) -> PersonalizedPrompt:
    if ui_language == "de":
        return PersonalizedPrompt(label=label_de, message=message_de)
    return PersonalizedPrompt(label=label_en, message=message_en)
