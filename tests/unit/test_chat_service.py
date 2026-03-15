"""Unit tests for the shared chat orchestration service."""

import json
from collections.abc import Generator

import pytest
from src.core.conversation import ConversationStore
from src.core.provenance import AgentReply, build_default_provenance
from src.core.session_summary import SessionSummary
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


class StubSummarizer:
    def summarize(
        self,
        messages: list[dict],
        *,
        ui_language: str,
        previous_summary: SessionSummary | None = None,
    ) -> SessionSummary:
        assert messages
        assert ui_language in {"de", "en"}
        if previous_summary is not None:
            assert isinstance(previous_summary, SessionSummary)
        if ui_language == "de":
            return SessionSummary(
                profile_facts=("Erstakademikerin", "Arbeitet 20h/Woche"),
                conversation_overview=(
                    "Du fragst nach Finanzierung und Studienalltag.",
                    "Die Arbeit mit 20h/Woche beeinflusst deine Optionen.",
                ),
            )
        return SessionSummary(
            profile_facts=("First-generation student",),
            conversation_overview=("You are exploring study funding.",),
        )


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
        assert result.session_id
        assert result.agent == "FINANCING"
        assert agent.messages_seen is not None
        assert agent.metadata_seen is not None
        assert agent.messages_seen[0]["content"][0]["text"] == "Vorherige Antwort"
        assert agent.messages_seen[-1]["content"][0]["text"] == "Wie beantrage ich BAfoeG?"
        assert agent.metadata_seen["identity_context"] == {"first_gen": True}
        assert agent.metadata_seen["provenance"].source_registry_used is True
        assert agent.metadata_seen["session_memory"]["message_count"] == 1
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
        assert result.session_id
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
        assert streamed[-1].session_id
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

    def test_respond_reuses_session_memory_without_replaying_history(self):
        agent = StubAgent(text="Antwort")
        service = ChatService(
            router=StubRouter("FINANCING"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(), "FINANCING": agent},
        )

        first = service.respond("Ich brauche Hilfe bei BAfoeG.", ui_language="de")
        second = service.respond(
            "Und was ist mit Stipendien?",
            session_id=first.session_id,
            ui_language="de",
        )

        assert second.session_id == first.session_id
        assert agent.messages_seen is not None
        assert len(agent.messages_seen) == 3
        assert agent.messages_seen[0]["content"][0]["text"] == "Ich brauche Hilfe bei BAfoeG."
        assert agent.messages_seen[1]["content"][0]["text"] == "Antwort"
        assert agent.messages_seen[2]["content"][0]["text"] == "Und was ist mit Stipendien?"
        assert agent.metadata_seen is not None
        assert agent.metadata_seen["session_memory"]["active_goals"] == (
            "Ich brauche Hilfe bei BAfoeG.",
        )

    def test_get_session_snapshot_exposes_ephemeral_summary(self):
        clock = iter([100.0, 100.0, 100.0, 101.0, 101.0, 102.0, 102.0, 103.0, 103.0]).__next__
        service = ChatService(
            router=StubRouter("ROLE_MODELS"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(), "ROLE_MODELS": StubAgent(text="Klar.")},
            sessions=ConversationStore(now=clock),
            summarizer=StubSummarizer(),
        )

        result = service.respond(
            "Ich bin Erstakademikerin und fuehle mich wie ein Impostor.",
            ui_language="de",
        )
        snapshot = service.get_session_snapshot(result.session_id)

        assert snapshot is not None
        assert snapshot.session_id == result.session_id
        assert snapshot.current_agent == "ROLE_MODELS"
        assert snapshot.identity_context["first_generation_student"] is True
        assert snapshot.topics[-1] == "role models"
        assert snapshot.preferences["response_language"] == "de"
        assert snapshot.profile_facts == ("Erstakademikerin", "Arbeitet 20h/Woche")
        assert snapshot.conversation_overview == (
            "Du fragst nach Finanzierung und Studienalltag.",
            "Die Arbeit mit 20h/Woche beeinflusst deine Optionen.",
        )

    def test_end_session_removes_ephemeral_memory_immediately(self):
        service = ChatService(
            router=StubRouter("COMPASS"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(text="Alles klar.")},
        )

        result = service.respond("Ich brauche Orientierung.", ui_language="de")

        assert service.get_session_snapshot(result.session_id) is not None

        service.end_session(result.session_id)

        assert service.get_session_snapshot(result.session_id) is None

    def test_export_and_import_round_trip_restores_ephemeral_session(self):
        service = ChatService(
            router=StubRouter("FINANCING"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(), "FINANCING": StubAgent(text="Antwort")},
            summarizer=StubSummarizer(),
        )

        first = service.respond(
            "Ich bin Erstakademikerin und brauche Hilfe bei BAfoeG.",
            ui_language="de",
        )
        service.respond(
            "Und was ist mit Stipendien?",
            session_id=first.session_id,
            ui_language="de",
        )

        bundle = service.export_session_bundle(first.session_id)

        assert bundle is not None

        imported = service.import_session_bundle(bundle, ui_language="en")
        snapshot = service.get_session_snapshot(imported.session_id)

        assert imported.session_id != first.session_id
        assert imported.ui_language == "de"
        assert len(imported.messages) == 4
        assert imported.messages[1]["agent"] == "FINANCING"
        assert snapshot is not None
        assert snapshot.message_count == 4
        assert snapshot.preferences["response_language"] == "de"
        assert snapshot.profile_facts == ("Erstakademikerin", "Arbeitet 20h/Woche")
        assert snapshot.conversation_overview == (
            "Du fragst nach Finanzierung und Studienalltag.",
            "Die Arbeit mit 20h/Woche beeinflusst deine Optionen.",
        )

    def test_import_session_bundle_revalidates_checksum_for_models(self):
        service = ChatService(
            router=StubRouter("COMPASS"),
            crisis_radar=StubCrisisRadar({"is_crisis": False, "resources": None}),
            agents={"COMPASS": StubAgent(text="Antwort")},
        )

        result = service.respond("Ich brauche Orientierung.", ui_language="de")
        bundle = service.export_session_bundle(result.session_id)

        assert bundle is not None

        tampered_payload = bundle.model_dump(mode="json")
        tampered_payload["session"]["active_goals"] = ["Das wurde veraendert."]
        tampered_bundle = bundle.model_validate(json.loads(json.dumps(tampered_payload)))

        with pytest.raises(ValueError, match="Invalid session bundle checksum"):
            service.import_session_bundle(tampered_bundle)
