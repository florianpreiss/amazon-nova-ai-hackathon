"""
Ephemeral session memory for the shared chat orchestration.

Sessions live in memory only, expire after inactivity, and are never persisted
automatically. The store keeps both raw turn history and a distilled summary so
agents can follow the conversation without relying on long-term storage.
"""

from __future__ import annotations

import re
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from typing import Any, Literal, cast

from config.settings import SESSION_TIMEOUT_MINUTES
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.documents import DocumentMemory, UploadedDocument
from src.core.provenance import ResponseProvenance, SourceAttribution
from src.core.session_summary import SessionSummary

MAX_SESSION_MESSAGES = 24
MAX_ACTIVE_GOALS = 4
MAX_TOPICS = 6
MAX_ACTIVE_DOCUMENTS = 5
MAX_GOAL_LENGTH = 140
MAX_ONBOARDING_MESSAGES = 12
MAX_PERSONALIZED_PROMPTS = 5
MAX_PROFILE_SUMMARY_LENGTH = 1200
MAX_PROMPT_LABEL_LENGTH = 80
MAX_PROMPT_MESSAGE_LENGTH = 240

_AGENT_TOPIC_LABELS = {
    "COMPASS": "general guidance",
    "FINANCING": "financing",
    "STUDY_CHOICE": "study choice",
    "ACADEMIC_BASICS": "academic basics",
    "ROLE_MODELS": "role models",
}

_TOPIC_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("BAfoeG", ("bafoeg", "bafög", "bafoe", "bafo g")),
    ("scholarships", ("scholarship", "scholarships", "stipendium", "stipendien")),
    ("ECTS", ("ects", "credit points", "leistungspunkte")),
    ("applications", ("application", "apply", "bewerbung", "bewerben")),
    ("deadlines", ("deadline", "frist", "fristen")),
    ("semester fees", ("semesterbeitrag", "semester fee", "semester fees")),
    ("Ausbildung", ("ausbildung", "apprenticeship")),
    ("dual study", ("duales studium", "dual study", "dual degree")),
    ("module handbook", ("modulhandbuch", "module handbook", "study regulations")),
    ("self-doubt", ("impostor", "belong", "ueberfordert", "überfordert", "zweifel")),
)

