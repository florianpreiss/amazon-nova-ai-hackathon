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
            "weekly_work_hours": "20h",
        },
        preferences={"response_language": "de"},
        active_goals=(
            "Ich brauche Hilfe bei BAföG.",
            "Welche Stipendien passen zu mir?",
            "Was sollte ich zuerst beantragen?",
            "Wie plane ich das Semester finanziell?",
        ),
        profile_summary=(
            "Du bist Erstakademikerin, arbeitest 20h/Woche und suchst gerade nach "
            "einer guten Finanzierungsstrategie."
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
        profile_facts=(
            "Erstakademikerin",
            "Arbeitet 20h/Woche",
            "Interessiert sich für BAföG und Stipendien",
        ),
        conversation_overview=(
            "Du vergleichst gerade BAföG, Stipendien und deine Arbeitsbelastung.",
            "Wichtig ist, dass deine Finanzierung zu 20h Arbeit pro Woche passt.",
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
    assert view.profile_summary_text is not None
    assert "arbeitest 20h/Woche" in view.profile_summary_text
    assert view.recognized_facts == (
        "Erstakademikerin",
        "Arbeitet 20h/Woche",
        "Interessiert sich für BAföG und Stipendien",
    )
    assert view.conversation_summary_points == (
        "Du vergleichst gerade BAföG, Stipendien und deine Arbeitsbelastung.",
        "Wichtig ist, dass deine Finanzierung zu 20h Arbeit pro Woche passt.",
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
    assert view.recognized_facts == ()
    assert view.conversation_summary_points == ()
    assert view.cited_sources == ()


def test_build_session_profile_view_falls_back_to_structured_memory_without_llm_summary() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-456",
        created_at=10.0,
        last_activity=20.0,
        message_count=2,
        current_agent="COMPASS",
        crisis_detected=False,
        topics=("financing", "scholarships"),
        identity_context={
            "first_generation_student": True,
            "working_student": True,
            "weekly_work_hours": "20h",
        },
        preferences={"response_language": "en"},
        active_goals=("What funding options fit around my 20h job?",),
    )

    view = build_session_profile_view(snapshot, ui_language="en")

    assert view.recognized_facts == (
        "First-generation student",
        "Works about 20h/week",
    )
    assert view.conversation_summary_points == (
        "Important context from the chat: First-generation student, Works about 20h/week.",
        "So far, the conversation is mainly about Scholarships, Financing.",
        "Your current focus is: What funding options fit around my 20h job?",
    )


def test_build_session_profile_view_infers_basic_student_context_from_goals() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-789",
        created_at=10.0,
        last_activity=20.0,
        message_count=2,
        current_agent="COMPASS",
        crisis_detected=False,
        topics=("study choice", "general guidance"),
        preferences={"response_language": "de"},
        active_goals=(
            "Hallo, ich bin 17, bin noch in der Schule und interessiere mich fürs Studium.",
        ),
    )

    view = build_session_profile_view(snapshot, ui_language="de")

    assert view.recognized_facts == (
        "17 Jahre alt",
        "Noch in der Schule",
        "Interesse am Studium",
    )
