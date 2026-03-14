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
from src.agents.role_models.anti_impostor import AntiImpostorAgent
from src.agents.router import RouterAgent
from src.agents.study_choice.degree_explorer import DegreeExplorerAgent
from src.core.provenance import ResponseProvenance, build_provenance_context
from src.i18n import t


class ChatTurnResult(BaseModel):
    """Structured output for a single assistant turn."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    response: str
    agent: str
    crisis: bool
    crisis_resources: dict[str, str] | None = None
    provenance: ResponseProvenance


@dataclass(frozen=True)
class PreparedChatTurn:
    """The shared context computed before generating a reply."""

    bedrock_messages: list[dict[str, Any]]
    crisis: dict[str, Any]
    agent_key: str
    agent: BaseAgent
    metadata: dict[str, Any]
    crisis_prefix: str


class ChatService:
    """One source of truth for routing, safety checks, and response shaping."""

    def __init__(
        self,
        *,
        router: RouterAgent,
        crisis_radar: CrisisRadar,
        agents: dict[str, BaseAgent],
    ) -> None:
        self.router = router
        self.crisis_radar = crisis_radar
        self.agents = agents

    @property
    def agent_keys(self) -> tuple[str, ...]:
        """Return the registered agent keys in stable order."""

        return tuple(self.agents.keys())

    def respond(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        *,
        ui_language: str = "en",
        conversation_metadata: dict[str, Any] | None = None,
    ) -> ChatTurnResult:
        """Return a complete reply for a single user turn."""

        turn = self._prepare_turn(
            user_message,
            history=history or [],
            ui_language=ui_language,
            conversation_metadata=conversation_metadata,
        )
        reply = turn.agent.respond_with_details(turn.bedrock_messages, turn.metadata)
        return ChatTurnResult(
            response=turn.crisis_prefix + reply.text,
            agent=turn.agent_key,
            crisis=turn.crisis["is_crisis"],
            crisis_resources=turn.crisis.get("resources"),
            provenance=reply.provenance,
        )

    def respond_stream(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        *,
        ui_language: str = "en",
        conversation_metadata: dict[str, Any] | None = None,
    ) -> Generator[str | ChatTurnResult, None, None]:
        """Stream visible text chunks and finish with a structured turn result."""

        turn = self._prepare_turn(
            user_message,
            history=history or [],
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

        yield ChatTurnResult(
            response=full_response,
            agent=turn.agent_key,
            crisis=turn.crisis["is_crisis"],
            crisis_resources=turn.crisis.get("resources"),
            provenance=provenance,
        )

    def _prepare_turn(
        self,
        user_message: str,
        *,
        history: list[dict[str, Any]],
        ui_language: str,
        conversation_metadata: dict[str, Any] | None,
    ) -> PreparedChatTurn:
        bedrock_messages = self._build_bedrock_messages(history, user_message)
        crisis = self.crisis_radar.scan(user_message)
        agent_key = self.router.route(user_message)
        agent = self.agents.get(agent_key, self.agents["COMPASS"])

        metadata = dict(conversation_metadata or {})
        metadata.update(
            build_provenance_context(
                agent_key=agent_key,
                user_message=user_message,
                ui_language=ui_language,
                tool_mode=agent.tool_mode,
            )
        )

        return PreparedChatTurn(
            bedrock_messages=bedrock_messages,
            crisis=crisis,
            agent_key=agent_key,
            agent=agent,
            metadata=metadata,
            crisis_prefix=self._format_crisis_prefix(crisis, ui_language),
        )

    @staticmethod
    def _build_bedrock_messages(
        history: list[dict[str, Any]],
        user_message: str,
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

        normalized.append({"role": "user", "content": [{"text": user_message}]})
        return normalized

    @staticmethod
    def _format_crisis_prefix(crisis: dict[str, Any], ui_language: str) -> str:
        if not crisis["is_crisis"] or not crisis["resources"]:
            return ""

        lines = [t("crisis_banner", ui_language)]
        for value in crisis["resources"].values():
            lines.append(f"• {value}")
        lines.append("")
        return "\n".join(lines) + "\n"


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
    )
