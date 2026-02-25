"""
Ephemeral conversation state.

Sessions live in memory only — no persistent storage, no user identification.
Auto-expires after configurable inactivity. Privacy by design.
"""

import time
import uuid

from config.settings import SESSION_TIMEOUT_MINUTES


class Conversation:
    """Single user session — created on first message, destroyed on close or timeout."""

    def __init__(self):
        self.session_id: str = str(uuid.uuid4())
        self.messages: list[dict] = []
        self.metadata: dict = {
            "current_agent": None,
            "topics": [],
            "identity_context": {},
            "crisis_detected": False,
        }
        self._last_activity = time.time()

    def add_user_message(self, text: str) -> None:
        self.messages.append({"role": "user", "content": [{"text": text}]})
        self._last_activity = time.time()

    def add_assistant_message(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": [{"text": text}]})
        self._last_activity = time.time()

    def get_messages(self, last_n: int | None = None) -> list[dict]:
        return self.messages[-last_n:] if last_n else self.messages

    def is_expired(self) -> bool:
        elapsed: float = time.time() - self._last_activity
        timeout_seconds: int = SESSION_TIMEOUT_MINUTES * 60
        return elapsed > timeout_seconds
