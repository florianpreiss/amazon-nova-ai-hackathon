"""Unit tests for ephemeral session memory."""

import pytest
from src.core.conversation import (
    Conversation,
    ConversationStore,
    SessionMemorySnapshot,
    build_session_memory_addendum,
)
from src.core.provenance import ResponseProvenance, SourceAttribution

pytestmark = pytest.mark.unit


class TestConversation:
    def test_conversation_tracks_profile_signals_goals_and_sources(self):
        conversation = Conversation(session_id="session-1", now=lambda: 100.0)

        conversation.add_user_message(
            "Ich bin Erstakademikerin und brauche Hilfe bei BAfoeG und Stipendien.",
            ui_language="de",
        )
        conversation.add_assistant_message(
            "Ich helfe dir Schritt fuer Schritt.",
            agent_key="FINANCING",
            provenance=ResponseProvenance(
                mode="source_registry",
                source_registry_used=True,
                web_grounding_used=False,
                sources=(
                    SourceAttribution(
                        title="BAfoeG Amt",
                        url="https://www.bafoeg.de",
                        domain="bafoeg.de",
                        origin="source_registry",
                    ),
                ),
            ),
        )

        snapshot = conversation.snapshot()

        assert isinstance(snapshot, SessionMemorySnapshot)
        assert snapshot.preferences["response_language"] == "de"
        assert snapshot.identity_context["first_generation_student"] is True
        assert "BAfoeG" in snapshot.topics
        assert snapshot.current_agent == "FINANCING"
        assert snapshot.active_goals == (
            "Ich bin Erstakademikerin und brauche Hilfe bei BAfoeG und Stipendien.",
        )
        assert snapshot.cited_sources[0].domain == "bafoeg.de"

    def test_build_session_memory_addendum_formats_memory_for_prompts(self):
        addendum = build_session_memory_addendum(
            {
                "current_agent": "FINANCING",
                "topics": ("BAfoeG", "scholarships"),
                "preferences": {"response_language": "de"},
                "active_goals": ("Ich brauche Hilfe bei BAfoeG.",),
                "cited_sources": (
                    {
                        "title": "BAfoeG Amt",
                        "url": "https://www.bafoeg.de",
                        "domain": "bafoeg.de",
                        "origin": "source_registry",
                    },
                ),
                "crisis_detected": False,
            }
        )

        assert "SESSION MEMORY" in addendum
        assert "Preferred response language: de" in addendum
        assert "Topics already discussed: BAfoeG, scholarships" in addendum
        assert "BAfoeG Amt (bafoeg.de)" in addendum

    def test_conversation_extracts_work_hours_from_user_context(self):
        conversation = Conversation(session_id="session-hours", now=lambda: 100.0)

        conversation.add_user_message(
            "Ich arbeite 20h pro Woche und brauche Hilfe bei BAfoeG.",
            ui_language="de",
        )

        snapshot = conversation.snapshot()

        assert snapshot.identity_context["working_student"] is True
        assert snapshot.identity_context["weekly_work_hours"] == "20h"

    def test_conversation_tracks_onboarding_state_profile_and_prompts(self):
        conversation = Conversation(session_id="session-onboarding", now=lambda: 100.0)

        conversation.set_onboarding_state("in_progress")
        conversation.add_onboarding_message("assistant", "Wo stehst du gerade?")
        conversation.add_onboarding_message("user", "Ich bin 17 und noch in der Schule.")
        conversation.complete_onboarding(
            profile_summary=(
                "Du bist 17, noch in der Schule und willst herausfinden, "
                "ob ein Studium zu dir passt."
            ),
            personalized_prompts=[
                {
                    "label": "Studium oder Ausbildung",
                    "message": "Wie finde ich heraus, ob Studium oder Ausbildung besser zu mir passt?",
                },
                {
                    "label": "Tage der offenen Tür",
                    "message": "Wie nutze ich Tage der offenen Tür, um mich besser zu orientieren?",
                },
            ],
            ui_language="de",
        )

        snapshot = conversation.snapshot()

        assert snapshot.onboarding_state == "complete"
        assert snapshot.profile_summary is not None
        assert "noch in der Schule" in snapshot.profile_summary
        assert snapshot.onboarding_messages[0].content == "Wo stehst du gerade?"
        assert snapshot.personalized_prompts[0].label == "Studium oder Ausbildung"
        assert snapshot.preferences["response_language"] == "de"

    def test_conversation_keeps_all_unique_sources_for_session(self):
        conversation = Conversation(session_id="session-2", now=lambda: 100.0)

        for index in range(8):
            conversation.add_assistant_message(
                f"Antwort {index}",
                agent_key="FINANCING",
                provenance=ResponseProvenance(
                    mode="source_registry",
                    source_registry_used=True,
                    web_grounding_used=False,
                    sources=(
                        SourceAttribution(
                            title=f"Quelle {index}",
                            url=f"https://example.org/source-{index}",
                            domain="example.org",
                            origin="source_registry",
                        ),
                    ),
                ),
            )

        conversation.add_assistant_message(
            "Antwort mit Duplikat",
            agent_key="FINANCING",
            provenance=ResponseProvenance(
                mode="source_registry",
                source_registry_used=True,
                web_grounding_used=False,
                sources=(
                    SourceAttribution(
                        title="Quelle 3 aktualisiert",
                        url="https://example.org/source-3",
                        domain="example.org",
                        origin="source_registry",
                    ),
                ),
            ),
        )

        snapshot = conversation.snapshot()

        assert len(snapshot.cited_sources) == 8
        assert snapshot.cited_sources[-1].title == "Quelle 3 aktualisiert"

    def test_build_session_memory_addendum_includes_onboarding_summary(self):
        addendum = build_session_memory_addendum(
            {
                "preferences": {"response_language": "de"},
                "onboarding_state": "complete",
                "profile_summary": (
                    "Du bist 17, noch in der Schule und suchst nach Orientierung rund ums Studium."
                ),
                "personalized_prompts": (
                    {
                        "label": "Studium oder Ausbildung",
                        "message": "Wie finde ich heraus, was besser zu mir passt?",
                    },
                ),
            }
        )

        assert "Onboarding status in this session: complete" in addendum
        assert "Narrative profile summary gathered in this session:" in addendum
        assert "Du bist 17, noch in der Schule" in addendum
        assert "Tailored follow-up prompts already prepared: Studium oder Ausbildung" in addendum


class TestConversationStore:
    def test_store_purges_expired_sessions(self):
        ticks = iter([0.0, 0.0, 1900.0, 1900.0, 1900.0, 1900.0]).__next__
        store = ConversationStore(now=ticks)

        first = store.get_or_create(None, ui_language="en")
        second = store.get_or_create(first.session_id, ui_language="en")

        assert second.session_id != first.session_id
        assert store.count == 1
