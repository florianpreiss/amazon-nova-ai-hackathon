"""
Base class for all KODA agents.

Provides the standard interface: system prompt enrichment with intersectionality
context, tool selection, and anti-shame post-processing.
"""

from src.core.client import NovaClient
from src.core.safety import apply_anti_shame_filter, build_identity_addendum

# Appended to every agent's system prompt to enable multilingual responses
LANGUAGE_INSTRUCTION = """

LANGUAGE RULE (CRITICAL):
Always reply in the same language the user writes in.
If the user writes in German, reply in German.
If the user writes in English, reply in English.
If the user writes in any other language, reply in that language.
Auto-detect the language from the user's latest message and match it exactly.
"""


class BaseAgent:
    """Base class for all domain agents."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        reasoning_effort: str | None = None,
        tool_mode: str | None = None,  # "code_interpreter" | "web_grounding" | None
    ):
        self.name = name
        self._base_prompt = system_prompt + LANGUAGE_INSTRUCTION
        self.reasoning_effort = reasoning_effort
        self.tool_mode = tool_mode
        self.client = NovaClient()

    def respond(self, messages: list[dict], metadata: dict | None = None) -> str:
        """
        Generate a response via Nova 2 Lite.

        1. Enrich system prompt with intersectionality context
        2. Call the appropriate Converse API variant
        3. Extract text
        4. Apply anti-shame filter
        """
        prompt = self._build_prompt(metadata)

        if self.tool_mode == "code_interpreter":
            resp = self.client.with_code_interpreter(messages, prompt, self.reasoning_effort)
        elif self.tool_mode == "web_grounding":
            resp = self.client.with_web_grounding(messages, prompt, self.reasoning_effort)
        else:
            resp = self.client.converse(messages, prompt, reasoning_effort=self.reasoning_effort)

        text = self.client.extract_text(resp)
        return apply_anti_shame_filter(text)

    def _build_prompt(self, metadata: dict | None) -> str:
        prompt = self._base_prompt
        if metadata and metadata.get("identity_context"):
            prompt += build_identity_addendum(metadata["identity_context"])
        return prompt
