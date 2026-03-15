"""Unit tests for internal session summarization."""

import pytest
from src.core.session_summary import NovaSessionSummarizer, SessionSummary

pytestmark = pytest.mark.unit


class StubSummaryClient:
    def __init__(self, *, text: str = "", error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.last_system_prompt: str | None = None
        self.last_messages: list[dict] | None = None

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
        del tool_config, reasoning_effort, max_tokens, temperature, top_p
        self.last_messages = messages
        self.last_system_prompt = system_prompt
        if self.error is not None:
            raise self.error
        return {"ok": True}

    def extract_text(self, _response: dict) -> str:
        return self.text


def test_nova_session_summarizer_parses_json_and_uses_previous_summary_context() -> None:
    client = StubSummaryClient(
        text="""
```json
{
  "profile_facts": ["Erstakademikerin", "Arbeitet 20h/Woche"],
  "conversation_overview": [
    "Du vergleichst BAföG, Stipendien und deinen Nebenjob.",
    "Wichtig bleibt, dass deine Finanzierung zu 20h Arbeit pro Woche passt."
  ]
}
```
"""
    )
    summarizer = NovaSessionSummarizer(client=client)
    previous = SessionSummary(
        profile_facts=("Erstakademikerin",),
        conversation_overview=("Du suchst nach Finanzierungsmöglichkeiten.",),
    )

    result = summarizer.summarize(
        [{"role": "user", "content": [{"text": "Ich arbeite 20h pro Woche und brauche BAföG."}]}],
        ui_language="de",
        previous_summary=previous,
    )

    assert result.profile_facts == ("Erstakademikerin", "Arbeitet 20h/Woche")
    assert result.conversation_overview == (
        "Du vergleichst BAföG, Stipendien und deinen Nebenjob.",
        "Wichtig bleibt, dass deine Finanzierung zu 20h Arbeit pro Woche passt.",
    )
    assert client.last_messages is not None
    assert client.last_system_prompt is not None
    assert "Use German for every string in the JSON output." in client.last_system_prompt
    assert "Existing profile_facts:" in client.last_system_prompt
    assert "Du suchst nach Finanzierungsmöglichkeiten." in client.last_system_prompt


def test_nova_session_summarizer_preserves_previous_summary_on_invalid_output() -> None:
    client = StubSummaryClient(text="not json at all")
    summarizer = NovaSessionSummarizer(client=client)
    previous = SessionSummary(
        profile_facts=("First-generation student",),
        conversation_overview=("You are comparing study funding options.",),
    )

    result = summarizer.summarize(
        [{"role": "user", "content": [{"text": "What funding options fit me best?"}]}],
        ui_language="en",
        previous_summary=previous,
    )

    assert result == previous


def test_nova_session_summarizer_preserves_previous_summary_on_empty_output() -> None:
    client = StubSummaryClient(text="   ")
    summarizer = NovaSessionSummarizer(client=client)
    previous = SessionSummary(
        profile_facts=("Erstakademikerin",),
        conversation_overview=("Du suchst nach Finanzierungsmöglichkeiten.",),
    )

    result = summarizer.summarize(
        [{"role": "user", "content": [{"text": "Ich brauche Orientierung."}]}],
        ui_language="de",
        previous_summary=previous,
    )

    assert result == previous


def test_nova_session_summarizer_repairs_trailing_commas() -> None:
    client = StubSummaryClient(
        text="""
{
  "profile_facts": ["Erstakademikerin",],
  "conversation_overview": [
    "Du vergleichst BAföG und Stipendien.",
  ],
}
"""
    )
    summarizer = NovaSessionSummarizer(client=client)

    result = summarizer.summarize(
        [{"role": "user", "content": [{"text": "Ich brauche Hilfe bei BAföG."}]}],
        ui_language="de",
    )

    assert result.profile_facts == ("Erstakademikerin",)
    assert result.conversation_overview == ("Du vergleichst BAföG und Stipendien.",)
