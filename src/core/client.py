"""
Amazon Bedrock client wrapper for Nova 2 Lite.

Every agent calls this module — never boto3 directly.
Handles: inference, extended thinking, Code Interpreter, Web Grounding, streaming.

Reference: Nova 2 Developer Guide — "Core inference" and "Advanced systems" chapters.
"""

import boto3
from botocore.config import Config
from config.settings import (
    AWS_REGION, NOVA_MODEL_ID, BEDROCK_READ_TIMEOUT,
    DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_TOP_P,
)


class NovaClient:
    """Unified wrapper around the Bedrock Converse API for Nova 2 Lite."""

    def __init__(self, model_id: str = NOVA_MODEL_ID, region: str = AWS_REGION):
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(read_timeout=BEDROCK_READ_TIMEOUT),
        )
        self.model_id = model_id

    # ── Public API ─────────────────────────────────────

    def converse(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        tool_config: dict | None = None,
        reasoning_effort: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
    ) -> dict:
        """Send a Converse API request to Nova 2 Lite."""
        return self._client.converse(
            **self._build(messages, system_prompt, tool_config,
                          reasoning_effort, max_tokens, temperature, top_p)
        )

    def converse_stream(self, messages, system_prompt=None, tool_config=None,
                        reasoning_effort=None, max_tokens=DEFAULT_MAX_TOKENS,
                        temperature=DEFAULT_TEMPERATURE):
        """Streaming variant — returns an event iterator."""
        return self._client.converse_stream(
            **self._build(messages, system_prompt, tool_config,
                          reasoning_effort, max_tokens, temperature)
        )

    def with_code_interpreter(self, messages, system_prompt=None, reasoning_effort=None):
        """Converse using the built-in Code Interpreter system tool."""
        cfg = {"tools": [{"systemTool": {"name": "nova_code_interpreter"}}]}
        return self.converse(messages, system_prompt, cfg, reasoning_effort, temperature=0.0)

    def with_web_grounding(self, messages, system_prompt=None, reasoning_effort=None):
        """Converse using the built-in Web Grounding system tool."""
        cfg = {"tools": [{"systemTool": {"name": "nova_grounding"}}]}
        return self.converse(messages, system_prompt, cfg, reasoning_effort, temperature=0.3)

    # ── Helpers ────────────────────────────────────────

    @staticmethod
    def extract_text(response: dict) -> str:
        """Pull all text content from a Converse API response."""
        parts: list[str] = []
        for block in response["output"]["message"]["content"]:
            if "text" in block:
                parts.append(block["text"])
            elif "toolResult" in block:
                for item in block["toolResult"].get("content", []):
                    if "json" in item and item["json"].get("stdOut"):
                        parts.append(item["json"]["stdOut"])
                    elif "text" in item:
                        parts.append(item["text"])
        return "\n".join(parts) if parts else ""

    def _build(self, messages, system_prompt, tool_config,
               reasoning_effort, max_tokens, temperature, top_p=DEFAULT_TOP_P):
        kw: dict = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature, "topP": top_p},
        }
        if system_prompt:
            kw["system"] = [{"text": system_prompt}]
        if tool_config:
            kw["toolConfig"] = tool_config
        if reasoning_effort:
            kw["additionalModelRequestFields"] = {
                "reasoningConfig": {"type": "enabled", "maxReasoningEffort": reasoning_effort}
            }
        return kw
