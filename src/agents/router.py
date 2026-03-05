"""
Router Agent — fast message classification using Extended Thinking LOW.

Determines which specialist agent should handle the incoming message.
"""

from config.prompt_loader import load_agent_config
from src.core.client import NovaClient

_cfg = load_agent_config("router")


class RouterAgent:
    """Routes each message to the appropriate specialist agent."""

    VALID_AGENTS = ("FINANCING", "STUDY_CHOICE", "ACADEMIC_BASICS", "ROLE_MODELS", "COMPASS")

    def __init__(self):
        self.client = NovaClient()

    def route(self, user_message: str) -> str:
        """Return the agent name that should handle this message."""
        messages = [{"role": "user", "content": [{"text": user_message}]}]

        response = self.client.converse(
            messages=messages,
            system_prompt=_cfg["system_prompt"],
            reasoning_effort=_cfg["agent"]["reasoning_effort"],
            max_tokens=_cfg["agent"]["max_tokens"],
            temperature=_cfg["agent"]["temperature"],
        )

        text = self.client.extract_text(response).upper()
        for name in self.VALID_AGENTS:
            if name in text:
                return name
        return "COMPASS"
