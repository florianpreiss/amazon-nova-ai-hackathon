"""Unit tests for onboarding marker parsing helpers."""

from __future__ import annotations

import pytest
from src.agents.onboarding import OnboardingAgent

pytestmark = pytest.mark.unit


def test_onboarding_agent_extracts_profile_and_prompts() -> None:
    text = """
Danke, das hilft mir weiter.

[PROFILE_START]
situation: Du bist 17 und noch in der Schule.
main_concern: Du bist unsicher, ob ein Studium zu dir passt.
context: Du willst dich orientieren und verschiedene Wege vergleichen.
language: de
[PROFILE_END]

[PROMPTS_START]
- Studium oder Ausbildung | Wie finde ich heraus, ob Studium oder Ausbildung besser zu mir passt?
- Offene Tage | Welche offenen Tage oder Schnupperangebote sollte ich nutzen?
[PROMPTS_END]
"""

    assert OnboardingAgent.extract_profile(text) is not None
    prompts = OnboardingAgent.extract_prompts(text)

    assert prompts is not None
    assert prompts[0]["label"] == "Studium oder Ausbildung"
    assert prompts[0]["message"].startswith("Wie finde ich heraus")


def test_onboarding_agent_clean_for_display_removes_marker_blocks() -> None:
    text = """
Danke, das hilft mir weiter.

[PROFILE_START]
situation: Beispiel
[PROFILE_END]

[PROMPTS_START]
- Frage | Frage?
[PROMPTS_END]
"""

    cleaned = OnboardingAgent.clean_for_display(text)

    assert cleaned == "Danke, das hilft mir weiter."
