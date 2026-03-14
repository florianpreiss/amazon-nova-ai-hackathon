"""
Curated source registry for trusted, domain-specific guidance.

This module ships a Germany-focused registry of hand-curated sources.
The selection policy intentionally prefers those sources only for
German-language requests or explicitly Germany-focused questions.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

SourceCategory = Literal["FINANCING", "STUDY_CHOICE", "ACADEMIC_BASICS", "ROLE_MODELS"]
SourceKind = Literal["official", "community", "editorial", "directory", "tool"]
SelectionReason = Literal["language_match", "germany_focus", "policy_not_matched"]

TRUSTED_SOURCES_DIR = Path(__file__).resolve().parent / "trusted_sources"
GERMANY_FOCUS_KEYWORDS = (
    "germany",
    "german university",
    "german universities",
    "study in germany",
    "university in germany",
    "universities in germany",
    "deutschland",
    "deutsch",
    "studium in deutschland",
    "bafoeg",
    "hochschulstart",
    "studierendenwerk",
    "abitur",
    "fachhochschule",
    "duales studium",
)


def _normalize_text(text: str) -> str:
    translation = str.maketrans(
        {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
        }
    )
    lowered = text.casefold().translate(translation)
    return re.sub(r"\s+", " ", lowered).strip()


def _normalize_domain(value: str) -> str:
    return value.casefold().removeprefix("www.").strip()


class TrustedSource(BaseModel):
    """A single curated source entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    category: SourceCategory
    sheet_name: str
    title: str
    summary: str = ""
    url: str
    domain: str
    language: str
    country_codes: tuple[str, ...]
    source_kind: SourceKind
    audience: tuple[str, ...]
    trust_tier: Literal["curated_registry"]
    origin: Literal["source_registry"]

    @field_validator("id", "sheet_name", "title", "url")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("summary")
    @classmethod
    def _normalize_summary(cls, value: str) -> str:
        return value.strip()

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str) -> str:
        value = value.strip().casefold()
        if not value:
            raise ValueError("language must not be blank")
        return value

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, value: str) -> str:
        value = _normalize_domain(value)
        if not value:
            raise ValueError("domain must not be blank")
        return value

    @field_validator("country_codes")
    @classmethod
    def _normalize_country_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(code.strip().upper() for code in value if code.strip())
        if not normalized:
            raise ValueError("country_codes must not be empty")
        return normalized

    @field_validator("audience")
    @classmethod
    def _normalize_audience(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value if item.strip())
        if not normalized:
            raise ValueError("audience must not be empty")
        return normalized

    @model_validator(mode="after")
    def _ensure_domain_matches_url(self) -> TrustedSource:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute http(s) URL")
        url_domain = _normalize_domain(parsed.netloc)
        if url_domain != self.domain:
            raise ValueError(f"domain '{self.domain}' does not match url domain '{url_domain}'")
        return self


class TrustedSourceManifest(BaseModel):
    """A versioned manifest of curated sources."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    registry_id: str
    version: int
    description: str
    default_languages: tuple[str, ...]
    country_codes: tuple[str, ...]
    sources: tuple[TrustedSource, ...]

    @field_validator("registry_id", "description")
    @classmethod
    def _manifest_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("manifest value must not be blank")
        return value

    @field_validator("default_languages")
    @classmethod
    def _normalize_default_languages(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip().casefold() for item in value if item.strip())
        if not normalized:
            raise ValueError("default_languages must not be empty")
        return normalized

    @field_validator("country_codes")
    @classmethod
    def _normalize_manifest_country_codes(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(code.strip().upper() for code in value if code.strip())
        if not normalized:
            raise ValueError("country_codes must not be empty")
        return normalized


class SourceSelectionContext(BaseModel):
    """Context used to decide if curated sources should be preferred."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_language: str = "en"
    user_message: str = ""
    country_code: str | None = None

    @field_validator("user_language")
    @classmethod
    def _normalize_user_language(cls, value: str) -> str:
        value = value.strip().casefold()
        if not value:
            raise ValueError("user_language must not be blank")
        return value

    @field_validator("user_message")
    @classmethod
    def _normalize_user_message(cls, value: str) -> str:
        return value.strip()

    @field_validator("country_code")
    @classmethod
    def _normalize_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        return value or None


class TrustedSourceSelection(BaseModel):
    """The outcome of a curated source selection decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    use_registry: bool
    reason: SelectionReason
    sources: tuple[TrustedSource, ...]


@lru_cache(maxsize=1)
def load_trusted_source_manifests() -> tuple[TrustedSourceManifest, ...]:
    """Load and validate all curated source manifests from disk."""

    manifests: list[TrustedSourceManifest] = []
    for path in sorted(TRUSTED_SOURCES_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifests.append(TrustedSourceManifest.model_validate(payload))
    return tuple(manifests)


@lru_cache(maxsize=1)
def get_trusted_sources(category: SourceCategory | None = None) -> tuple[TrustedSource, ...]:
    """Return all curated sources, optionally filtered by category."""

    sources = tuple(
        source
        for manifest in load_trusted_source_manifests()
        for source in manifest.sources
        if category is None or source.category == category
    )
    return sources


def should_use_trusted_sources(context: SourceSelectionContext) -> tuple[bool, SelectionReason]:
    """
    Decide whether curated sources should be preferred for this request.

    The current registry is Germany-specific and German-language. We therefore
    prefer it only when the user writes in German or the request is explicitly
    about Germany.
    """

    if context.user_language.startswith("de"):
        return True, "language_match"

    if context.country_code == "DE":
        return True, "germany_focus"

    normalized_message = _normalize_text(context.user_message)
    if any(keyword in normalized_message for keyword in GERMANY_FOCUS_KEYWORDS):
        return True, "germany_focus"

    return False, "policy_not_matched"


def select_trusted_sources(
    context: SourceSelectionContext,
    category: SourceCategory | None = None,
    limit: int | None = None,
) -> TrustedSourceSelection:
    """Return curated sources if the selection policy applies."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")

    use_registry, reason = should_use_trusted_sources(context)
    if not use_registry:
        return TrustedSourceSelection(use_registry=False, reason=reason, sources=())

    sources = get_trusted_sources(category)
    if limit is not None:
        sources = sources[:limit]
    return TrustedSourceSelection(use_registry=True, reason=reason, sources=sources)
