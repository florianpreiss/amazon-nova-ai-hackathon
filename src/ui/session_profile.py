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
_MAX_PROFILE_FACT_LENGTH = 88
_AGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bich bin\s+(\d{1,2})\b"),
    re.compile(r"\bi am\s+(\d{1,2})\b"),
)


@dataclass(frozen=True)
class SessionProfileView:
    """Sidebar-friendly summary of the active in-session memory."""

    message_count: int = 0
    current_agent: str | None = None
    response_language_label: str | None = None
    topic_labels: tuple[str, ...] = ()
    goal_summaries: tuple[str, ...] = ()
    profile_summary_text: str | None = None
    recognized_facts: tuple[str, ...] = ()
    conversation_summary_points: tuple[str, ...] = ()
    document_labels: tuple[str, ...] = ()
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
                self.profile_summary_text,
                self.recognized_facts,
                self.conversation_summary_points,
                self.document_labels,
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


def _clean_profile_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" -:;,.")
    return _ensure_terminal_punctuation(cleaned) if cleaned else ""


def _truncate_profile_fact(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" -:;,.")
    if len(cleaned) <= _MAX_PROFILE_FACT_LENGTH:
        return cleaned
    return cleaned[: _MAX_PROFILE_FACT_LENGTH - 1].rstrip() + "..."


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
    onboarding_profile_facts: tuple[str, ...],
    contextual_facts: tuple[str, ...],
    structured_facts: tuple[str, ...],
) -> tuple[str, ...]:
    if summary_profile_facts:
        return _dedupe_facts(summary_profile_facts)

    if onboarding_profile_facts:
        return _dedupe_facts((*onboarding_profile_facts, *contextual_facts, *structured_facts))

    return _dedupe_facts((*contextual_facts, *structured_facts))


