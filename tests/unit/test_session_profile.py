from src.core.conversation import SessionMemorySnapshot, SessionTextTurn
from src.core.documents import DocumentMemory
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


def test_build_session_profile_view_formats_structured_onboarding_profile_text() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-onboarding-profile",
        created_at=10.0,
        last_activity=20.0,
        message_count=0,
        profile_summary=(
            "situation: Du bist 17 und noch in der Schule.\n"
            "main_concern: Du bist unsicher, ob Studium oder Ausbildung besser zu dir passt.\n"
            "context: Du willst dich in Ruhe orientieren und verschiedene Wege vergleichen.\n"
            "language: de"
        ),
    )

    view = build_session_profile_view(snapshot, ui_language="de")

    assert view.profile_summary_text == (
        "Du bist 17 und noch in der Schule. "
        "Du bist unsicher, ob Studium oder Ausbildung besser zu dir passt. "
        "Du willst dich in Ruhe orientieren und verschiedene Wege vergleichen."
    )
    assert view.recognized_facts == (
        "Du bist 17 und noch in der Schule",
        "Du bist unsicher, ob Studium oder Ausbildung besser zu dir passt",
        "Du willst dich in Ruhe orientieren und verschiedene Wege vergleichen",
    )
    assert view.conversation_summary_points == (
        "Deine aktuelle Situation: Du bist 17 und noch in der Schule.",
        "Gerade besonders wichtig für dich: Du bist unsicher, ob Studium oder Ausbildung besser zu dir passt.",
        "Relevanter Hintergrund aus dem Gespräch: Du willst dich in Ruhe orientieren und verschiedene Wege vergleichen.",
    )


def test_build_session_profile_view_counts_onboarding_turns_in_messages() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-onboarding-count",
        created_at=10.0,
        last_activity=20.0,
        message_count=0,
        onboarding_messages=(
            SessionTextTurn(role="assistant", content="Hallo!"),
            SessionTextTurn(role="user", content="Ich bin noch in der Schule."),
            SessionTextTurn(role="assistant", content="Was interessiert dich?"),
        ),
    )

    view = build_session_profile_view(snapshot, ui_language="de")

    assert view.message_count == 3


def test_build_session_profile_view_exposes_document_labels() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-documents",
        created_at=10.0,
        last_activity=20.0,
        message_count=2,
        document_memories=(
            DocumentMemory(
                document_id="doc-1",
                name="BAfoeG-Bescheid.pdf",
                extension="pdf",
                kind="media",
                size_bytes=2048,
                sha256="a" * 64,
                summary="Ein BAföG-Bescheid wurde erklärt.",
            ),
        ),
    )

    view = build_session_profile_view(snapshot, ui_language="de")

    assert view.document_labels == ("BAfoeG-Bescheid.pdf",)
