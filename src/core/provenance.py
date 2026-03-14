"""
Helpers for source-backed prompting and user-facing attribution.
"""

from __future__ import annotations

import re
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator

from src.knowledge import SourceSelectionContext, TrustedSource, select_trusted_sources
from src.knowledge.source_registry import SelectionReason, SourceCategory

CitationOrigin = Literal["source_registry", "web_grounding"]
ProvenanceMode = Literal[
    "source_registry",
    "source_registry_and_web",
    "web_grounding",
    "model",
]

AGENT_SOURCE_CATEGORY: dict[str, SourceCategory] = {
    "FINANCING": "FINANCING",
    "STUDY_CHOICE": "STUDY_CHOICE",
    "ACADEMIC_BASICS": "ACADEMIC_BASICS",
    "ROLE_MODELS": "ROLE_MODELS",
}

GERMAN_HINTS = {
    "abitur",
    "antrag",
    "ausbildung",
    "bafoeg",
    "bafög",
    "bewerbung",
    "deutschland",
    "fachhochschule",
    "finanzierung",
    "hochschule",
    "ich",
    "studieren",
    "studium",
    "und",
    "uni",
    "universitaet",
    "universität",
    "was",
    "wie",
}
ENGLISH_HINTS = {
    "application",
    "college",
    "degree",
    "finance",
    "financing",
    "help",
    "how",
    "i",
    "scholarship",
    "study",
    "university",
    "what",
}
DEFAULT_SOURCE_LIMIT = 5


def _normalize_domain(url: str) -> str:
    return urlparse(url).netloc.casefold().removeprefix("www.")


class SourceAttribution(BaseModel):
    """User-facing citation metadata for a single source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str
    url: str
    domain: str
    origin: CitationOrigin

    @field_validator("title", "url")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("domain")
    @classmethod
    def _normalize_domain(cls, value: str) -> str:
        value = value.strip().casefold().removeprefix("www.")
        if not value:
            raise ValueError("domain must not be blank")
        return value


class ResponseProvenance(BaseModel):
    """Structured metadata that explains where an answer came from."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: ProvenanceMode
    source_registry_used: bool
    web_grounding_used: bool
    source_registry_reason: SelectionReason | None = None
    sources: tuple[SourceAttribution, ...] = ()


