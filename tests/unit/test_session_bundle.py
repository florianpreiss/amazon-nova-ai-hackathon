"""Unit tests for portable session memory bundles."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.core.conversation import SessionMemorySnapshot
from src.core.provenance import ResponseProvenance, SourceAttribution
from src.core.session_bundle import (
    MAX_SESSION_BUNDLE_BYTES,
    build_session_bundle,
    parse_session_bundle,
    portable_messages_to_history,
    serialize_session_bundle,
)

pytestmark = pytest.mark.unit


def _build_snapshot() -> SessionMemorySnapshot:
    return SessionMemorySnapshot(
        session_id="session-1",
        created_at=100.0,
        last_activity=120.0,
        message_count=2,
        current_agent="FINANCING",
        crisis_detected=False,
        topics=("BAfoeG", "scholarships"),
        identity_context={
            "first_generation_student": True,
            "weekly_work_hours": "20h",
        },
        preferences={"response_language": "de"},
        active_goals=("Ich brauche Hilfe bei BAfoeG.",),
        cited_sources=(
            SourceAttribution(
                title="BAfoeG Amt",
                url="https://www.bafoeg.de",
                domain="bafoeg.de",
                origin="source_registry",
            ),
        ),
        profile_facts=("Erstakademikerin", "Arbeitet 20h/Woche"),
        conversation_overview=(
            "Du vergleichst BAfoeG und Stipendien.",
            "Wichtig ist deine Arbeitszeit neben dem Studium.",
        ),
    )


def _build_messages() -> list[dict]:
    return [
        {"role": "user", "content": [{"text": "Ich brauche Hilfe bei BAfoeG."}]},
        {
            "role": "assistant",
            "content": [{"text": "Ich erklaere dir BAfoeG Schritt fuer Schritt."}],
            "agent": "FINANCING",
            "provenance": ResponseProvenance(
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
            ).model_dump(mode="python"),
        },
    ]


def test_session_bundle_round_trips_portable_memory() -> None:
    bundle = build_session_bundle(
        snapshot=_build_snapshot(),
        messages=_build_messages(),
        exported_at=datetime(2026, 3, 15, tzinfo=UTC),
    )

    payload = serialize_session_bundle(bundle)
    parsed = parse_session_bundle(payload)
    history = portable_messages_to_history(parsed.session.messages)

    assert parsed.bundle_type == "koda_session_memory"
    assert parsed.schema_version == "1.0"
    assert parsed.session.preferences["response_language"] == "de"
    assert parsed.session.profile_facts == ("Erstakademikerin", "Arbeitet 20h/Woche")
    assert history[0]["role"] == "user"
    assert history[1]["agent"] == "FINANCING"
    assert history[1]["provenance"]["mode"] == "source_registry"


def test_session_bundle_rejects_checksum_tampering() -> None:
    bundle = build_session_bundle(snapshot=_build_snapshot(), messages=_build_messages())
    payload = serialize_session_bundle(bundle).decode("utf-8")
    tampered = payload.replace("BAfoeG", "Studium", 1)

    with pytest.raises(ValueError, match="Invalid session bundle checksum"):
        parse_session_bundle(tampered)


def test_session_bundle_rejects_oversized_payloads() -> None:
    with pytest.raises(ValueError, match="too large"):
        parse_session_bundle(b" " * (MAX_SESSION_BUNDLE_BYTES + 1))


def test_session_bundle_requires_json_object_root() -> None:
    with pytest.raises(ValueError, match="root must be a JSON object"):
        parse_session_bundle("[]")
