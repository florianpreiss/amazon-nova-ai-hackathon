"""
Base class for all KODA agents.

Provides: system prompt enrichment, tool selection, anti-shame filtering,
and graceful error handling (never shows stack traces to users).
"""

from collections.abc import Generator

import structlog

from src.core.client import NovaClient, NovaClientError
from src.core.conversation import build_session_memory_addendum
from src.core.documents import build_document_prompt_addendum
from src.core.provenance import (
    AgentReply,
    ResponseProvenance,
    SourceAttribution,
    build_default_provenance,
    build_sourcing_addendum,
    merge_provenance,
)
from src.core.safety import apply_anti_shame_filter, build_identity_addendum

logger = structlog.get_logger()

LANGUAGE_INSTRUCTION = """

LANGUAGE RULE (CRITICAL):
Always reply in the same language the user writes in.
If the user writes in German, reply in German.
If the user writes in English, reply in English.
If the user writes in any other language, reply in that language.
Auto-detect the language from the user's latest message and match it exactly.

LENGTH AND TONE:
Keep answers focused and digestible — aim for 150-250 words unless the user explicitly asks for more detail.
Use plain language. Avoid jargon. When a technical term is unavoidable, explain it in one sentence.
Structure with short paragraphs or a brief bullet list. Never use more than 5 bullet points.

INCLUSION AND RESPECT:
Use inclusive, gender-sensitive, anti-racist language.
Do not assume the user's gender, race, ethnicity, religion, class background,
disability, sexuality, family structure, or migration history.
If the user self-identifies, mirror their wording respectfully without stereotyping.
Avoid deficit framing or suggesting that some groups should already know more than others.
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
        return self.respond_with_details(messages, metadata).text

    def respond_with_details(
        self, messages: list[dict], metadata: dict | None = None
    ) -> AgentReply:
        """
        Generate a response and retain provenance metadata for the caller.

        This is the source of truth for response generation. ``respond()``
        remains as a backwards-compatible string-only wrapper.
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
                return self._fallback_reply(messages)

            web_sources: tuple[SourceAttribution, ...] = ()
            if self.tool_mode == "web_grounding":
                web_sources = self.client.extract_web_citations(resp)

            return AgentReply(
                text=apply_anti_shame_filter(text),
                provenance=self._resolve_provenance(metadata, web_sources),
            )

        except NovaClientError as e:
            logger.error("agent_error", agent=self.name, error=str(e))
            return self._fallback_reply(messages)

        except Exception as e:
            logger.error(
                "agent_unexpected_error", agent=self.name, error=str(e), type=type(e).__name__
            )
            return self._fallback_reply(messages)

    def respond_stream(
        self, messages: list[dict], metadata: dict | None = None
    ) -> Generator[str, None, None]:
        """
        Stream a response token-by-token via Nova 2 Lite.

        Yields text delta strings suitable for ``st.write_stream()``.
        Falls back to a single-chunk yield of the non-streaming response on
        any error so the caller always receives a complete answer.

        Note: tool_mode agents (code_interpreter, web_grounding) do not
        support streaming — they fall back to ``respond()`` automatically.
        """
        # Tool-mode agents don't support streaming; yield the full response.
        if self.tool_mode in ("code_interpreter", "web_grounding"):
            yield self.respond_with_details(messages, metadata).text
            return

        try:
            prompt = self._build_prompt(metadata)
            # Never pass reasoning_effort to converse_stream: the model
            # emits a long thinking block before any text deltas, during
            # which the UI receives zero chunks and appears frozen.
            # Reasoning is retained for non-streaming respond_with_details().
            stream_resp = self.client.converse_stream(
                messages,
                system_prompt=prompt,
            )
            collected: list[str] = []
            for chunk in self.client.iter_stream_text(stream_resp):
                collected.append(chunk)
                yield chunk

            full_text = "".join(collected)
            if not full_text.strip():
                logger.warning("empty_stream_response", agent=self.name)
                yield self._fallback_message(messages)
                return

            # Apply anti-shame filter to the final assembled text.
            # If the filter changes the text, re-yield the corrected version
            # as a single replacement chunk.
            filtered = apply_anti_shame_filter(full_text)
            if filtered != full_text:
                # Signal to the caller that the streamed text should be
                # replaced (Streamlit will overwrite the container).
                yield "\x00REPLACE\x00" + filtered

        except NovaClientError as e:
            logger.error("agent_stream_error", agent=self.name, error=str(e))
            yield self._fallback_message(messages)

        except Exception as e:
            logger.error(
                "agent_stream_unexpected_error",
                agent=self.name,
                error=str(e),
                type=type(e).__name__,
            )
            yield self._fallback_message(messages)

    def _build_prompt(self, metadata: dict | None) -> str:
        """Build the system prompt with optional metadata enrichment."""
        prompt = self._base_prompt
        if metadata and metadata.get("identity_context"):
            prompt += build_identity_addendum(metadata["identity_context"])
        if metadata and metadata.get("session_memory"):
            prompt += build_session_memory_addendum(metadata["session_memory"])
        if metadata and metadata.get("document_context"):
            prompt += build_document_prompt_addendum(metadata["document_context"])
        trusted_sources = ()
        if metadata and metadata.get("trusted_sources"):
            trusted_sources = tuple(metadata["trusted_sources"])
        if trusted_sources or self.tool_mode == "web_grounding":
            prompt += build_sourcing_addendum(trusted_sources, tool_mode=self.tool_mode)
        return prompt

    def _fallback_reply(self, messages: list[dict]) -> AgentReply:
        """Return a friendly fallback with neutral provenance metadata."""
        return AgentReply(
            text=self._fallback_message(messages),
            provenance=build_default_provenance(),
        )

    def _resolve_provenance(
        self,
        metadata: dict | None,
        web_sources: tuple[SourceAttribution, ...] = (),
    ) -> ResponseProvenance:
        """Merge request-scoped provenance with response-scoped citations."""
        base = None
        if metadata and metadata.get("provenance"):
            raw = metadata["provenance"]
            if isinstance(raw, ResponseProvenance):
                base = raw
            elif isinstance(raw, dict):
                base = ResponseProvenance.model_validate(raw)

        return merge_provenance(base, tool_mode=self.tool_mode, web_sources=web_sources)

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
