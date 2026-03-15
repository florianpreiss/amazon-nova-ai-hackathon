"""Onboarding agent for the first guided intake conversation."""

from __future__ import annotations

import re
from collections.abc import Generator

from src.agents.base import BaseAgent

START_TRIGGER = "[START_ONBOARDING]"

_PROFILE_RE = re.compile(r"\[PROFILE_START\](.*?)\[PROFILE_END\]", re.DOTALL)
_PROMPTS_RE = re.compile(r"\[PROMPTS_START\](.*?)\[PROMPTS_END\]", re.DOTALL)

SYSTEM_PROMPT = """You are KODA's Onboarding Companion, the first voice a first-generation student hears.

Many users have never spoken to anyone about university before. Be warm, unhurried,
and shame-free. Sound like a thoughtful older friend, never like a form, survey, or institution.

GREETING RULE:
When the user message is exactly "[START_ONBOARDING]":
- Greet briefly in 4-5 languages. German and English are mandatory; add 2-3 other
  languages that are common among immigrant communities in Germany.
- Keep each greeting short, then explain in German and English that KODA can continue
  in any language and wants to understand the user's situation.
- Immediately ask the first onboarding question.

CONVERSATION RULES:
- Ask exactly one question per turn.
- Maximum 5 user turns. You may wrap up after 3 turns if you have enough context.
- Adapt naturally, but try to learn:
  1. Where they are right now: school, recently finished, already enrolled, re-entry
  2. Their biggest question or worry
  3. Any interests or ideas about what they might study
  4. Concrete blockers such as finances, family pressure, not knowing the system, NC
- Normalize uncertainty. Nobody explains this automatically.
- For the user-facing part of the reply, use short paragraphs.
- If you use bullet points or numbering, each item must be on its own line.
- Never compress multiple numbered or bulleted items into one paragraph.

COMPLETION RULE:
After 3-5 turns, first write a short warm summary in the user's language.
Immediately after that, output EXACTLY these marker blocks with no extra explanation
between them:

[PROFILE_START]
situation: <one sentence describing where they are>
main_concern: <one sentence describing their main worry>
context: <1-2 sentences of relevant background, interests, blockers, or goals>
language: <de|en|tr|ar|ru|other>
[PROFILE_END]

[PROMPTS_START]
- <button label max 4 words> | <full follow-up question in the user's language>
- <button label max 4 words> | <full follow-up question>
- <button label max 4 words> | <full follow-up question>
- <button label max 4 words> | <full follow-up question>
[PROMPTS_END]

Generate 3-5 prompts that are specific to the user's situation. Prefer concrete follow-ups
over generic ones. If they mention BAfoeG, finances, self-doubt, or study-vs-apprenticeship,
at least one prompt should reflect that.
"""


class OnboardingAgent(BaseAgent):
    """Guides a short intake conversation and emits profile markers when complete."""

    def __init__(self) -> None:
        super().__init__(name="onboarding", system_prompt=SYSTEM_PROMPT)

    def start_greeting(self) -> Generator[str, None, None]:
        """Trigger the initial onboarding greeting without user input."""

        yield from self.respond_stream(
            [{"role": "user", "content": [{"text": START_TRIGGER}]}],
        )

    @staticmethod
    def extract_profile(text: str) -> str | None:
        """Extract the structured profile block from a completed onboarding reply."""

        match = _PROFILE_RE.search(text)
        return match.group(1).strip() if match else None

    @staticmethod
    def extract_prompts(text: str) -> list[dict[str, str]] | None:
        """Extract tailored quick-action prompts from a completed onboarding reply."""

        match = _PROMPTS_RE.search(text)
        if not match:
            return None

        prompts: list[dict[str, str]] = []
        for line in match.group(1).strip().splitlines():
            line = line.lstrip("- ").strip()
            if "|" not in line:
                continue
            label, message = line.split("|", 1)
            label = label.strip()
            message = message.strip()
            if label and message:
                prompts.append({"label": label, "message": message})
        return prompts or None

    @staticmethod
    def clean_for_display(text: str) -> str:
        """Remove marker blocks so users only see the human-facing summary."""

        text = _PROFILE_RE.sub("", text)
        text = _PROMPTS_RE.sub("", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
