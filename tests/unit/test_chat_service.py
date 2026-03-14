"""Unit tests for the shared chat orchestration service."""

from collections.abc import Generator

import pytest
from src.core.provenance import AgentReply, build_default_provenance
from src.i18n import t
from src.orchestration import ChatService, ChatTurnResult

pytestmark = pytest.mark.unit


class StubRouter:
    def __init__(self, agent_key: str) -> None:
        self.agent_key = agent_key

    def route(self, _message: str) -> str:
        return self.agent_key


class StubCrisisRadar:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def scan(self, _message: str) -> dict:
        return self.payload


class StubAgent:
    def __init__(
        self,
        *,
        tool_mode: str | None = None,
        text: str = "Test response",
        stream_chunks: list[str] | None = None,
    ) -> None:
        self.tool_mode = tool_mode
        self.text = text
        self.stream_chunks = stream_chunks or []
        self.messages_seen: list[dict] | None = None
        self.metadata_seen: dict | None = None

    def respond_with_details(
        self, messages: list[dict], metadata: dict | None = None
    ) -> AgentReply:
        self.messages_seen = messages
        self.metadata_seen = metadata or {}
        return AgentReply(text=self.text, provenance=build_default_provenance(self.tool_mode))

    def respond_stream(
        self,
        messages: list[dict],
        metadata: dict | None = None,
    ) -> Generator[str, None, None]:
        self.messages_seen = messages
        self.metadata_seen = metadata or {}
        yield from self.stream_chunks


class TestChatService:
    def test_respond_normalizes_history_and_passes_metadata(self):
        agent = StubAgent(text="Antwort")
        service = ChatService(
            router=StubRouter("FINANCING"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(), "FINANCING": agent},
        )

        result = service.respond(
            "Wie beantrage ich BAfoeG?",
            history=[{"role": "assistant", "content": "Vorherige Antwort"}],
            ui_language="de",
            conversation_metadata={"identity_context": {"first_gen": True}},
        )

        assert result.response == "Antwort"
        assert result.agent == "FINANCING"
        assert agent.messages_seen is not None
        assert agent.metadata_seen is not None
        assert agent.messages_seen[0]["content"][0]["text"] == "Vorherige Antwort"
        assert agent.messages_seen[-1]["content"][0]["text"] == "Wie beantrage ich BAfoeG?"
        assert agent.metadata_seen["identity_context"] == {"first_gen": True}
        assert agent.metadata_seen["provenance"].source_registry_used is True
        assert agent.metadata_seen["trusted_sources"]

    def test_respond_adds_localized_crisis_prefix(self):
        agent = StubAgent(text="Wir finden gemeinsam einen naechsten Schritt.")
        service = ChatService(
            router=StubRouter("COMPASS"),
            crisis_radar=StubCrisisRadar(
                {
                    "is_crisis": True,
                    "resources": {
                        "emergency": "112",
                        "student_support": "Studierendenwerk",
                    },
                }
            ),
            agents={"COMPASS": agent},
        )

        result = service.respond("Ich kann nicht mehr", ui_language="de")

        assert result.crisis is True
        assert result.crisis_resources == {
            "emergency": "112",
            "student_support": "Studierendenwerk",
        }
        assert result.response.startswith(t("crisis_banner", "de"))
        assert "112" in result.response

    def test_stream_returns_structured_result_for_tool_agents(self):
        agent = StubAgent(tool_mode="web_grounding", text="Grounded answer")
        service = ChatService(
            router=StubRouter("STUDY_CHOICE"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(), "STUDY_CHOICE": agent},
        )

        streamed = list(service.respond_stream("How do I compare degrees?", ui_language="en"))

        assert streamed[:-1] == ["Grounded answer"]
        assert isinstance(streamed[-1], ChatTurnResult)
        assert streamed[-1].response == "Grounded answer"
        assert streamed[-1].agent == "STUDY_CHOICE"

    def test_stream_honors_replacement_chunks(self):
        agent = StubAgent(stream_chunks=["First draft", "\x00REPLACE\x00Improved answer"])
        service = ChatService(
            router=StubRouter("COMPASS"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": agent},
        )

        streamed = list(service.respond_stream("I feel lost", ui_language="en"))

        assert streamed[:-1] == ["First draft"]
        assert isinstance(streamed[-1], ChatTurnResult)
        assert streamed[-1].response == "Improved answer"
