"""
Onboarding Agent — conversational intake for new KODA users.

Asks 3-5 empathetic questions to understand the user's situation,
then outputs a structured profile and personalized prompt suggestions.
"""

import re
from collections.abc import Generator

from config.prompt_loader import load_agent_config

from src.agents.base import BaseAgent

START_TRIGGER = "[START_ONBOARDING]"

_PROFILE_RE = re.compile(r"\[PROFILE_START\](.*?)\[PROFILE_END\]", re.DOTALL)
_PROMPTS_RE = re.compile(r"\[PROMPTS_START\](.*?)\[PROMPTS_END\]", re.DOTALL)


class OnboardingAgent(BaseAgent):
    """Onboarding agent that guides new users through an intake conversation."""

    def __init__(self):
        cfg = load_agent_config("onboarding")
        super().__init__(
            name=cfg["agent"]["name"],
            system_prompt=cfg["system_prompt"],
            reasoning_effort=cfg["agent"]["reasoning_effort"],
        )

    def start_greeting(self) -> Generator[str, None, None]:
        """Trigger the initial multilingual greeting; no user input required."""
        yield from self.respond_stream(
            [{"role": "user", "content": [{"text": START_TRIGGER}]}]
        )

    @staticmethod
    def extract_profile(text: str) -> str | None:
        """Parse [PROFILE_START]...[PROFILE_END] and return the raw block text.

        Returns None if no profile block is found (onboarding not yet complete).
        """
        m = _PROFILE_RE.search(text)
        return m.group(1).strip() if m else None

    @staticmethod
    def extract_prompts(text: str) -> list[dict] | None:
        """Parse [PROMPTS_START]...[PROMPTS_END] into a list of {label, message} dicts.

        Each line in the block must follow the format:
            - <button label> | <full question>

        Returns None if no prompts block is found or parsing yields no results.
        """
        m = _PROMPTS_RE.search(text)
        if not m:
            return None
        result = []
        for line in m.group(1).strip().splitlines():
            line = line.lstrip("- ").strip()
            if "|" in line:
                label, message = line.split("|", 1)
                result.append({"label": label.strip(), "message": message.strip()})
        return result or None

    @staticmethod
    def clean_for_display(text: str) -> str:
        """Strip structured marker blocks so the user sees only the human summary."""
        text = _PROFILE_RE.sub("", text)
        text = _PROMPTS_RE.sub("", text)
        return text.strip()