_IDENTITY_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "first_generation_student",
        (
            "first generation",
            "first-gen",
            "erstakademiker",
            "erstakademikerin",
            "nicht-akademikerkind",
            "non-academic family",
        ),
    ),
    (
        "international_student",
        ("international student", "auslandsstudent", "foreign student", "visa"),
    ),
    (
        "working_student",
        (
            "working student",
            "werkstudent",
            "part-time job",
            "nebenjob",
            "20 hours",
            "20 stunden",
        ),
    ),
    (
        "caregiver",
        ("single parent", "caregiver", "pflege", "betreuung", "childcare", "kids"),
    ),
    (
        "financial_stress",
        (
            "can't afford",
            "cannot afford",
            "money is tight",
            "geldprobleme",
            "geldsorgen",
            "finanzielle probleme",
        ),
    ),
)
_WORK_CONTEXT_KEYWORDS = (
    "arbeite",
    "arbeit",
    "job",
    "nebenjob",
    "werkstudent",
    "work",
    "working",
    "part-time",
    "part time",
)
_WORK_HOURS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(\d{1,2})\s*(?:h|std)\b"),
    re.compile(r"\b(\d{1,2})\s*(?:stunden|hours?|hrs?)\b"),
)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate_text(text: str, *, limit: int = MAX_GOAL_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _truncate_multiline_text(text: str, *, limit: int) -> str:
    normalized = re.sub(r"\r\n?", "\n", text).strip()
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."


def _normalize_content(content: Any) -> list[dict[str, str]]:
    if isinstance(content, list):
        normalized: list[dict[str, str]] = []
        for block in content:
            if not isinstance(block, dict):
                raise TypeError(f"Unsupported content block type: {type(block).__name__}")
            text = _normalize_text(str(block.get("text", "")))
            normalized.append({"text": text})
        return normalized

    if isinstance(content, str):
        return [{"text": _normalize_text(content)}]

    raise TypeError(f"Unsupported message content type: {type(content).__name__}")


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return _normalize_text(content)
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = _normalize_text(str(block.get("text", "")))
                if text:
                    parts.append(text)
        return " ".join(parts)
    raise TypeError(f"Unsupported message content type: {type(content).__name__}")


def _remember_recent(values: list[str], candidate: str, *, limit: int) -> None:
    candidate = _normalize_text(candidate)
    if not candidate:
        return

    deduped = [value for value in values if value.casefold() != candidate.casefold()]
    deduped.append(candidate)
    del values[:]
    values.extend(deduped[-limit:])


def _remember_source(sources: list[SourceAttribution], source: SourceAttribution) -> None:
    source_key = (source.url or f"document::{source.title}").casefold()
    deduped = [
        item for item in sources if (item.url or f"document::{item.title}").casefold() != source_key
    ]
    deduped.append(source)
    del sources[:]
    sources.extend(deduped)


class SessionMemorySnapshot(BaseModel):
    """Structured snapshot of the current in-session memory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    created_at: float
    last_activity: float
    message_count: int
    current_agent: str | None = None
    crisis_detected: bool = False
    topics: tuple[str, ...] = ()
    identity_context: dict[str, bool | str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)
    active_goals: tuple[str, ...] = ()
    cited_sources: tuple[SourceAttribution, ...] = ()
    profile_facts: tuple[str, ...] = ()
    conversation_overview: tuple[str, ...] = ()
    onboarding_state: Literal["pending", "in_progress", "complete", "skipped"] = "pending"
    onboarding_messages: tuple[SessionTextTurn, ...] = ()
    profile_summary: str | None = None
    personalized_prompts: tuple[PersonalizedPrompt, ...] = ()
    document_memories: tuple[DocumentMemory, ...] = ()


class SessionTextTurn(BaseModel):
    """Compact session-owned text turn used for onboarding transcripts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str

    @field_validator("content")
    @classmethod
    def _content_must_not_be_blank(cls, value: str) -> str:
        value = _normalize_text(value)
        if not value:
            raise ValueError("content must not be blank")
        return value


class PersonalizedPrompt(BaseModel):
    """Profile-aware quick action suggested for the current session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    message: str

    @field_validator("label")
    @classmethod
    def _label_must_not_be_blank(cls, value: str) -> str:
        value = _truncate_text(_normalize_text(value), limit=MAX_PROMPT_LABEL_LENGTH)
        if not value:
            raise ValueError("label must not be blank")
        return value

    @field_validator("message")
    @classmethod
    def _message_must_not_be_blank(cls, value: str) -> str:
        value = _truncate_multiline_text(value, limit=MAX_PROMPT_MESSAGE_LENGTH)
        if not value:
            raise ValueError("message must not be blank")
        return value


SessionMemorySnapshot.model_rebuild()


class Conversation:
    """Single in-memory user session."""

    def __init__(
        self,
        *,
        session_id: str | None = None,
        now: Callable[[], float] | None = None,
    ) -> None:
        self.session_id = session_id or str(uuid.uuid4())
        self._now = now or time.time
        self._lock = threading.RLock()

        now_ts = self._now()
        self.created_at = now_ts
        self._last_activity = now_ts
        self.messages: list[dict[str, Any]] = []
        self.current_agent: str | None = None
        self.topics: list[str] = []
        self.identity_context: dict[str, bool | str] = {}
        self.preferences: dict[str, str] = {}
        self.active_goals: list[str] = []
        self.cited_sources: list[SourceAttribution] = []
        self.profile_facts: list[str] = []
        self.conversation_overview: list[str] = []
        self.onboarding_state: Literal["pending", "in_progress", "complete", "skipped"] = "pending"
        self.onboarding_messages: list[SessionTextTurn] = []
        self.profile_summary: str | None = None
        self.personalized_prompts: list[PersonalizedPrompt] = []
        self.document_memories: list[DocumentMemory] = []
        self._active_documents: list[UploadedDocument] = []
        self.crisis_detected = False

    @property
    def metadata(self) -> dict[str, Any]:
        """Return prompt-ready metadata derived from the current session."""

        snapshot = self.snapshot()
        return {
            "current_agent": snapshot.current_agent,
            "topics": list(snapshot.topics),
            "identity_context": dict(snapshot.identity_context),
            "preferences": dict(snapshot.preferences),
            "active_goals": list(snapshot.active_goals),
            "crisis_detected": snapshot.crisis_detected,
            "profile_facts": list(snapshot.profile_facts),
            "conversation_overview": list(snapshot.conversation_overview),
            "onboarding_state": snapshot.onboarding_state,
            "onboarding_messages": [
                message.model_dump(mode="python") for message in snapshot.onboarding_messages
            ],
            "profile_summary": snapshot.profile_summary,
            "personalized_prompts": [
                prompt.model_dump(mode="python") for prompt in snapshot.personalized_prompts
            ],
            "document_memories": [
                document.model_dump(mode="python") for document in snapshot.document_memories
            ],
            "document_context": {
                "remembered": [document.display_label for document in snapshot.document_memories]
            },
            "session_memory": snapshot.model_dump(mode="python"),
        }

    def set_preference(self, key: str, value: str) -> None:
        normalized_key = _normalize_text(key)
        normalized_value = _normalize_text(value)
        if not normalized_key or not normalized_value:
            return

        with self._lock:
            self.preferences[normalized_key] = normalized_value
            self._touch()

    def sync_history(
        self,
        history: list[dict[str, Any]],
        *,
        ui_language: str = "en",
    ) -> None:
        """Replace the current message history with caller-supplied turns."""

        with self._lock:
            self.messages = []
            self.current_agent = None
            self.topics = []
            self.identity_context = {}
            self.active_goals = []
            self.cited_sources = []
            self.profile_facts = []
            self.conversation_overview = []
            self.onboarding_state = "pending"
            self.onboarding_messages = []
            self.profile_summary = None
            self.personalized_prompts = []
            self.document_memories = []
            self._active_documents = []
            self.crisis_detected = False
            self.preferences["response_language"] = ui_language

            for raw_message in history:
                role = str(raw_message.get("role", "user"))
                content = _normalize_content(raw_message.get("content", ""))
                self.messages.append({"role": role, "content": content})
                text = _extract_text(content)

                if role == "user":
                    self._remember_goal(text)
                    self._remember_topics(text)
                    self._remember_identity_signals(text)
                    continue

                agent = raw_message.get("agent")
                if isinstance(agent, str):
                    self.current_agent = agent
                    self._remember_agent_topic(agent)

                provenance = raw_message.get("provenance")
                if provenance is not None:
                    self._remember_sources(_coerce_provenance(provenance))

            self._trim_messages()
            self._touch()

    def set_onboarding_state(
        self,
        state: Literal["pending", "in_progress", "complete", "skipped"],
    ) -> None:
        with self._lock:
            self.onboarding_state = state
            self._touch()

    def add_onboarding_message(
        self,
        role: Literal["user", "assistant"],
        text: str,
    ) -> None:
        normalized = _normalize_text(text)
        if not normalized:
            return

        with self._lock:
            self.onboarding_messages.append(SessionTextTurn(role=role, content=normalized))
            if len(self.onboarding_messages) > MAX_ONBOARDING_MESSAGES:
                self.onboarding_messages = self.onboarding_messages[-MAX_ONBOARDING_MESSAGES:]
            self._touch()

    def set_profile_summary(self, summary: str | None) -> None:
        normalized = _truncate_multiline_text(summary or "", limit=MAX_PROFILE_SUMMARY_LENGTH)
        with self._lock:
            self.profile_summary = normalized or None
            self._touch()

    def set_personalized_prompts(
        self,
        prompts: Sequence[PersonalizedPrompt | dict[str, Any]],
    ) -> None:
        normalized = _coerce_personalized_prompts(prompts)
        with self._lock:
            self.personalized_prompts = list(normalized)
            self._touch()

    def complete_onboarding(
        self,
        *,
        profile_summary: str,
        personalized_prompts: Sequence[PersonalizedPrompt | dict[str, Any]] | None = None,
        ui_language: str | None = None,
    ) -> None:
        with self._lock:
            self.onboarding_state = "complete"
            if ui_language:
                self.preferences["response_language"] = ui_language
            self.profile_summary = (
                _truncate_multiline_text(profile_summary, limit=MAX_PROFILE_SUMMARY_LENGTH) or None
            )
            self.personalized_prompts = list(
                _coerce_personalized_prompts(personalized_prompts or [])
            )
            self._touch()

    def skip_onboarding(self) -> None:
        with self._lock:
            self.onboarding_state = "skipped"
            self._touch()

    def add_user_message(self, text: str, *, ui_language: str = "en") -> None:
        normalized = _normalize_text(text)
        if not normalized:
            return

        with self._lock:
            self.messages.append({"role": "user", "content": [{"text": normalized}]})
            self.preferences["response_language"] = ui_language
            self._remember_goal(normalized)
            self._remember_topics(normalized)
            self._remember_identity_signals(normalized)
            self._trim_messages()
            self._touch()

    def add_assistant_message(
        self,
        text: str,
        *,
        agent_key: str,
        crisis: bool = False,
        provenance: ResponseProvenance | dict[str, Any] | None = None,
    ) -> None:
        normalized = _normalize_text(text)
        if not normalized:
            return

        normalized_provenance = _coerce_provenance(provenance)
        message_payload: dict[str, Any] = {
            "role": "assistant",
            "content": [{"text": normalized}],
            "agent": agent_key,
        }
        if normalized_provenance is not None:
            message_payload["provenance"] = normalized_provenance.model_dump(mode="python")

        with self._lock:
            self.messages.append(message_payload)
            self.current_agent = agent_key
            self.crisis_detected = crisis
            self._remember_agent_topic(agent_key)
            self._remember_sources(normalized_provenance)
            self._trim_messages()
            self._touch()

    def get_messages(self, last_n: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            messages = self.messages[-last_n:] if last_n else self.messages
            copied: list[dict[str, Any]] = []
            for message in messages:
                entry: dict[str, Any] = {
                    "role": message["role"],
                    "content": [dict(block) for block in message["content"]],
                }
                if "agent" in message:
                    entry["agent"] = message["agent"]
                if "provenance" in message:
                    entry["provenance"] = message["provenance"]
                copied.append(entry)
            return copied

    def snapshot(self) -> SessionMemorySnapshot:
        with self._lock:
            return SessionMemorySnapshot(
                session_id=self.session_id,
                created_at=self.created_at,
                last_activity=self._last_activity,
                message_count=len(self.messages),
                current_agent=self.current_agent,
                crisis_detected=self.crisis_detected,
                topics=tuple(self.topics),
                identity_context=dict(self.identity_context),
                preferences=dict(self.preferences),
                active_goals=tuple(self.active_goals),
                cited_sources=tuple(self.cited_sources),
                profile_facts=tuple(self.profile_facts),
                conversation_overview=tuple(self.conversation_overview),
                onboarding_state=self.onboarding_state,
                onboarding_messages=tuple(self.onboarding_messages),
                profile_summary=self.profile_summary,
                personalized_prompts=tuple(self.personalized_prompts),
                document_memories=tuple(self.document_memories),
            )

    def set_active_documents(
        self,
        documents: Sequence[UploadedDocument],
        *,
        summary_text: str | None = None,
    ) -> None:
        with self._lock:
            deduped_documents: list[UploadedDocument] = []
            seen_hashes: set[str] = set()
            for document in documents:
                if document.sha256 in seen_hashes:
                    continue
                seen_hashes.add(document.sha256)
                deduped_documents.append(document)
            self._active_documents = deduped_documents[-MAX_ACTIVE_DOCUMENTS:]

            next_memories: list[DocumentMemory] = [
                memory for memory in self.document_memories if memory.sha256 not in seen_hashes
            ]
            for document in self._active_documents:
                next_memories.append(
                    DocumentMemory(
                        document_id=document.document_id,
                        name=document.name,
                        extension=document.extension,
                        kind=document.kind,
                        size_bytes=document.size_bytes,
                        sha256=document.sha256,
                        summary=summary_text,
                    )
                )
            self.document_memories = next_memories[-MAX_ACTIVE_DOCUMENTS:]
            self._touch()

    def get_active_documents(self) -> tuple[UploadedDocument, ...]:
        with self._lock:
            return tuple(self._active_documents)

    def is_expired(self) -> bool:
        with self._lock:
            elapsed = self._now() - self._last_activity
        timeout_seconds = SESSION_TIMEOUT_MINUTES * 60
        return elapsed > timeout_seconds

    def _remember_goal(self, text: str) -> None:
        cleaned = _truncate_text(_normalize_text(text))
        _remember_recent(self.active_goals, cleaned, limit=MAX_ACTIVE_GOALS)

    def _remember_topics(self, text: str) -> None:
        lowered = text.casefold()
        for topic, keywords in _TOPIC_KEYWORDS:
            if any(keyword in lowered for keyword in keywords):
                _remember_recent(self.topics, topic, limit=MAX_TOPICS)

    def _remember_agent_topic(self, agent_key: str) -> None:
        label = _AGENT_TOPIC_LABELS.get(agent_key)
        if label:
            _remember_recent(self.topics, label, limit=MAX_TOPICS)

    def _remember_identity_signals(self, text: str) -> None:
        lowered = text.casefold()
        for key, patterns in _IDENTITY_PATTERNS:
            if any(pattern in lowered for pattern in patterns):
                self.identity_context[key] = True

        has_work_context = any(keyword in lowered for keyword in _WORK_CONTEXT_KEYWORDS)
        for pattern in _WORK_HOURS_PATTERNS:
            match = pattern.search(lowered)
            if not match:
                continue
            if has_work_context or "pro woche" in lowered or "per week" in lowered:
                hours = match.group(1)
                self.identity_context["working_student"] = True
                self.identity_context["weekly_work_hours"] = f"{hours}h"
                break

    def _remember_sources(self, provenance: ResponseProvenance | None) -> None:
        if provenance is None:
            return
        for source in provenance.sources:
            _remember_source(self.cited_sources, source)

    def update_summary(self, summary: SessionSummary) -> None:
        """Replace dynamic sidebar summary fields with the latest LLM summary."""

        with self._lock:
            self.profile_facts = [item.strip() for item in summary.profile_facts if item.strip()]
            self.conversation_overview = [
                item.strip() for item in summary.conversation_overview if item.strip()
            ]
            self._touch()

    def restore_portable_state(
        self,
        *,
        messages: list[dict[str, Any]],
        session_memory: dict[str, Any],
        ui_language: str = "en",
    ) -> None:
        """Load a user-owned export bundle into this fresh in-memory session."""

        self.sync_history(messages, ui_language=ui_language)

        with self._lock:
            current_agent = str(session_memory.get("current_agent", "")).strip() or None
            self.current_agent = current_agent
            self.crisis_detected = bool(session_memory.get("crisis_detected", False))
            self.topics = [
                str(item).strip() for item in session_memory.get("topics", ()) if str(item).strip()
            ][-MAX_TOPICS:]
            self.identity_context = {
                str(key): value
                for key, value in dict(session_memory.get("identity_context", {})).items()
                if str(key).strip()
            }
            self.preferences = {
                str(key).strip(): str(value).strip()
                for key, value in dict(session_memory.get("preferences", {})).items()
                if str(key).strip() and str(value).strip()
            }
            self.preferences.setdefault("response_language", ui_language)
            self.active_goals = [
                str(item).strip()
                for item in session_memory.get("active_goals", ())
                if str(item).strip()
            ][-MAX_ACTIVE_GOALS:]
            self.cited_sources = list(_coerce_sources(session_memory.get("cited_sources", ())))
            self.profile_facts = [
                str(item).strip()
                for item in session_memory.get("profile_facts", ())
                if str(item).strip()
            ]
            self.conversation_overview = [
                str(item).strip()
                for item in session_memory.get("conversation_overview", ())
                if str(item).strip()
            ]
            onboarding_state = str(session_memory.get("onboarding_state", "pending")).strip()
            if onboarding_state in {"pending", "in_progress", "complete", "skipped"}:
                self.onboarding_state = cast(
                    Literal["pending", "in_progress", "complete", "skipped"],
                    onboarding_state,
                )
            else:
                self.onboarding_state = "pending"
            self.onboarding_messages = list(
                _coerce_onboarding_messages(session_memory.get("onboarding_messages", ()))
            )
            profile_summary = _truncate_multiline_text(
                str(session_memory.get("profile_summary", "")).strip(),
                limit=MAX_PROFILE_SUMMARY_LENGTH,
            )
            self.profile_summary = profile_summary or None
            self.personalized_prompts = list(
                _coerce_personalized_prompts(session_memory.get("personalized_prompts", ()))
            )
            self.document_memories = list(
                _coerce_document_memories(session_memory.get("document_memories", ()))
            )
            self._active_documents = []
            self._trim_messages()
            self._touch()

    def _trim_messages(self) -> None:
        if len(self.messages) > MAX_SESSION_MESSAGES:
            self.messages = self.messages[-MAX_SESSION_MESSAGES:]

    def _touch(self) -> None:
        self._last_activity = self._now()


class ConversationStore:
    """Thread-safe in-memory session store with TTL cleanup."""

    def __init__(
        self,
        *,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._now = now or time.time
        self._lock = threading.RLock()
        self._sessions: dict[str, Conversation] = {}

    def get_or_create(self, session_id: str | None, *, ui_language: str = "en") -> Conversation:
        with self._lock:
            self._purge_expired_locked()

            if session_id:
                existing = self._sessions.get(session_id)
                if existing and not existing.is_expired():
                    existing.set_preference("response_language", ui_language)
                    return existing

            conversation = Conversation(now=self._now)
            conversation.set_preference("response_language", ui_language)
            self._sessions[conversation.session_id] = conversation
            return conversation

    def get(self, session_id: str) -> Conversation | None:
        with self._lock:
            self._purge_expired_locked()
            return self._sessions.get(session_id)

    def snapshot(self, session_id: str) -> SessionMemorySnapshot | None:
        conversation = self.get(session_id)
        if conversation is None:
            return None
        return conversation.snapshot()

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    @property
    def count(self) -> int:
        with self._lock:
            self._purge_expired_locked()
            return len(self._sessions)

    def _purge_expired_locked(self) -> None:
        expired = [session_id for session_id, conv in self._sessions.items() if conv.is_expired()]
        for session_id in expired:
            self._sessions.pop(session_id, None)


def build_session_memory_addendum(
    session_memory: dict[str, Any] | SessionMemorySnapshot | None,
) -> str:
    """Convert ephemeral memory into a compact prompt addendum."""

    if session_memory is None:
        return ""

    if isinstance(session_memory, SessionMemorySnapshot):
        raw_memory = session_memory.model_dump(mode="python")
    else:
        raw_memory = dict(session_memory)

    topics = tuple(str(item).strip() for item in raw_memory.get("topics", ()) if str(item).strip())
    active_goals = tuple(
        str(item).strip() for item in raw_memory.get("active_goals", ()) if str(item).strip()
    )
    current_agent = str(raw_memory.get("current_agent", "")).strip() or None
    crisis_detected = bool(raw_memory.get("crisis_detected", False))
    preferences = raw_memory.get("preferences", {})
    cited_sources = _coerce_sources(raw_memory.get("cited_sources", ()))
    profile_facts = tuple(
        str(item).strip() for item in raw_memory.get("profile_facts", ()) if str(item).strip()
    )
    conversation_overview = tuple(
        str(item).strip()
        for item in raw_memory.get("conversation_overview", ())
        if str(item).strip()
    )
    onboarding_state = str(raw_memory.get("onboarding_state", "")).strip()
    profile_summary = _truncate_multiline_text(
        str(raw_memory.get("profile_summary", "")).strip(),
        limit=MAX_PROFILE_SUMMARY_LENGTH,
    )
    personalized_prompts = _coerce_personalized_prompts(raw_memory.get("personalized_prompts", ()))
    document_memories = _coerce_document_memories(raw_memory.get("document_memories", ()))

    if not any(
        (
            topics,
            active_goals,
            current_agent,
            crisis_detected,
            preferences,
            cited_sources,
            profile_facts,
            conversation_overview,
            onboarding_state,
            profile_summary,
            personalized_prompts,
            document_memories,
        )
    ):
        return ""

    lines = [
        "",
        "",
        "SESSION MEMORY (EPHEMERAL, CURRENT SESSION ONLY):",
        "- Use this to maintain continuity inside the current session only.",
        "- Build on what the user already asked instead of restarting from scratch.",
        "- If the user corrects a detail, prefer the newest turn over older memory.",
    ]

    response_language = str(preferences.get("response_language", "")).strip()
    if response_language:
        lines.append(f"- Preferred response language: {response_language}")

    if current_agent:
        lines.append(f"- Last specialist used: {current_agent}")

    if topics:
        lines.append(f"- Topics already discussed: {', '.join(topics)}")

    if active_goals:
        lines.append("- Recent user requests:")
        lines.extend(f"  - {goal}" for goal in active_goals)

    if onboarding_state and onboarding_state != "pending":
        lines.append(f"- Onboarding status in this session: {onboarding_state}")

    if profile_summary:
        lines.append("- Narrative profile summary gathered in this session:")
        lines.extend(
            f"  - {line.strip()}" for line in re.split(r"\n+", profile_summary) if line.strip()
        )

    if profile_facts:
        lines.append("- Dynamic context recognized in this session:")
        lines.extend(f"  - {fact}" for fact in profile_facts[:6])

    if personalized_prompts:
        labels = ", ".join(prompt.label for prompt in personalized_prompts[:4])
        lines.append(f"- Tailored follow-up prompts already prepared: {labels}")

    if document_memories:
        lines.append("- Documents already discussed in this session:")
        for document in document_memories[:MAX_ACTIVE_DOCUMENTS]:
            if document.summary:
                lines.append(f"  - {document.display_label}: {document.summary}")
            else:
                lines.append(f"  - {document.display_label}")

    if conversation_overview:
        lines.append("- Session summary so far:")
        lines.extend(f"  - {point}" for point in conversation_overview[:4])

    if cited_sources:
        lines.append("- Sources already cited in this session:")
        for source in cited_sources[:3]:
            lines.append(f"  - {source.title} ({source.domain})")

    if crisis_detected:
        lines.append("- Crisis support was already shown earlier in this session.")

    return "\n".join(lines)


def _coerce_provenance(
    provenance: ResponseProvenance | dict[str, Any] | None,
) -> ResponseProvenance | None:
    if provenance is None:
        return None
    if isinstance(provenance, ResponseProvenance):
        return provenance
    if isinstance(provenance, dict):
        return ResponseProvenance.model_validate(provenance)
    raise TypeError(f"Unsupported provenance type: {type(provenance).__name__}")


def _coerce_sources(raw_sources: Any) -> tuple[SourceAttribution, ...]:
    sources: list[SourceAttribution] = []
    if not isinstance(raw_sources, (list, tuple)):
        return ()

    for raw in raw_sources:
        if isinstance(raw, SourceAttribution):
            sources.append(raw)
            continue
        if isinstance(raw, dict):
            sources.append(SourceAttribution.model_validate(raw))

    return tuple(sources)


def _coerce_onboarding_messages(values: Any) -> tuple[SessionTextTurn, ...]:
    messages: list[SessionTextTurn] = []
    for item in values or ():
        if isinstance(item, SessionTextTurn):
            messages.append(item)
            continue
        if isinstance(item, dict):
            messages.append(SessionTextTurn.model_validate(item))
    return tuple(messages[-MAX_ONBOARDING_MESSAGES:])


def _coerce_personalized_prompts(values: Any) -> tuple[PersonalizedPrompt, ...]:
    prompts: list[PersonalizedPrompt] = []
    seen: set[tuple[str, str]] = set()
    for item in values or ():
        if isinstance(item, PersonalizedPrompt):
            prompt = item
        elif isinstance(item, dict):
            prompt = PersonalizedPrompt.model_validate(item)
        else:
            continue
        key = (prompt.label.casefold(), prompt.message.casefold())
        if key in seen:
            continue
        seen.add(key)
        prompts.append(prompt)
    return tuple(prompts[:MAX_PERSONALIZED_PROMPTS])


def _coerce_document_memories(values: Any) -> tuple[DocumentMemory, ...]:
    documents: list[DocumentMemory] = []
    seen_hashes: set[str] = set()
    for item in values or ():
        if isinstance(item, DocumentMemory):
            document = item
        elif isinstance(item, dict):
            document = DocumentMemory.model_validate(item)
        else:
            continue
        if document.sha256 in seen_hashes:
            continue
        seen_hashes.add(document.sha256)
        documents.append(document)
    return tuple(documents[-MAX_ACTIVE_DOCUMENTS:])