def _dedupe_facts(facts: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    seen: set[str] = set()
    for fact in facts:
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
        return f"Bisher tauchen vor allem diese Themen auf: {preview}."
    return f"So far, the conversation is mainly about {preview}."


def _format_identity_sentence(identity_labels: tuple[str, ...], *, ui_language: str) -> str | None:
    if not identity_labels:
        return None
    preview = ", ".join(identity_labels[:3])
    if ui_language == "de":
        return f"Wichtiger Hintergrund aus dem Gespräch: {preview}."
    return f"Important context from the chat: {preview}."


def _format_goal_sentence(goals: tuple[str, ...], *, ui_language: str) -> str | None:
    if not goals:
        return None
    latest_goal = _clean_goal_text(goals[0])
    if not latest_goal:
        return None
    if ui_language == "de":
        return f"Als Nächstes suchst du vor allem Orientierung zu: {_ensure_terminal_punctuation(latest_goal)}"
    return f"Your current focus is: {_ensure_terminal_punctuation(latest_goal)}"


def _build_onboarding_summary_points(
    profile_summary: str | None,
    *,
    ui_language: str,
) -> tuple[str, ...]:
    fields = _parse_onboarding_profile_fields(profile_summary)
    if not fields:
        return ()

    points: list[str] = []
    situation = fields.get("situation")
    concern = fields.get("main_concern")
    context = fields.get("context")

    if situation:
        if ui_language == "de":
            points.append(
                f"Deine aktuelle Situation: {_ensure_terminal_punctuation(situation.strip())}"
            )
        else:
            points.append(
                f"Your current situation: {_ensure_terminal_punctuation(situation.strip())}"
            )

    if concern:
        if ui_language == "de":
            points.append(
                f"Gerade besonders wichtig für dich: {_ensure_terminal_punctuation(concern.strip())}"
            )
        else:
            points.append(
                f"Especially important for you right now: {_ensure_terminal_punctuation(concern.strip())}"
            )

    if context:
        if ui_language == "de":
            points.append(
                f"Relevanter Hintergrund aus dem Gespräch: {_ensure_terminal_punctuation(context.strip())}"
            )
        else:
            points.append(
                f"Relevant background from the conversation: {_ensure_terminal_punctuation(context.strip())}"
            )

    return tuple(points[:_MAX_SUMMARY_POINTS])


def _build_contextual_facts(goals: tuple[str, ...], *, ui_language: str) -> tuple[str, ...]:
    if not goals:
        return ()

    text = " ".join(goals).casefold()
    facts: list[str] = []

    age = _extract_age(text)
    if age is not None:
        if ui_language == "de":
            facts.append(f"{age} Jahre alt")
        else:
            facts.append(f"{age} years old")

    if _mentions_school_stage(text):
        if ui_language == "de":
            facts.append("Noch in der Schule")
        else:
            facts.append("Still in school")

    if _mentions_abitur(text):
        if ui_language == "de":
            facts.append("Abi steht bald an")
        else:
            facts.append("Finishing school soon")

    if _mentions_study_interest(text):
        if ui_language == "de":
            facts.append("Interesse am Studium")
        else:
            facts.append("Interested in studying")

    return tuple(facts)


def _extract_age(text: str) -> int | None:
    for pattern in _AGE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        age = int(match.group(1))
        if 13 <= age <= 99:
            return age
    return None


def _parse_onboarding_profile_fields(profile_summary: str | None) -> dict[str, str]:
    if not profile_summary:
        return {}

    fields: dict[str, str] = {}
    for raw_line in profile_summary.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().casefold()
        value = value.strip()
        if key and value:
            fields[key] = value
    return fields


def _format_profile_summary_text(profile_summary: str | None) -> str | None:
    if not profile_summary:
        return None

    fields = _parse_onboarding_profile_fields(profile_summary)
    if not fields:
        cleaned = re.sub(r"\s+", " ", profile_summary).strip()
        return cleaned or None

    parts = [
        _clean_profile_sentence(fields[key])
        for key in ("situation", "main_concern", "context")
        if fields.get(key)
    ]
    formatted = " ".join(part for part in parts if part).strip()
    return formatted or None


def _build_onboarding_profile_facts(profile_summary: str | None) -> tuple[str, ...]:
    fields = _parse_onboarding_profile_fields(profile_summary)
    if not fields:
        return ()

    facts: list[str] = []
    for key in ("situation", "main_concern", "context"):
        value = fields.get(key)
        if not value:
            continue
        fact = _truncate_profile_fact(value)
        if fact:
            facts.append(fact)
    return tuple(facts)


def _mentions_school_stage(text: str) -> bool:
    return any(
        token in text
        for token in (
            "noch in der schule",
            "bin in der schule",
            "school",
            "high school",
            "secondary school",
            "gymnasium",
        )
    )


def _mentions_abitur(text: str) -> bool:
    return any(token in text for token in ("abi", "abitur", "a-level", "a levels"))


def _mentions_study_interest(text: str) -> bool:
    return any(
        token in text
        for token in (
            "interessiere mich fürs studium",
            "interessiere mich fuer studium",
            "interessiere mich für studium",
            "interessiere mich für ein studium",
            "interessiere mich fuer ein studium",
            "studieren",
            "studium",
            "interested in studying",
            "interested in university",
            "thinking about studying",
            "want to study",
        )
    )


def _build_conversation_summary_points(
    *,
    profile_summary: str | None,
    topic_labels: tuple[str, ...],
    goal_summaries: tuple[str, ...],
    recognized_facts: tuple[str, ...],
    summary_points: tuple[str, ...],
    ui_language: str,
) -> tuple[str, ...]:
    if summary_points:
        return summary_points[:_MAX_SUMMARY_POINTS]

    onboarding_points = _build_onboarding_summary_points(
        profile_summary,
        ui_language=ui_language,
    )
    if onboarding_points:
        extra_points: list[str] = list(onboarding_points)
        goal_sentence = _format_goal_sentence(goal_summaries, ui_language=ui_language)
        if goal_sentence:
            extra_points.append(goal_sentence)
        return tuple(extra_points[:_MAX_SUMMARY_POINTS])

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
    total_message_count = snapshot.message_count + len(snapshot.onboarding_messages)
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
    contextual_facts = _build_contextual_facts(snapshot.active_goals, ui_language=language)
    summary_profile_facts = tuple(
        str(item).strip() for item in snapshot.profile_facts if str(item).strip()
    )
    onboarding_profile_facts = _build_onboarding_profile_facts(snapshot.profile_summary)
    recognized_facts = _merge_recognized_facts(
        summary_profile_facts=summary_profile_facts,
        onboarding_profile_facts=onboarding_profile_facts,
        contextual_facts=contextual_facts,
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
    document_labels = tuple(document.display_label for document in snapshot.document_memories[-5:])

    return SessionProfileView(
        message_count=total_message_count,
        current_agent=snapshot.current_agent,
        response_language_label=response_language_label,
        topic_labels=topic_labels,
        goal_summaries=goal_summaries,
        profile_summary_text=_format_profile_summary_text(snapshot.profile_summary),
        recognized_facts=recognized_facts,
        conversation_summary_points=_build_conversation_summary_points(
            profile_summary=snapshot.profile_summary,
            topic_labels=topic_labels,
            goal_summaries=goal_summaries,
            recognized_facts=recognized_facts,
            summary_points=summary_points,
            ui_language=language,
        ),
        document_labels=document_labels,
        cited_sources=cited_sources,
        crisis_detected=snapshot.crisis_detected,
    )