class AgentReply(BaseModel):
    """A text answer plus its provenance metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    provenance: ResponseProvenance


def infer_request_language(user_message: str, fallback_language: str = "en") -> str:
    """Infer whether the latest user turn is German or English."""

    tokens = set(re.findall(r"[A-Za-zÄÖÜäöüß]+", user_message.casefold()))
    german_score = len(tokens & GERMAN_HINTS)
    english_score = len(tokens & ENGLISH_HINTS)

    if any(char in user_message for char in "ÄÖÜäöüß"):
        german_score += 1

    if german_score > english_score and german_score > 0:
        return "de"
    if english_score > german_score and english_score > 0:
        return "en"
    return fallback_language.strip().casefold() or "en"


def get_agent_source_category(agent_key: str) -> SourceCategory | None:
    """Map an agent key to a curated-source category when applicable."""

    return AGENT_SOURCE_CATEGORY.get(agent_key)


def build_default_provenance(tool_mode: str | None = None) -> ResponseProvenance:
    """Return honest fallback provenance for an uncited answer."""

    web_grounding_used = tool_mode == "web_grounding"
    mode: ProvenanceMode = "web_grounding" if web_grounding_used else "model"
    return ResponseProvenance(
        mode=mode,
        source_registry_used=False,
        web_grounding_used=web_grounding_used,
        sources=(),
    )


def build_provenance_context(
    *,
    agent_key: str,
    user_message: str,
    ui_language: str,
    tool_mode: str | None,
    country_code: str | None = None,
    limit: int = DEFAULT_SOURCE_LIMIT,
) -> dict:
    """Build prompt metadata and initial provenance for a chat turn."""

    category = get_agent_source_category(agent_key)
    inferred_language = infer_request_language(user_message, ui_language)

    if category is None:
        return {
            "trusted_sources": (),
            "provenance": build_default_provenance(tool_mode),
        }

    selection = select_trusted_sources(
        SourceSelectionContext(
            user_language=inferred_language,
            user_message=user_message,
            country_code=country_code,
        ),
        category=category,
        limit=limit,
    )

    registry_sources = tuple(_from_trusted_source(source) for source in selection.sources)
    mode: ProvenanceMode
    if selection.use_registry:
        mode = "source_registry"
    elif tool_mode == "web_grounding":
        mode = "web_grounding"
    else:
        mode = "model"

    return {
        "trusted_sources": selection.sources,
        "provenance": ResponseProvenance(
            mode=mode,
            source_registry_used=selection.use_registry,
            web_grounding_used=tool_mode == "web_grounding",
            source_registry_reason=selection.reason if selection.use_registry else None,
            sources=registry_sources,
        ),
    }


def build_sourcing_addendum(
    trusted_sources: tuple[TrustedSource, ...] = (),
    *,
    tool_mode: str | None = None,
) -> str:
    """Return prompt guidance that keeps factual answers source-backed."""

    lines = [
        "",
        "",
        "FACTUAL SOURCING POLICY (CRITICAL):",
        "- Prefer source-backed information over unsupported recall.",
        "- If a factual detail is uncertain or not covered by your sources, say that clearly instead of guessing.",
        "- End source-backed answers with a short 'Sources' section listing the source title and URL.",
    ]

    if tool_mode == "web_grounding":
        lines.append(
            "- Use Web Grounding for factual or time-sensitive claims whenever it is available."
        )

    if trusted_sources:
        lines.append(
            "- Prioritize the curated sources below when they are relevant to the user's question."
        )
        lines.append("")
        lines.append("CURATED TRUSTED SOURCES:")
        for index, source in enumerate(trusted_sources, start=1):
            lines.append(f"{index}. {source.title}")
            if source.summary:
                lines.append(f"   Why it matters: {source.summary}")
            lines.append(f"   URL: {source.url}")

    return "\n".join(lines)


def merge_provenance(
    base: ResponseProvenance | None,
    *,
    tool_mode: str | None = None,
    web_sources: tuple[SourceAttribution, ...] = (),
) -> ResponseProvenance:
    """Merge request-level provenance with citations extracted from the response."""

    if base is None:
        base = build_default_provenance(tool_mode)

    sources = dedupe_sources(base.sources + web_sources)
    web_grounding_used = (
        base.web_grounding_used or tool_mode == "web_grounding" or bool(web_sources)
    )
    source_registry_used = base.source_registry_used

    if source_registry_used and web_grounding_used:
        mode: ProvenanceMode = "source_registry_and_web"
    elif source_registry_used:
        mode = "source_registry"
    elif web_grounding_used:
        mode = "web_grounding"
    else:
        mode = "model"

    return ResponseProvenance(
        mode=mode,
        source_registry_used=source_registry_used,
        web_grounding_used=web_grounding_used,
        source_registry_reason=base.source_registry_reason,
        sources=sources,
    )


def dedupe_sources(sources: tuple[SourceAttribution, ...]) -> tuple[SourceAttribution, ...]:
    """Deduplicate sources by URL while preserving stable order."""

    deduped: dict[str, SourceAttribution] = {}
    for source in sources:
        key = source.url.casefold()
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = source
            continue

        if existing.origin == "web_grounding" and source.origin == "source_registry":
            deduped[key] = source
            continue

        if len(source.title) > len(existing.title):
            deduped[key] = source

    return tuple(deduped.values())


def _from_trusted_source(source: TrustedSource) -> SourceAttribution:
    return SourceAttribution(
        title=source.title,
        url=source.url,
        domain=source.domain,
        origin="source_registry",
    )


def build_web_source(title: str, url: str) -> SourceAttribution:
    """Normalize a web-grounded citation into the shared attribution shape."""

    return SourceAttribution(
        title=title.strip() or _normalize_domain(url),
        url=url.strip(),
        domain=_normalize_domain(url),
        origin="web_grounding",
    )
