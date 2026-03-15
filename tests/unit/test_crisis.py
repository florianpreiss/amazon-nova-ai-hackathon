"""Unit tests for crisis detection safeguards."""

import pytest
from src.agents.crisis import CrisisRadar

pytestmark = pytest.mark.unit


class StubCrisisClient:
    def __init__(self, response_text: str = "CRISIS: NO\nTYPE: NONE") -> None:
        self.response_text = response_text
        self.called = False

    def converse(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        tool_config: dict | None = None,
        reasoning_effort: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float = 1.0,
    ) -> dict:
        del messages, system_prompt, tool_config, reasoning_effort, max_tokens, temperature, top_p
        self.called = True
        return {"ok": True}

    def extract_text(self, response: dict) -> str:
        del response
        return self.response_text


def test_crisis_radar_skips_benign_study_choice_questions() -> None:
    client = StubCrisisClient(response_text="CRISIS: YES\nTYPE: DROPOUT")
    radar = CrisisRadar(client=client)

    result = radar.scan(
        "Bevor ich mich um Finanzierung kümmere, will ich erstmal wissen, ob ich überhaupt studieren will oder ob es sich lohnt."
    )

    assert result["is_crisis"] is False
    assert result["resources"] is None
    assert "BENIGN_STUDY_CHOICE" in result["assessment"]
    assert client.called is False


def test_crisis_radar_still_allows_real_crisis_language() -> None:
    client = StubCrisisClient(response_text="CRISIS: YES\nTYPE: MENTAL")
    radar = CrisisRadar(client=client)

    result = radar.scan("Ich kann nicht mehr und will einfach nur verschwinden.")

    assert client.called is True
    assert result["is_crisis"] is True
    assert result["resources"] is not None


def test_crisis_radar_does_not_override_when_strong_distress_is_present() -> None:
    client = StubCrisisClient(response_text="CRISIS: YES\nTYPE: DROPOUT")
    radar = CrisisRadar(client=client)

    result = radar.scan(
        "Ich frage mich, ob ich überhaupt studieren soll, aber gerade ist alles sinnlos und ich kann nicht mehr."
    )

    assert client.called is True
    assert result["is_crisis"] is True
    assert result["resources"] is not None
