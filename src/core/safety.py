"""
Safety: anti-shame filter and intersectionality context enrichment.

Anti-shame: scans responses for language that reinforces class shame.
Intersectionality: enriches prompts with identity context from conversation.
"""

import re

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

_SHAME_REPLACEMENTS = {
    "you should know": "I'll explain it clearly",
    "this is basic": "I'll keep this simple",
    "everyone knows": "many people are never told this",
    "obviously": "to make it clear",
    "common knowledge": "often left unexplained",
    "should have learned": "may not have been explained yet",
    "das solltest du wissen": "ich erklaere es dir kurz",
    "das ist grundwissen": "ich halte es bewusst einfach",
    "jeder weiss": "viele Menschen bekommen das nie erklaert",
    "selbstverstaendlich": "zur Einordnung",
}


def apply_anti_shame_filter(text: str) -> str:
    """Rewrite obvious shame-reinforcing language into neutral wording."""
    filtered = text
    lower = filtered.lower()
    for pattern in _SHAME_PATTERNS:
        if pattern not in lower:
            continue
        logger.warning("shame_pattern_detected", pattern=pattern)
        replacement = _SHAME_REPLACEMENTS.get(pattern)
        if replacement:
            filtered = re.sub(re.escape(pattern), replacement, filtered, flags=re.IGNORECASE)
            lower = filtered.lower()
    return filtered


def build_identity_addendum(identity_context: dict) -> str:
    """Build a system-prompt addendum from accumulated identity signals."""
    if not identity_context:
        return ""
    lines = [
        "\n--- Adapt guidance to this user context ---",
        "- Use inclusive, gender-sensitive, anti-racist language.",
        "- Do not stereotype or make assumptions based on gender, race, class, migration history, disability, religion, or sexuality.",
        "- Treat identity markers as context, not as limitations.",
    ]
    for k, v in identity_context.items():
        lines.append(f"- {k}: {v}")
    lines.append("---\n")
    return "\n".join(lines)
