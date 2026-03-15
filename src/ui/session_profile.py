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
_MAX_SUMMARY_POINTS = 3
_MAX_SUMMARY_LENGTH = 140


@dataclass(frozen=True)
class SessionProfileView:
    """Sidebar-friendly summary of the active in-session memory."""

    message_count: int = 0
    current_agent: str | None = None
    response_language_label: str | None = None
    topic_labels: tuple[str, ...] = ()
    goal_summaries: tuple[str, ...] = ()
    identity_labels: tuple[str, ...] = ()
    answer_summary_points: tuple[str, ...] = ()
    cited_sources: tuple[SourceAttribution, ...] = ()
    crisis_detected: bool = False

    @property
    def has_content(self) -> bool:
        return any(
            (
                self.message_count,
                self.current_agent,
                self.response_language_label,
                self.topic_labels,
                self.goal_summaries,
                self.identity_labels,
                self.answer_summary_points,
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


def _clean_summary_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"^(\d+\.\s+|[-*•]\s+)", "", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:;,.")
    if len(cleaned) > _MAX_SUMMARY_LENGTH:
        cleaned = cleaned[: _MAX_SUMMARY_LENGTH - 1].rstrip() + "..."
    return cleaned


def _extract_answer_summary_points(response_text: str | None) -> tuple[str, ...]:
    if not response_text:
        return ()

    normalized = response_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in normalized.split("\n")]

    bullet_candidates: list[str] = []
    for line in lines:
        if not line or line.startswith("#") or set(line) <= {"-"}:
            continue
        if re.match(r"^(\d+\.\s+|[-*•]\s+)", line):
            cleaned = _clean_summary_text(line)
            if cleaned and cleaned not in bullet_candidates:
                bullet_candidates.append(cleaned)
        if len(bullet_candidates) >= _MAX_SUMMARY_POINTS:
            return tuple(bullet_candidates[:_MAX_SUMMARY_POINTS])

    prose = " ".join(
        line for line in lines if line and not line.startswith("#") and set(line) != {"-"}
    )
    prose = prose.replace("**", "").replace("__", "")
    sentence_candidates: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", prose):
        cleaned = _clean_summary_text(sentence)
        if cleaned and cleaned not in sentence_candidates:
            sentence_candidates.append(cleaned)
        if len(sentence_candidates) >= _MAX_SUMMARY_POINTS:
            break

    return tuple(sentence_candidates[:_MAX_SUMMARY_POINTS])


def build_session_profile_view(
    snapshot: SessionMemorySnapshot | None,
    *,
    ui_language: str,
    latest_assistant_response: str | None = None,
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

    identity_keys = tuple(key for key in _IDENTITY_ORDER if snapshot.identity_context.get(key))
    identity_labels = tuple(_localize_identity(key, ui_language=language) for key in identity_keys)
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
        identity_labels=identity_labels,
        answer_summary_points=_extract_answer_summary_points(latest_assistant_response),
        cited_sources=cited_sources,
        crisis_detected=snapshot.crisis_detected,
    )
