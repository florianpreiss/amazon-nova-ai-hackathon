"""
Router Agent — fast message classification using Extended Thinking LOW.

Determines which specialist agent should handle the incoming message.
"""

from src.core.client import NovaClient

ROUTER_PROMPT = """You are the router for KODA, an AI companion for first-generation academics.

Analyze the user's message and determine which agent should handle it.

Available agents:
- COMPASS: First contact, emotional support, general orientation. Use when someone is new, unsure, overwhelmed, or does not fit other categories.
- FINANCING: Student aid (BAföG), scholarships, cost of living, student jobs, loans. Any financial question about studying.
- STUDY_CHOICE: Degree programs, universities, numerus clausus, applications, types of higher education institutions.
- ACADEMIC_BASICS: Fundamental questions about how university works, academic terminology, study vs. apprenticeship decisions.
- ROLE_MODELS: Motivation, role models, career visions, impostor feelings, self-doubt, encouragement.

IMPORTANT: Always respond in English regardless of the language of the user's message.
Respond ONLY with the agent name:
AGENT: [NAME]

If the message is ambiguous, choose COMPASS.
"""

# Fallback map for non-English model output (e.g. when the model mirrors
# the user's language despite instructions).  Keys are casefold substrings.
_GERMAN_FALLBACK: dict[str, str] = {
    "finanzierung": "FINANCING",
    "studiumswahl": "STUDY_CHOICE",
    "studienwahl": "STUDY_CHOICE",
    "hochschulwahl": "STUDY_CHOICE",
    "grundlagen": "ACADEMIC_BASICS",
    "studiengrundlagen": "ACADEMIC_BASICS",
    "vorbilder": "ROLE_MODELS",
    "kompass": "COMPASS",
}


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
            max_tokens=50,
            temperature=0.0,
        )

        text = self.client.extract_text(response)
        upper = text.upper()

        for name in self.VALID_AGENTS:
            if name in upper:
                return name

        # Second-chance: model may have translated agent names despite instructions
        lower = text.casefold()
        for fragment, agent in _GERMAN_FALLBACK.items():
            if fragment in lower:
                return agent

        return "COMPASS"
