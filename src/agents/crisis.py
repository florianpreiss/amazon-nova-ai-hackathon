"""
Crisis Radar — parallel safety monitor on every message.

Detects financial emergencies, mental health crises, dropout risk,
and acute danger using contextual reasoning (not just keywords).
"""

from __future__ import annotations

import re
from typing import Protocol

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
- "I want to understand whether studying is right for me" → NOT a crisis (normal orientation).
- "I am unsure whether university is worth it for me" → NOT a crisis (study-choice exploration).
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

_BENIGN_STUDY_CHOICE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bob ich (?:ueberhaupt |überhaupt )?studieren will\b"),
    re.compile(r"\bob ich studieren soll\b"),
    re.compile(r"\bob sich (?:ein )?studium lohnt\b"),
    re.compile(r"\blohnt sich (?:ein )?studium\b"),
    re.compile(r"\bwill mich (?:erstmal )?(?:zum |ueber |über )?studium informieren\b"),
    re.compile(r"\bmich (?:erstmal )?(?:zum |ueber |über )?studium informieren\b"),
    re.compile(r"\bstudium oder ausbildung\b"),
    re.compile(r"\bwhether (?:college|university|studying) is worth it\b"),
    re.compile(r"\bwhether i (?:even )?want to study\b"),
    re.compile(r"\bif i should study\b"),
)

_STRONG_CRISIS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:suizid|suicide|kill myself|bring myself|self-harm|selbstmord)\b"),
    re.compile(r"\b(?:ich kann nicht mehr|i can't do this anymore|i cant do this anymore)\b"),
    re.compile(
        r"\b(?:verschwinden|disappear|nicht mehr leben|don't want to live|do not want to live)\b"
    ),
    re.compile(r"\b(?:alles ist sinnlos|nothing matters|no point anymore|keinen sinn mehr)\b"),
    re.compile(r"\b(?:obdachlos|homeless|gewalt|violence)\b"),
    re.compile(
        r"\b(?:kann.*(?:miete|essen) nicht bezahlen|can't pay (?:rent|food)|cannot pay (?:rent|food))\b"
    ),
)


class CrisisClient(Protocol):
    def converse(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        tool_config: dict | None = None,
        reasoning_effort: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
        top_p: float = 1.0,
    ) -> dict: ...

    def extract_text(self, response: dict) -> str: ...


class CrisisRadar:
    """Scans every user message for crisis indicators."""

    def __init__(self, client: CrisisClient | None = None):
        self.client = client or NovaClient()

    def scan(self, message: str) -> dict:
        """Return crisis assessment with resources if needed."""
        normalized = message.casefold()
        if _looks_like_benign_study_choice(normalized) and not _contains_strong_crisis_signal(
            normalized
        ):
            return _no_crisis("BENIGN_STUDY_CHOICE")

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
        crisis_type = _extract_crisis_type(text)

        if (
            is_crisis
            and crisis_type == "DROPOUT"
            and _looks_like_benign_study_choice(normalized)
            and not _contains_strong_crisis_signal(normalized)
        ):
            return _no_crisis("DROPOUT_OVERRIDE")

        return {
            "is_crisis": is_crisis,
            "assessment": text,
            "resources": CRISIS_RESOURCES if is_crisis else None,
        }


def _looks_like_benign_study_choice(text: str) -> bool:
    return any(pattern.search(text) for pattern in _BENIGN_STUDY_CHOICE_PATTERNS)


def _contains_strong_crisis_signal(text: str) -> bool:
    return any(pattern.search(text) for pattern in _STRONG_CRISIS_PATTERNS)


def _extract_crisis_type(assessment: str) -> str | None:
    match = re.search(r"TYPE:\s*([A-Z]+)", assessment)
    if not match:
        return None
    return match.group(1)


def _no_crisis(reason: str) -> dict:
    return {
        "is_crisis": False,
        "assessment": f"CRISIS: NO\nTYPE: NONE\nREASON: {reason}",
        "resources": None,
    }
