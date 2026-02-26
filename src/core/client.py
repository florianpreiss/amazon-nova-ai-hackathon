"""
Amazon Bedrock client wrapper for Nova 2 Lite.

Every agent calls this module — never boto3 directly.
Includes retry logic with exponential backoff for transient errors.

Reference: Nova 2 Developer Guide — "Core inference" and "Troubleshooting" chapters.
"""

import time
from typing import Any

import boto3
import botocore.exceptions
import structlog
from botocore.config import Config
from config.settings import (
    AWS_REGION,
    BEDROCK_READ_TIMEOUT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    NOVA_MODEL_ID,
)

logger = structlog.get_logger()

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds


class NovaClientError(Exception):
    """Base exception for NovaClient errors."""


class NovaThrottlingError(NovaClientError):
    """Raised when Bedrock rate limits are exceeded after all retries."""


class NovaAccessDeniedError(NovaClientError):
    """Raised when IAM permissions are insufficient."""


class NovaTimeoutError(NovaClientError):
    """Raised when Bedrock does not respond within the timeout."""


class NovaClient:
    """Unified wrapper around the Bedrock Converse API for Nova 2 Lite."""

    def __init__(self, model_id: str = NOVA_MODEL_ID, region: str = AWS_REGION):
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(read_timeout=BEDROCK_READ_TIMEOUT),
        )
        self.model_id = model_id

    # ── Public API ─────────────────────────────────

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
        """Send a Converse API request with retry logic."""
        kwargs = self._build(
            messages,
            system_prompt,
            tool_config,
            reasoning_effort,
            max_tokens,
            temperature,
            top_p,
        )
        return self._call_with_retry(kwargs)

    def converse_stream(
        self,
        messages,
        system_prompt=None,
        tool_config=None,
        reasoning_effort=None,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
    ):
        """Streaming variant — returns an event iterator."""
        kwargs = self._build(
            messages,
            system_prompt,
            tool_config,
            reasoning_effort,
            max_tokens,
            temperature,
        )
        return self._client.converse_stream(**kwargs)

    def with_code_interpreter(self, messages, system_prompt=None, reasoning_effort=None):
        """Converse using the built-in Code Interpreter system tool."""
        cfg = {"tools": [{"systemTool": {"name": "nova_code_interpreter"}}]}
        return self.converse(messages, system_prompt, cfg, reasoning_effort, temperature=0.0)

    def with_web_grounding(self, messages, system_prompt=None, reasoning_effort=None):
        """Converse using the built-in Web Grounding system tool."""
        cfg = {"tools": [{"systemTool": {"name": "nova_grounding"}}]}
        return self.converse(messages, system_prompt, cfg, reasoning_effort, temperature=0.3)

    # ── Response helpers ───────────────────────────

    @staticmethod
    def extract_text(response: dict) -> str:
        """Pull all text content from a Converse API response."""
        parts: list[str] = []
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                parts.append(block["text"])
            elif "toolResult" in block:
                for item in block["toolResult"].get("content", []):
                    if "json" in item and item["json"].get("stdOut"):
                        parts.append(item["json"]["stdOut"])
                    elif "text" in item:
                        parts.append(item["text"])
        return "\n".join(parts) if parts else ""

    # ── Internal ───────────────────────────────────

    def _call_with_retry(self, kwargs: dict) -> dict[str, Any]:
        """Execute a Bedrock call with exponential backoff retry."""
        last_exception = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                result: dict[str, Any] = self._client.converse(**kwargs)
                return result

            except botocore.exceptions.ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                if error_code == "ThrottlingException":
                    last_exception = e
                    if attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2**attempt)
                        logger.warning(
                            "bedrock_throttled",
                            attempt=attempt + 1,
                            max_retries=MAX_RETRIES,
                            delay=delay,
                        )
                        time.sleep(delay)
                        continue
                    raise NovaThrottlingError(
                        "Bedrock rate limit exceeded after all retries."
                    ) from e

                if error_code == "AccessDeniedException":
                    logger.error("bedrock_access_denied", error=str(e))
                    raise NovaAccessDeniedError(
                        "Permission denied. Check IAM policy for bedrock:Converse and bedrock:InvokeTool."
                    ) from e

                if error_code == "ValidationException":
                    logger.error("bedrock_validation_error", error=str(e))
                    raise NovaClientError(f"Invalid request: {e}") from e

                # Unknown client error — don't retry
                logger.error("bedrock_client_error", code=error_code, error=str(e))
                raise NovaClientError(f"Bedrock error ({error_code}): {e}") from e

            except botocore.exceptions.ReadTimeoutError as e:
                logger.error("bedrock_timeout", timeout=BEDROCK_READ_TIMEOUT)
                raise NovaTimeoutError("Bedrock did not respond in time. Please try again.") from e

            except Exception as e:
                logger.error("bedrock_unexpected_error", error=str(e), type=type(e).__name__)
                raise NovaClientError(f"Unexpected error: {e}") from e

        # Should not reach here, but safety net
        raise NovaClientError("All retries exhausted.") from last_exception

    def _build(
        self,
        messages: list,
        system_prompt: str | None,
        tool_config: dict | None,
        reasoning_effort: str | None,
        max_tokens: int,
        temperature: float,
        top_p: float = DEFAULT_TOP_P,
    ) -> dict[str, Any]:
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
