"""View-model helpers for the Streamlit session profile sidebar."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.core.conversation import SessionMemorySnapshot
from src.core.provenance import SourceAttribution

_SUPPORTED_LANGUAGES = {"de", "en"}

_TOPIC_LABELS = {
    "de": {
        "BAfoeG": "BAföG",
        "scholarships": "Stipendien",
        "ECTS": "ECTS",
        "applications": "Bewerbungen",
        "deadlines": "Fristen",
        "semester fees": "Semesterbeitrag",
        "Ausbildung": "Ausbildung",
        "dual study": "Duales Studium",
        "module handbook": "Modulhandbuch",
        "self-doubt": "Selbstzweifel",
        "general guidance": "Orientierung",
        "financing": "Finanzierung",
        "study choice": "Studienwahl",
        "academic basics": "Uni-Grundlagen",
        "role models": "Vorbilder",
    },
    "en": {
        "BAfoeG": "BAfoeG",
        "scholarships": "Scholarships",
        "ECTS": "ECTS",
        "applications": "Applications",
        "deadlines": "Deadlines",
        "semester fees": "Semester fees",
        "Ausbildung": "Apprenticeships",
        "dual study": "Dual study",
        "module handbook": "Module handbook",
        "self-doubt": "Self-doubt",
        "general guidance": "General guidance",
        "financing": "Financing",
        "study choice": "Study choice",
        "academic basics": "Academic basics",
        "role models": "Role models",
    },
}

_IDENTITY_LABELS = {
    "de": {
        "first_generation_student": "Erstakademiker*in",
        "international_student": "Internationale*r Studierende*r",
        "working_student": "Arbeitet neben dem Studium",
        "caregiver": "Mit Sorgeverantwortung",
        "financial_stress": "Finanziell unter Druck",
    },
    "en": {
        "first_generation_student": "First-generation student",
        "international_student": "International student",
        "working_student": "Working alongside studies",
        "caregiver": "Caregiver",
        "financial_stress": "Financial stress",
    },
}

_IDENTITY_ORDER = (
    "first_generation_student",
    "international_student",
    "working_student",
    "caregiver",
    "financial_stress",
)

_LANGUAGE_LABELS = {
    "de": {"de": "Deutsch", "en": "Englisch"},
    "en": {"de": "German", "en": "English"},
}
_MAX_SUMMARY_POINTS = 5
_MAX_GOAL_LENGTH = 180


@dataclass(frozen=True)
class SessionProfileView:
    """Sidebar-friendly summary of the active in-session memory."""

    message_count: int = 0
    current_agent: str | None = None
    response_language_label: str | None = None
    topic_labels: tuple[str, ...] = ()
    goal_summaries: tuple[str, ...] = ()
    recognized_facts: tuple[str, ...] = ()
    conversation_summary_points: tuple[str, ...] = ()
    cited_sources: tuple[SourceAttribution, ...] = ()
    crisis_detected: bool = False

    @property
    def identity_labels(self) -> tuple[str, ...]:
        """Backward-compatible alias for older sidebar code paths."""

        return self.recognized_facts

    @property
    def has_content(self) -> bool:
        return any(
            (
                self.message_count,
                self.current_agent,
                self.response_language_label,
                self.topic_labels,
                self.goal_summaries,
                self.recognized_facts,
                self.conversation_summary_points,
                self.cited_sources,
                self.crisis_detected,
            )
        )


def _normalize_language(ui_language: str) -> str:
    return ui_language if ui_language in _SUPPORTED_LANGUAGES else "en"


def _localize_topic(topic: str, *, ui_language: str) -> str:
    language = _normalize_language(ui_language)
    return _TOPIC_LABELS[language].get(topic, topic)


def _localize_identity(identity_key: str, *, ui_language: str) -> str:
    language = _normalize_language(ui_language)
    return _IDENTITY_LABELS[language].get(
        identity_key,
        identity_key.replace("_", " ").strip().title(),
    )


def _clean_goal_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"^(\d+\.\s+|[-*•]\s+)", "", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:;,.")
    if len(cleaned) > _MAX_GOAL_LENGTH:
        cleaned = cleaned[: _MAX_GOAL_LENGTH - 1].rstrip() + "..."
    return cleaned


def _ensure_terminal_punctuation(text: str) -> str:
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _format_work_hours_label(hours: str, *, ui_language: str) -> str:
    if ui_language == "de":
        return f"Arbeitet etwa {hours}/Woche"
    return f"Works about {hours}/week"


def _build_identity_labels(
    identity_context: dict[str, bool | str], *, ui_language: str
) -> tuple[str, ...]:
    labels: list[str] = []
    has_work_hours = isinstance(identity_context.get("weekly_work_hours"), str)

    for key in _IDENTITY_ORDER:
        value = identity_context.get(key)
        if not value:
            continue
        if key == "working_student" and has_work_hours:
            continue
        labels.append(_localize_identity(key, ui_language=ui_language))

    work_hours = identity_context.get("weekly_work_hours")
    if isinstance(work_hours, str) and work_hours:
        labels.append(_format_work_hours_label(work_hours, ui_language=ui_language))

    return tuple(labels)


def _merge_recognized_facts(
    *,
    summary_profile_facts: tuple[str, ...],
    structured_facts: tuple[str, ...],
) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for fact in (*summary_profile_facts, *structured_facts):
        normalized = _normalize_fact_for_dedupe(fact)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(fact)
    return tuple(deduped)


def _normalize_fact_for_dedupe(text: str) -> str:
    normalized = text.casefold().replace("*", "")
    for filler in (" etwa ", " about ", " circa ", " ca. ", " ca "):
        normalized = normalized.replace(filler, " ")
    normalized = re.sub(r"[^a-z0-9äöüß]+", "", normalized)
    return normalized.strip()


def _format_topic_sentence(topic_labels: tuple[str, ...], *, ui_language: str) -> str | None:
    if not topic_labels:
        return None
    preview = ", ".join(topic_labels[:3])
    if ui_language == "de":
        return f"Im Gespräch geht es bisher vor allem um {preview}."
    return f"So far, the conversation is mainly about {preview}."


def _format_identity_sentence(identity_labels: tuple[str, ...], *, ui_language: str) -> str | None:
    if not identity_labels:
        return None
    preview = ", ".join(identity_labels[:3])
    if ui_language == "de":
        return f"Wichtiger Kontext aus dem Gespräch: {preview}."
    return f"Important context from the chat: {preview}."


def _format_goal_sentence(goals: tuple[str, ...], *, ui_language: str) -> str | None:
    if not goals:
        return None
    latest_goal = _clean_goal_text(goals[0])
    if not latest_goal:
        return None
    if ui_language == "de":
        return f"Dein aktuelles Anliegen ist: {_ensure_terminal_punctuation(latest_goal)}"
    return f"Your current focus is: {_ensure_terminal_punctuation(latest_goal)}"


def _build_conversation_summary_points(
    *,
    topic_labels: tuple[str, ...],
    goal_summaries: tuple[str, ...],
    recognized_facts: tuple[str, ...],
    summary_points: tuple[str, ...],
    ui_language: str,
) -> tuple[str, ...]:
    if summary_points:
        return summary_points[:_MAX_SUMMARY_POINTS]

    candidates = (
        _format_identity_sentence(recognized_facts, ui_language=ui_language),
        _format_topic_sentence(topic_labels, ui_language=ui_language),
        _format_goal_sentence(goal_summaries, ui_language=ui_language),
    )
    points = [item for item in candidates if item]
    return tuple(points[:_MAX_SUMMARY_POINTS])


def build_session_profile_view(
    snapshot: SessionMemorySnapshot | None,
    *,
    ui_language: str,
    goal_limit: int = 3,
    topic_limit: int = 4,
    source_limit: int | None = None,
) -> SessionProfileView:
    """Convert the raw session snapshot into a sidebar-friendly summary."""

    if snapshot is None:
        return SessionProfileView()

    language = _normalize_language(ui_language)
    response_language = snapshot.preferences.get("response_language")
    response_language_label = None
    if isinstance(response_language, str) and response_language:
        response_language_label = _LANGUAGE_LABELS[language].get(
            response_language, response_language.upper()
        )

    topic_labels = tuple(
        _localize_topic(topic, ui_language=language)
        for topic in reversed(snapshot.topics[-topic_limit:])
    )
    goal_summaries = tuple(reversed(snapshot.active_goals[-goal_limit:]))
    structured_facts = _build_identity_labels(snapshot.identity_context, ui_language=language)
    summary_profile_facts = tuple(
        str(item).strip() for item in snapshot.profile_facts if str(item).strip()
    )
    recognized_facts = _merge_recognized_facts(
        summary_profile_facts=summary_profile_facts,
        structured_facts=structured_facts,
    )
    summary_points = tuple(
        str(item).strip() for item in snapshot.conversation_overview if str(item).strip()
    )
    cited_sources = (
        tuple(reversed(snapshot.cited_sources))
        if source_limit is None
        else tuple(reversed(snapshot.cited_sources[-source_limit:]))
    )

    return SessionProfileView(
        message_count=snapshot.message_count,
        current_agent=snapshot.current_agent,
        response_language_label=response_language_label,
        topic_labels=topic_labels,
        goal_summaries=goal_summaries,
        recognized_facts=recognized_facts,
        conversation_summary_points=_build_conversation_summary_points(
            topic_labels=topic_labels,
            goal_summaries=goal_summaries,
            recognized_facts=recognized_facts,
            summary_points=summary_points,
            ui_language=language,
        ),
        cited_sources=cited_sources,
        crisis_detected=snapshot.crisis_detected,
    )
