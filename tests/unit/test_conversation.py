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


class TestConversationStore:
    def test_store_purges_expired_sessions(self):
        ticks = iter([0.0, 0.0, 1900.0, 1900.0, 1900.0, 1900.0]).__next__
        store = ConversationStore(now=ticks)

        first = store.get_or_create(None, ui_language="en")
        second = store.get_or_create(first.session_id, ui_language="en")

        assert second.session_id != first.session_id
        assert store.count == 1
