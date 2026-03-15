from src.core.conversation import PersonalizedPrompt, SessionMemorySnapshot
from src.ui import build_quick_action_prompts


def test_build_quick_action_prompts_prioritizes_current_direction() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-financing",
        created_at=10.0,
        last_activity=20.0,
        message_count=4,
        current_agent="FINANCING",
        topics=("study choice", "BAfoeG", "scholarships"),
        active_goals=(
            "Ich will zuerst herausfinden, ob Studium zu mir passt.",
            "Welche Finanzierung passt zu mir?",
        ),
        personalized_prompts=(
            PersonalizedPrompt(
                label="Studium oder Ausbildung",
                message="Wie finde ich heraus, ob Studium oder Ausbildung besser zu mir passt?",
            ),
        ),
    )

    prompts = build_quick_action_prompts(snapshot, ui_language="de")

    assert prompts
    assert prompts[0].label == "Finanzierung verstehen"
    assert any(prompt.label == "Passender Start" for prompt in prompts)
    assert any(prompt.label == "Realistische Wege" for prompt in prompts)
    assert any(prompt.label == "Studium oder Ausbildung" for prompt in prompts)


def test_build_quick_action_prompts_supports_english_study_choice_prompts() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-study-choice",
        created_at=10.0,
        last_activity=20.0,
        message_count=2,
        current_agent="STUDY_CHOICE",
        topics=("general guidance", "study choice"),
        active_goals=("I am unsure whether university is right for me.",),
    )

    prompts = build_quick_action_prompts(snapshot, ui_language="en")

    labels = {prompt.label for prompt in prompts}
    assert "Best starting point" in labels
    assert "Compare paths" in labels
    assert "What fits me?" in labels


def test_build_quick_action_prompts_uses_profile_clues_for_more_specific_prompts() -> None:
    snapshot = SessionMemorySnapshot(
        session_id="session-profile-clues",
        created_at=10.0,
        last_activity=20.0,
        message_count=0,
        profile_summary=(
            "situation: noch in der schule und macht gerade das abitur\n"
            "main_concern: finanzielle unsicherheit und unsicherheit darüber, was an der uni erwartet wird\n"
            "context: interessiert sich für architektur und bauingenieurwesen, kennt bafög noch nicht\n"
            "language: de"
        ),
    )

    prompts = build_quick_action_prompts(snapshot, ui_language="de")

    labels = {prompt.label for prompt in prompts}
    assert "Architektur vs Bau" in labels
    assert "Finanzierung verstehen" in labels
    assert "Uni-Alltag verstehen" in labels


def test_build_quick_action_prompts_returns_empty_without_snapshot() -> None:
    assert build_quick_action_prompts(None, ui_language="de") == ()
