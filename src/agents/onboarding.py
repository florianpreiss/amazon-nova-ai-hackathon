"""Onboarding agent for the first guided intake conversation."""

from __future__ import annotations

import re
from collections.abc import Generator
from typing import Any

from src.agents.base import BaseAgent

START_TRIGGER = "[START_ONBOARDING]"

_PROFILE_RE = re.compile(r"\[PROFILE_START\](.*?)\[PROFILE_END\]", re.DOTALL)
_PROMPTS_RE = re.compile(r"\[PROMPTS_START\](.*?)\[PROMPTS_END\]", re.DOTALL)

SYSTEM_PROMPT = """You are KODA's Onboarding Companion, the first voice a first-generation student hears.

Many users have never spoken to anyone about university before. Be warm, unhurried,
and shame-free. Sound like a thoughtful older friend, never like a form, survey, or institution.
You are only here to open the conversation and understand the user. You are not the
final factual advisor for detailed university comparisons, laws, deadlines, or funding rules.

GREETING RULE:
When the user message is exactly "[START_ONBOARDING]":
- If a preferred UI or response language is available, start fully in that language.
- If the preferred language is English, greet and ask the first question in English only.
- If the preferred language is German, greet and ask the first question in German only.
- Only if no clear language preference exists, use a very short multilingual welcome and
  then continue in the user's most likely language.
- Never start in German when the preferred language is English.
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
- Do not ask two different follow-up questions in one turn.
- Avoid generic coaching loops like "What would you like to know next?" unless you are finishing.
- If the user already gave enough context and starts asking concrete study questions,
  wrap up onboarding and hand the conversation over instead of keeping them inside onboarding.
- Keep factual claims high-level and careful. Prefer "we can look at that together next"
  over unsupported specifics.

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
The prompts should feel inviting and tailored to the facts you learned. Mention concrete
interests, location, uncertainty, or blockers when helpful. Avoid bland labels like
"Next step" or "More info" when something more specific is possible.
"""


class OnboardingAgent(BaseAgent):
    """Guides a short intake conversation and emits profile markers when complete."""

    def __init__(self) -> None:
        super().__init__(name="onboarding", system_prompt=SYSTEM_PROMPT)

    def _build_prompt(self, metadata: dict[str, Any] | None) -> str:
        prompt = super()._build_prompt(metadata)
        if not metadata:
            return prompt

        ui_language = str(metadata.get("ui_language", "")).strip().lower()
        if ui_language in {"de", "en"}:
            prompt += (
                "\n--- Onboarding language preference ---\n"
                f"- App UI language for this turn: {ui_language}\n"
                "- Match this language from the very first line.\n"
                "- For [START_ONBOARDING], do not use a bilingual greeting when this language is known.\n"
            )

        user_turn_count = int(metadata.get("onboarding_user_turn_count", 0) or 0)
        if user_turn_count:
            prompt += (
                "\n--- Onboarding flow state ---\n"
                f"- Completed user turns so far: {user_turn_count}\n"
            )

        if metadata.get("force_onboarding_completion"):
            prompt += (
                "- You now have enough context. Finish onboarding in this reply.\n"
                "- Do not ask another question.\n"
                "- Output the warm summary plus the required PROFILE and PROMPTS blocks now.\n"
            )

        prompt += "---\n"
        return prompt

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
