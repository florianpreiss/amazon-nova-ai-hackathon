from src.core.conversation import SessionMemorySnapshot
from src.core.provenance import SourceAttribution
from src.ui import build_session_profile_view


def test_build_session_profile_view_localizes_and_limits_recent_items() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-123",
        created_at=10.0,
        last_activity=20.0,
        message_count=6,
        current_agent="FINANCING",
        crisis_detected=False,
        topics=("BAfoeG", "scholarships", "study choice", "financing", "deadlines"),
        identity_context={
            "working_student": True,
            "first_generation_student": True,
        },
        preferences={"response_language": "de"},
        active_goals=(
            "Ich brauche Hilfe bei BAföG.",
            "Welche Stipendien passen zu mir?",
            "Was sollte ich zuerst beantragen?",
            "Wie plane ich das Semester finanziell?",
        ),
        cited_sources=(
            SourceAttribution(
                title="BAföG",
                url="https://www.studienwahl.de/finanzierung/bafoeg",
                domain="studienwahl.de",
                origin="source_registry",
            ),
            SourceAttribution(
                title="Finanzierungsmöglichkeiten",
                url="https://www.arbeiterkind.de/finanzierung",
                domain="arbeiterkind.de",
                origin="source_registry",
            ),
        ),
    )

    view = build_session_profile_view(snapshot, ui_language="de")

    assert view.has_content is True
    assert view.message_count == 6
    assert view.current_agent == "FINANCING"
    assert view.response_language_label == "Deutsch"
    assert view.topic_labels == ("Fristen", "Finanzierung", "Studienwahl", "Stipendien")
    assert view.goal_summaries == (
        "Wie plane ich das Semester finanziell?",
        "Was sollte ich zuerst beantragen?",
        "Welche Stipendien passen zu mir?",
    )
    assert view.identity_labels == (
        "Erstakademiker*in",
        "Arbeitet neben dem Studium",
    )
    assert [source.domain for source in view.cited_sources] == [
        "arbeiterkind.de",
        "studienwahl.de",
    ]


def test_build_session_profile_view_returns_empty_view_without_snapshot() -> None:
    view = build_session_profile_view(None, ui_language="fr")

    assert view.has_content is False
    assert view.message_count == 0
    assert view.response_language_label is None
    assert view.topic_labels == ()
    assert view.goal_summaries == ()
    assert view.identity_labels == ()
    assert view.cited_sources == ()
