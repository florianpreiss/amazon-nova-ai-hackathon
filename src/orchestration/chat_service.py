"""
Shared chat orchestration used by both the API and the Streamlit frontend.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict

from src.agents.academic_basics.hidden_curriculum import HiddenCurriculumAgent
from src.agents.base import BaseAgent
from src.agents.compass import CompassAgent
from src.agents.crisis import CrisisRadar
from src.agents.financing.student_aid import StudentAidAgent
from src.agents.onboarding import START_TRIGGER, OnboardingAgent
from src.agents.role_models.anti_impostor import AntiImpostorAgent
from src.agents.router import RouterAgent
from src.agents.study_choice.degree_explorer import DegreeExplorerAgent
from src.core.conversation import (
    Conversation,
    ConversationStore,
    PersonalizedPrompt,
    SessionMemorySnapshot,
)
from src.core.documents import DocumentUploadInput, UploadedDocument, validate_document_uploads
from src.core.provenance import (
    ResponseProvenance,
    build_default_provenance,
    build_document_source,
    build_provenance_context,
    with_document_sources,
)
from src.core.session_bundle import (
    SessionBundle,
    build_session_bundle,
    parse_session_bundle,
    portable_messages_to_history,
)
from src.core.session_summary import NovaSessionSummarizer, SessionSummarizer, SessionSummary
from src.i18n import t


class ChatTurnResult(BaseModel):
    """Structured output for a single assistant turn."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    response: str
    agent: str
    crisis: bool
    crisis_resources: dict[str, str] | None = None
    provenance: ResponseProvenance


