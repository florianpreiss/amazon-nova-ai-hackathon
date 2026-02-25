"""
Safety: anti-shame filter and intersectionality context enrichment.

Anti-shame: scans responses for language that reinforces class shame.
Intersectionality: enriches prompts with identity context from conversation.
"""

import structlog

logger = structlog.get_logger()

# Patterns that must NEVER appear in KODA responses (any language)
_SHAME_PATTERNS = [
    "you should know",
    "this is basic",
    "everyone knows",
    "obviously",
    "common knowledge",
    "should have learned",
    "das solltest du wissen",
    "das ist grundwissen",
    "jeder weiss",
    "selbstverstaendlich",
]


def apply_anti_shame_filter(text: str) -> str:
    """Log a warning if the response contains shame-reinforcing language."""
    lower = text.lower()
    for p in _SHAME_PATTERNS:
        if p in lower:
            logger.warning("shame_pattern_detected", pattern=p)
    return text


def build_identity_addendum(identity_context: dict) -> str:
    """Build a system-prompt addendum from accumulated identity signals."""
    if not identity_context:
        return ""
    lines = ["\n--- Adapt guidance to this user context ---"]
    for k, v in identity_context.items():
        lines.append(f"- {k}: {v}")
    lines.append("---\n")
    return "\n".join(lines)
