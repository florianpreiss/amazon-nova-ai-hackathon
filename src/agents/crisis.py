"""
Crisis Radar — parallel safety monitor on every message.

Detects financial emergencies, mental health crises, dropout risk,
and acute danger using contextual reasoning (not just keywords).
"""

from config.settings import REASONING_LOW

from src.core.client import NovaClient

CRISIS_PROMPT = """You are a crisis detector for a student support system.

Analyze the user's message for signs of:
1. FINANCIAL: Cannot pay rent or food, at risk of dropping out due to money.
2. MENTAL: Hopelessness, self-harm indicators, extreme isolation, despair.
3. DROPOUT: Wants to quit studies, sees no purpose in continuing.
4. ACUTE: Homelessness, violence, immediate physical danger.

IMPORTANT: Understand CONTEXT.
- "I can't pass this exam" → NOT a crisis (academic frustration).
- "I can't do this anymore, I just want to disappear" → POTENTIAL crisis.

Respond ONLY in this format:
CRISIS: YES or NO
TYPE: FINANCIAL | MENTAL | DROPOUT | ACUTE | NONE
"""

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
            system_prompt=CRISIS_PROMPT,
            reasoning_effort=REASONING_LOW,
            max_tokens=100,
            temperature=0.0,
        )
        text = self.client.extract_text(response).upper()
        is_crisis = "CRISIS: YES" in text

        return {
            "is_crisis": is_crisis,
            "assessment": text,
            "resources": CRISIS_RESOURCES if is_crisis else None,
        }