class OnboardingTurnResult(BaseModel):
    """Structured output for a single onboarding turn."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    response: str
    onboarding_state: str
    completed: bool
    profile_summary: str | None = None
    personalized_prompts: tuple[PersonalizedPrompt, ...] = ()
    provenance: ResponseProvenance


@dataclass(frozen=True)
class PreparedChatTurn:
    """The shared context computed before generating a reply."""

    session: Conversation
    bedrock_messages: list[dict[str, Any]]
    crisis: dict[str, Any]
    agent_key: str
    agent: BaseAgent
    metadata: dict[str, Any]
    crisis_prefix: str


@dataclass(frozen=True)
class PreparedOnboardingTurn:
    """Computed onboarding context before generating the next onboarding reply."""

    session: Conversation
    bedrock_messages: list[dict[str, Any]]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ImportedSession:
    """Result of loading a user-owned session bundle into a fresh session."""

    session_id: str
    ui_language: str
    messages: tuple[dict[str, Any], ...]
    snapshot: SessionMemorySnapshot


class ChatService:
    """One source of truth for routing, safety checks, and response shaping."""

    def __init__(
        self,
        *,
        router: RouterAgent,
        crisis_radar: CrisisRadar,
        agents: dict[str, BaseAgent],
        onboarding_agent: OnboardingAgent | None = None,
        sessions: ConversationStore | None = None,
        summarizer: SessionSummarizer | None = None,
    ) -> None:
        self.router = router
        self.crisis_radar = crisis_radar
        self.agents = agents
        self.onboarding_agent = onboarding_agent or OnboardingAgent()
        self.sessions = sessions or ConversationStore()
        self.summarizer = summarizer

    @property
    def agent_keys(self) -> tuple[str, ...]:
        """Return the registered agent keys in stable order."""

        return tuple(self.agents.keys())

    def respond(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
        conversation_metadata: dict[str, Any] | None = None,
    ) -> ChatTurnResult:
        """Return a complete reply for a single user turn."""

        turn = self._prepare_turn(
            user_message,
            history=history or [],
            session_id=session_id,
            ui_language=ui_language,
            conversation_metadata=conversation_metadata,
        )
        reply = turn.agent.respond_with_details(turn.bedrock_messages, turn.metadata)
        self._store_completed_turn(
            turn.session,
            user_message=user_message,
            response=turn.crisis_prefix + reply.text,
            agent_key=turn.agent_key,
            ui_language=ui_language,
            crisis=turn.crisis["is_crisis"],
            provenance=reply.provenance,
        )
        return ChatTurnResult(
            session_id=turn.session.session_id,
            response=turn.crisis_prefix + reply.text,
            agent=turn.agent_key,
            crisis=turn.crisis["is_crisis"],
            crisis_resources=turn.crisis.get("resources"),
            provenance=reply.provenance,
        )

    def respond_with_documents(
        self,
        user_message: str,
        documents: list[DocumentUploadInput] | tuple[DocumentUploadInput, ...],
        history: list[dict[str, Any]] | None = None,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
        conversation_metadata: dict[str, Any] | None = None,
    ) -> ChatTurnResult:
        """Return a complete reply for a turn that includes uploaded documents."""

        validated_documents = validate_document_uploads(list(documents))
        effective_message = user_message.strip() or self._default_document_message(ui_language)
        turn = self._prepare_turn(
            effective_message,
            history=history or [],
            session_id=session_id,
            ui_language=ui_language,
            conversation_metadata=conversation_metadata,
            documents=validated_documents,
        )
        reply = turn.agent.respond_with_details(turn.bedrock_messages, turn.metadata)
        document_sources = tuple(
            build_document_source(document.name) for document in validated_documents
        )
        provenance = (
            reply.provenance
            if reply.provenance.document_used
            else with_document_sources(reply.provenance, document_sources)
        )
        full_response = turn.crisis_prefix + reply.text
        self._store_completed_turn(
            turn.session,
            user_message=effective_message,
            response=full_response,
            agent_key=turn.agent_key,
            ui_language=ui_language,
            crisis=turn.crisis["is_crisis"],
            provenance=provenance,
            documents=validated_documents,
        )
        return ChatTurnResult(
            session_id=turn.session.session_id,
            response=full_response,
            agent=turn.agent_key,
            crisis=turn.crisis["is_crisis"],
            crisis_resources=turn.crisis.get("resources"),
            provenance=provenance,
        )

    def respond_stream(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
        conversation_metadata: dict[str, Any] | None = None,
    ) -> Generator[str | ChatTurnResult, None, None]:
        """Stream visible text chunks and finish with a structured turn result."""

        turn = self._prepare_turn(
            user_message,
            history=history or [],
            session_id=session_id,
            ui_language=ui_language,
            conversation_metadata=conversation_metadata,
        )

        if turn.crisis_prefix:
            yield turn.crisis_prefix

        collected: list[str] = [turn.crisis_prefix]
        replace_text: str | None = None
        provenance = turn.metadata["provenance"]

        if turn.agent.tool_mode in {"code_interpreter", "web_grounding"}:
            reply = turn.agent.respond_with_details(turn.bedrock_messages, turn.metadata)
            collected.append(reply.text)
            provenance = reply.provenance
            yield reply.text
        else:
            for chunk in turn.agent.respond_stream(turn.bedrock_messages, turn.metadata):
                if chunk.startswith("\x00REPLACE\x00"):
                    replace_text = turn.crisis_prefix + chunk.removeprefix("\x00REPLACE\x00")
                    continue

                collected.append(chunk)
                yield chunk

        full_response = replace_text if replace_text is not None else "".join(collected)
        self._store_completed_turn(
            turn.session,
            user_message=user_message,
            response=full_response,
            agent_key=turn.agent_key,
            ui_language=ui_language,
            crisis=turn.crisis["is_crisis"],
            provenance=provenance,
        )

        yield ChatTurnResult(
            session_id=turn.session.session_id,
            response=full_response,
            agent=turn.agent_key,
            crisis=turn.crisis["is_crisis"],
            crisis_resources=turn.crisis.get("resources"),
            provenance=provenance,
        )

    def start_onboarding(
        self,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
    ) -> OnboardingTurnResult:
        """Start onboarding and return the first assistant greeting/question."""

        prepared = self._prepare_onboarding_start(session_id=session_id, ui_language=ui_language)
        reply = self.onboarding_agent.respond_with_details(
            prepared.bedrock_messages,
            prepared.metadata,
        )
        return self._finalize_onboarding_reply(
            prepared.session,
            response_text=reply.text,
            ui_language=ui_language,
            provenance=reply.provenance,
        )

    def start_onboarding_stream(
        self,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
    ) -> Generator[str | OnboardingTurnResult, None, None]:
        """Stream the initial onboarding greeting and finish with structured metadata."""

        prepared = self._prepare_onboarding_start(session_id=session_id, ui_language=ui_language)
        yield from self._stream_onboarding_reply(
            prepared.session,
            bedrock_messages=prepared.bedrock_messages,
            metadata=prepared.metadata,
            ui_language=ui_language,
        )

    def continue_onboarding(
        self,
        user_message: str,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
    ) -> OnboardingTurnResult:
        """Continue onboarding with one user answer."""

        prepared = self._prepare_onboarding_turn(
            user_message,
            session_id=session_id,
            ui_language=ui_language,
        )
        reply = self.onboarding_agent.respond_with_details(
            prepared.bedrock_messages,
            prepared.metadata,
        )
        return self._finalize_onboarding_reply(
            prepared.session,
            response_text=reply.text,
            ui_language=ui_language,
            provenance=reply.provenance,
            user_message=user_message,
        )

    def continue_onboarding_stream(
        self,
        user_message: str,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
    ) -> Generator[str | OnboardingTurnResult, None, None]:
        """Stream one onboarding turn and finish with structured metadata."""

        prepared = self._prepare_onboarding_turn(
            user_message,
            session_id=session_id,
            ui_language=ui_language,
        )
        yield from self._stream_onboarding_reply(
            prepared.session,
            bedrock_messages=prepared.bedrock_messages,
            metadata=prepared.metadata,
            ui_language=ui_language,
            user_message=user_message,
        )

    def skip_onboarding(
        self,
        *,
        session_id: str | None = None,
        ui_language: str = "en",
    ) -> SessionMemorySnapshot:
        """Mark onboarding as skipped for the current session."""

        session = self.sessions.get_or_create(session_id, ui_language=ui_language)
        session.skip_onboarding()
        session.set_preference("response_language", ui_language)
        return session.snapshot()

    def _prepare_turn(
        self,
        user_message: str,
        *,
        history: list[dict[str, Any]],
        session_id: str | None,
        ui_language: str,
        conversation_metadata: dict[str, Any] | None,
        documents: tuple[UploadedDocument, ...] = (),
    ) -> PreparedChatTurn:
        session = self.sessions.get_or_create(session_id, ui_language=ui_language)
        if history:
            session.sync_history(history, ui_language=ui_language)

        metadata = self._merge_conversation_metadata(session.metadata, conversation_metadata)
        bedrock_messages = self._build_bedrock_messages(
            session.get_messages(),
            user_message,
            documents=documents,
        )
        crisis = self.crisis_radar.scan(user_message)
        agent_key = self.router.route(self._build_route_message(user_message, documents))
        agent = self.agents.get(agent_key, self.agents["COMPASS"])

        metadata.update(
            build_provenance_context(
                agent_key=agent_key,
                user_message=self._build_route_message(user_message, documents),
                ui_language=ui_language,
                tool_mode=agent.tool_mode,
            )
        )

        remembered_documents = tuple(
            document.display_label for document in session.snapshot().document_memories
        )
        if documents or remembered_documents:
            metadata["document_context"] = {
                "attached": tuple(document.short_label for document in documents),
                "remembered": remembered_documents,
            }

        if documents:
            document_sources = tuple(build_document_source(document.name) for document in documents)
            metadata["provenance"] = with_document_sources(
                metadata.get("provenance")
                if isinstance(metadata.get("provenance"), ResponseProvenance)
                else (
                    ResponseProvenance.model_validate(metadata["provenance"])
                    if isinstance(metadata.get("provenance"), dict)
                    else None
                ),
                document_sources,
            )

        return PreparedChatTurn(
            session=session,
            bedrock_messages=bedrock_messages,
            crisis=crisis,
            agent_key=agent_key,
            agent=agent,
            metadata=metadata,
            crisis_prefix=self._format_crisis_prefix(crisis, ui_language),
        )

    def _prepare_onboarding_start(
        self,
        *,
        session_id: str | None,
        ui_language: str,
    ) -> PreparedOnboardingTurn:
        session = self.sessions.get_or_create(session_id, ui_language=ui_language)
        session.set_onboarding_state("in_progress")
        session.set_preference("response_language", ui_language)
        metadata = self._merge_conversation_metadata(session.metadata, None)
        metadata["onboarding_user_turn_count"] = 0
        metadata["force_onboarding_completion"] = False
        bedrock_messages = [{"role": "user", "content": [{"text": START_TRIGGER}]}]
        return PreparedOnboardingTurn(
            session=session,
            bedrock_messages=bedrock_messages,
            metadata=metadata,
        )

    def _prepare_onboarding_turn(
        self,
        user_message: str,
        *,
        session_id: str | None,
        ui_language: str,
    ) -> PreparedOnboardingTurn:
        session = self.sessions.get_or_create(session_id, ui_language=ui_language)
        session.set_onboarding_state("in_progress")
        session.set_preference("response_language", ui_language)
        metadata = self._merge_conversation_metadata(session.metadata, None)
        existing_user_turns = sum(
            1 for turn in session.snapshot().onboarding_messages if turn.role == "user"
        )
        user_turn_count = existing_user_turns + 1
        metadata["onboarding_user_turn_count"] = user_turn_count
        metadata["force_onboarding_completion"] = user_turn_count >= 4
        bedrock_messages = self._build_onboarding_messages(session, user_message=user_message)
        return PreparedOnboardingTurn(
            session=session,
            bedrock_messages=bedrock_messages,
            metadata=metadata,
        )

    def _stream_onboarding_reply(
        self,
        session: Conversation,
        *,
        bedrock_messages: list[dict[str, Any]],
        metadata: dict[str, Any],
        ui_language: str,
        user_message: str | None = None,
    ) -> Generator[str | OnboardingTurnResult, None, None]:
        collected: list[str] = []
        replace_text: str | None = None

        for chunk in self.onboarding_agent.respond_stream(bedrock_messages, metadata):
            if chunk.startswith("\x00REPLACE\x00"):
                replace_text = chunk.removeprefix("\x00REPLACE\x00")
                continue
            collected.append(chunk)
            yield chunk

        full_response = replace_text if replace_text is not None else "".join(collected)
        yield self._finalize_onboarding_reply(
            session,
            response_text=full_response,
            ui_language=ui_language,
            provenance=metadata.get("provenance") or build_default_provenance(),
            user_message=user_message,
        )

    def _finalize_onboarding_reply(
        self,
        session: Conversation,
        *,
        response_text: str,
        ui_language: str,
        provenance: ResponseProvenance,
        user_message: str | None = None,
    ) -> OnboardingTurnResult:
        if user_message:
            session.add_onboarding_message("user", user_message)

        profile_summary = self.onboarding_agent.extract_profile(response_text)
        prompt_payload = self.onboarding_agent.extract_prompts(response_text) or []
        display_text = self.onboarding_agent.clean_for_display(response_text)
        session.add_onboarding_message("assistant", display_text)

        if profile_summary:
            session.complete_onboarding(
                profile_summary=profile_summary,
                personalized_prompts=prompt_payload,
                ui_language=ui_language,
            )
        else:
            session.set_onboarding_state("in_progress")

        snapshot = session.snapshot()
        return OnboardingTurnResult(
            session_id=session.session_id,
            response=display_text,
            onboarding_state=snapshot.onboarding_state,
            completed=snapshot.onboarding_state == "complete",
            profile_summary=snapshot.profile_summary,
            personalized_prompts=snapshot.personalized_prompts,
            provenance=(
                provenance
                if isinstance(provenance, ResponseProvenance)
                else ResponseProvenance.model_validate(provenance)
            ),
        )

    @staticmethod
    def _build_bedrock_messages(
        history: list[dict[str, Any]],
        user_message: str,
        *,
        documents: tuple[UploadedDocument, ...] = (),
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for message in history:
            role = message.get("role", "user")
            content = message.get("content", "")

            if isinstance(content, list):
                normalized.append({"role": role, "content": content})
                continue

            if isinstance(content, str):
                normalized.append({"role": role, "content": [{"text": content}]})
                continue

            raise TypeError(f"Unsupported message content type: {type(content).__name__}")

        final_content: list[dict[str, Any]] = [{"text": user_message}]
        final_content.extend(document.to_bedrock_block() for document in documents)
        normalized.append({"role": "user", "content": final_content})
        return normalized

    @staticmethod
    def _build_route_message(
        user_message: str,
        documents: tuple[UploadedDocument, ...] = (),
    ) -> str:
        if not documents:
            return user_message
        names = ", ".join(document.name for document in documents)
        return f"{user_message}\n\nAttached documents: {names}"

    @staticmethod
    def _default_document_message(ui_language: str) -> str:
        if ui_language == "de":
            return "Bitte erkläre mir dieses Dokument in einfacher Sprache und sage mir, was jetzt wichtig ist."
        return "Please explain this document in plain language and tell me what matters now."

    @staticmethod
    def _build_onboarding_messages(
        session: Conversation,
        *,
        user_message: str | None = None,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = [{"role": "user", "content": [{"text": START_TRIGGER}]}]
        for turn in session.snapshot().onboarding_messages:
            normalized.append({"role": turn.role, "content": [{"text": turn.content}]})
        if user_message is not None:
            normalized.append({"role": "user", "content": [{"text": user_message}]})
        return normalized

    @staticmethod
    def _merge_conversation_metadata(
        base_metadata: dict[str, Any],
        extra_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        merged = dict(base_metadata)
        if not extra_metadata:
            return merged

        for key, value in extra_metadata.items():
            if (
                key in {"identity_context", "preferences"}
                and isinstance(merged.get(key), dict)
                and isinstance(value, dict)
            ):
                nested = dict(merged[key])
                nested.update(value)
                merged[key] = nested
                continue
            merged[key] = value
        return merged

    @staticmethod
    def _format_crisis_prefix(crisis: dict[str, Any], ui_language: str) -> str:
        if not crisis["is_crisis"] or not crisis["resources"]:
            return ""

        lines = [t("crisis_banner", ui_language)]
        for value in crisis["resources"].values():
            lines.append(f"• {value}")
        lines.append("")
        return "\n".join(lines) + "\n"

    def _store_completed_turn(
        self,
        session: Conversation,
        *,
        user_message: str,
        response: str,
        agent_key: str,
        ui_language: str,
        crisis: bool,
        provenance: ResponseProvenance,
        documents: tuple[UploadedDocument, ...] = (),
    ) -> None:
        previous_summary = SessionSummary(
            profile_facts=tuple(session.profile_facts),
            conversation_overview=tuple(session.conversation_overview),
        )
        session.add_user_message(user_message, ui_language=ui_language)
        session.add_assistant_message(
            response,
            agent_key=agent_key,
            crisis=crisis,
            provenance=provenance,
        )
        if self.summarizer is not None:
            summary = self.summarizer.summarize(
                session.get_messages(),
                ui_language=ui_language,
                previous_summary=previous_summary,
            )
            session.update_summary(summary)
        if documents:
            session.set_active_documents(documents, summary_text=response)

    def end_session(self, session_id: str) -> None:
        """Delete a session explicitly."""

        self.sessions.delete(session_id)

    def get_session_snapshot(self, session_id: str) -> SessionMemorySnapshot | None:
        """Return the current in-memory summary for a session, if it exists."""

        return self.sessions.snapshot(session_id)

    def export_session_bundle(self, session_id: str) -> SessionBundle | None:
        """Build a validated user-owned export bundle for the active session."""

        session = self.sessions.get(session_id)
        if session is None:
            return None
        return build_session_bundle(
            snapshot=session.snapshot(),
            messages=session.get_messages(),
        )

    def import_session_bundle(
        self,
        payload: bytes | str | dict[str, Any] | SessionBundle,
        *,
        ui_language: str | None = None,
    ) -> ImportedSession:
        """Load a user-owned bundle into a new ephemeral session."""

        bundle = (
            parse_session_bundle(payload.model_dump(mode="python"))
            if isinstance(payload, SessionBundle)
            else parse_session_bundle(payload)
        )
        imported_language = (
            bundle.session.preferences.get("response_language") or ui_language or "en"
        )
        session = self.sessions.get_or_create(None, ui_language=imported_language)
        history = portable_messages_to_history(bundle.session.messages)
        session.restore_portable_state(
            messages=history,
            session_memory=bundle.session.model_dump(mode="python"),
            ui_language=imported_language,
        )
        snapshot = session.snapshot()
        return ImportedSession(
            session_id=session.session_id,
            ui_language=imported_language,
            messages=tuple(history),
            snapshot=snapshot,
        )

    @property
    def session_count(self) -> int:
        """Expose the number of active in-memory sessions."""

        return self.sessions.count


def build_default_chat_service() -> ChatService:
    """Create the production chat service with the standard agent registry."""

    return ChatService(
        router=RouterAgent(),
        crisis_radar=CrisisRadar(),
        agents={
            "COMPASS": CompassAgent(),
            "FINANCING": StudentAidAgent(),
            "STUDY_CHOICE": DegreeExplorerAgent(),
            "ACADEMIC_BASICS": HiddenCurriculumAgent(),
            "ROLE_MODELS": AntiImpostorAgent(),
        },
        onboarding_agent=OnboardingAgent(),
        summarizer=NovaSessionSummarizer(),
    )
