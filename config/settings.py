"""
Central configuration — single source of truth for all settings.

Model IDs follow the Nova 2 Developer Guide naming convention:
  US region:  us.amazon.nova-2-lite-v1:0
  Global:     global.amazon.nova-2-lite-v1:0
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── AWS ────────────────────────────────────────────────
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

# ── Models ─────────────────────────────────────────────
NOVA_MODEL_ID: str = os.getenv("NOVA_MODEL_ID", "us.amazon.nova-2-lite-v1:0")
NOVA_EMBEDDINGS_MODEL_ID: str = os.getenv(
    "NOVA_EMBEDDINGS_MODEL_ID",
    "amazon.nova-2-multimodal-embeddings-v1:0",
)

# ── Inference defaults ─────────────────────────────────
DEFAULT_MAX_TOKENS: int = 4096
DEFAULT_TEMPERATURE: float = 0.7
DEFAULT_TOP_P: float = 0.9

# ── Extended thinking effort levels ────────────────────
REASONING_LOW: str = "low"  # Router, Crisis Radar, Compass
REASONING_MEDIUM: str = "medium"
REASONING_HIGH: str = "high"  # All domain agents

# ── API security ──────────────────────────────────────
# Comma-separated list of origins allowed to call the API.
# OWASP A05:2021 — never use a wildcard '*' in production.
# Example: https://koda.example.com,https://koda-staging.example.com
_raw_origins: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501")
CORS_ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]


def validate_cors_origins(origins: list[str]) -> None:
    """
    Fail fast if the CORS origin list is misconfigured.

    Raises:
        ValueError: if ``origins`` is empty or contains the wildcard ``"*"``.

    Call this at process startup (e.g. in a FastAPI lifespan handler) so a
    misconfiguration is caught immediately rather than silently shipping a
    permissive CORS policy to production.

    OWASP A05:2021 — Broken Access Control (Security Misconfiguration).
    """
    if not origins:
        raise ValueError(
            "CORS_ALLOWED_ORIGINS is empty. "
            "Set it to a comma-separated list of allowed origins "
            "(e.g. https://koda.example.com). "
            "An empty list would block all cross-origin requests."
        )
    wildcards = [o for o in origins if o == "*"]
    if wildcards:
        raise ValueError(
            "CORS_ALLOWED_ORIGINS must not contain the wildcard '*'. "
            "Specify explicit origins instead "
            "(e.g. https://koda.example.com). "
            "A wildcard allows any origin to call the API — OWASP A05:2021."
        )


# ── Session ────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# ── Bedrock timeout (Nova guide: up to 60 min for extended thinking) ──
BEDROCK_READ_TIMEOUT: int = 3600
