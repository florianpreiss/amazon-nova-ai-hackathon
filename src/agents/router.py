"""
Router Agent — fast message classification using Extended Thinking LOW.

Determines which specialist agent should handle the incoming message.
"""

from src.core.client import NovaClient
from config.settings import REASONING_LOW

ROUTER_PROMPT = """You are the router for KODA, an AI companion for first-generation academics.

Analyze the user's message and determine which agent should handle it.

Available agents:
- COMPASS: First contact, emotional support, general orientation. Use when someone is new, unsure, overwhelmed, or does not fit other categories.
- FINANCING: Student aid (BAföG), scholarships, cost of living, student jobs, loans. Any financial question about studying.
- STUDY_CHOICE: Degree programs, universities, numerus clausus, applications, types of higher education institutions.
- ACADEMIC_BASICS: Fundamental questions about how university works, academic terminology, study vs. apprenticeship decisions.
- ROLE_MODELS: Motivation, role models, career visions, impostor feelings, self-doubt, encouragement.

Respond ONLY with the agent name:
AGENT: [NAME]

If the message is ambiguous, choose COMPASS.
"""


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
            system_prompt=ROUTER_PROMPT,
            reasoning_effort=REASONING_LOW,
            max_tokens=50,
            temperature=0.0,
        )

        text = self.client.extract_text(response).upper()
        for name in self.VALID_AGENTS:
            if name in text:
                return name
        return "COMPASS"
