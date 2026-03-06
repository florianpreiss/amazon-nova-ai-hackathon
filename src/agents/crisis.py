"""
Crisis Radar — parallel safety monitor on every message.

Detects financial emergencies, mental health crises, dropout risk,
and acute danger using contextual reasoning (not just keywords).
"""

from config.prompt_loader import load_agent_config

from src.core.client import NovaClient

_cfg = load_agent_config("crisis")

CRISIS_RESOURCES = {
    "emergency": "112 (Emergency) / 110 (Police)",
    "crisis_hotline": "Telefonseelsorge: 0800 111 0 111 (free, 24/7, Germany)",
    "student_counseling": "Free psychological counseling at your university's Studierendenwerk",
    "financial_emergency": "BAföG office: emergency advance payment application (Vorausleistung)",
    "peer_support": "ArbeiterKind.de — mentoring network for first-gen students",
}


class CrisisRadar:
    """Scans every user message for crisis indicators."""

    def __init__(self):
        self.client = NovaClient()

    def scan(self, message: str) -> dict:
        """Return crisis assessment with resources if needed."""
        messages = [{"role": "user", "content": [{"text": message}]}]
        response = self.client.converse(
            messages=messages,
            system_prompt=_cfg["system_prompt"],
            reasoning_effort=_cfg["agent"]["reasoning_effort"],
            max_tokens=_cfg["agent"]["max_tokens"],
            temperature=_cfg["agent"]["temperature"],
        )
        text = self.client.extract_text(response).upper()
        is_crisis = "CRISIS: YES" in text

        return {
            "is_crisis": is_crisis,
            "assessment": text,
            "resources": CRISIS_RESOURCES if is_crisis else None,
        }
