"""
Base class for all KODA agents.

Provides: system prompt enrichment, tool selection, anti-shame filtering,
and graceful error handling (never shows stack traces to users).
"""

import structlog

from src.core.client import NovaClient, NovaClientError
from src.core.safety import apply_anti_shame_filter, build_identity_addendum

logger = structlog.get_logger()

LANGUAGE_INSTRUCTION = """

LANGUAGE RULE (CRITICAL):
Always reply in the same language the user writes in.
If the user writes in German, reply in German.
If the user writes in English, reply in English.
If the user writes in any other language, reply in that language.
Auto-detect the language from the user's latest message and match it exactly.
"""

FALLBACK_MESSAGES = {
    "en": "I'm having a temporary issue. Please try again in a moment.",
    "de": "Ich habe gerade ein technisches Problem. Bitte versuche es in einem Moment erneut.",
}


class BaseAgent:
    """Base class for all domain agents."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        reasoning_effort: str | None = None,
        tool_mode: str | None = None,
    ):
        self.name = name
        self._base_prompt = system_prompt + LANGUAGE_INSTRUCTION
        self.reasoning_effort = reasoning_effort
        self.tool_mode = tool_mode
        self.client = NovaClient()

    def respond(self, messages: list[dict], metadata: dict | None = None) -> str:
        """
        Generate a response via Nova 2 Lite with graceful error handling.

        Never raises exceptions to the caller. Returns a friendly fallback
        message if anything goes wrong.
        """
        try:
            prompt = self._build_prompt(metadata)

            if self.tool_mode == "code_interpreter":
                resp = self.client.with_code_interpreter(messages, prompt, self.reasoning_effort)
            elif self.tool_mode == "web_grounding":
                resp = self.client.with_web_grounding(messages, prompt, self.reasoning_effort)
            else:
                resp = self.client.converse(
                    messages, prompt, reasoning_effort=self.reasoning_effort
                )

            text = self.client.extract_text(resp)

            if not text.strip():
                logger.warning("empty_response", agent=self.name)
                return self._fallback_message(messages)

            return apply_anti_shame_filter(text)

        except NovaClientError as e:
            logger.error("agent_error", agent=self.name, error=str(e))
            return self._fallback_message(messages)

        except Exception as e:
            logger.error(
                "agent_unexpected_error", agent=self.name, error=str(e), type=type(e).__name__
            )
            return self._fallback_message(messages)

    def _build_prompt(self, metadata: dict | None) -> str:
        """Build the system prompt with optional metadata enrichment."""
        prompt = self._base_prompt
        if metadata and metadata.get("identity_context"):
            prompt += build_identity_addendum(metadata["identity_context"])
        return prompt

    @staticmethod
    def _fallback_message(messages: list[dict]) -> str:
        """Return a fallback in the user's language."""
        if messages:
            last_msg = messages[-1].get("content", [{}])
            if isinstance(last_msg, list) and last_msg:
                text = last_msg[0].get("text", "")
                # Simple German detection heuristic
                german_indicators = ["ich", "ist", "und", "ein", "was", "wie", "mein"]
                words = text.lower().split()
                if any(w in german_indicators for w in words[:10]):
                    return FALLBACK_MESSAGES["de"]
        return FALLBACK_MESSAGES["en"]
