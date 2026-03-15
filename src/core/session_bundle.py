"""Portable export/import format for user-owned session memory bundles."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.conversation import SessionMemorySnapshot
from src.core.provenance import ResponseProvenance, SourceAttribution

SESSION_BUNDLE_TYPE: Final[Literal["koda_session_memory"]] = "koda_session_memory"
SESSION_BUNDLE_VERSION: Final[Literal["1.0"]] = "1.0"
MAX_SESSION_BUNDLE_BYTES = 256 * 1024


class PortableMessage(BaseModel):
    """User-owned text history that can be re-imported into a new session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["user", "assistant"]
    content: str
    agent: str | None = None
    provenance: ResponseProvenance | None = None

    @field_validator("content")
    @classmethod
    def _content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class PortableSessionState(BaseModel):
    """Portable subset of ephemeral session state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    current_agent: str | None = None
    crisis_detected: bool = False
    topics: tuple[str, ...] = ()
    identity_context: dict[str, bool | str] = Field(default_factory=dict)
    preferences: dict[str, str] = Field(default_factory=dict)
    active_goals: tuple[str, ...] = ()
    cited_sources: tuple[SourceAttribution, ...] = ()
    profile_facts: tuple[str, ...] = ()
    conversation_overview: tuple[str, ...] = ()
    messages: tuple[PortableMessage, ...] = ()


class SessionBundle(BaseModel):
    """Versioned user-owned session memory export."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_type: Literal["koda_session_memory"] = SESSION_BUNDLE_TYPE
    schema_version: Literal["1.0"] = SESSION_BUNDLE_VERSION
    exported_at: str
    session: PortableSessionState
    checksum: str

    @field_validator("exported_at")
    @classmethod
    def _exported_at_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("exported_at must not be blank")
        return value

    @field_validator("checksum")
    @classmethod
    def _checksum_must_look_like_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("checksum must be a 64-character lowercase sha256 digest")
        return value


def build_session_bundle(
    *,
    snapshot: SessionMemorySnapshot,
    messages: list[dict[str, Any]],
    exported_at: datetime | None = None,
) -> SessionBundle:
    """Create a portable bundle from the current in-memory session."""

    session = PortableSessionState(
        current_agent=snapshot.current_agent,
        crisis_detected=snapshot.crisis_detected,
        topics=snapshot.topics,
        identity_context=snapshot.identity_context,
        preferences=snapshot.preferences,
        active_goals=snapshot.active_goals,
        cited_sources=snapshot.cited_sources,
        profile_facts=snapshot.profile_facts,
        conversation_overview=snapshot.conversation_overview,
        messages=tuple(_portable_messages_from_history(messages)),
    )
    exported_at_value = (exported_at or datetime.now(UTC)).isoformat()
    payload = {
        "bundle_type": SESSION_BUNDLE_TYPE,
        "schema_version": SESSION_BUNDLE_VERSION,
        "exported_at": exported_at_value,
        "session": session.model_dump(mode="json"),
    }
    checksum = _compute_checksum(payload)
    return SessionBundle.model_validate({**payload, "checksum": checksum})


def serialize_session_bundle(bundle: SessionBundle) -> bytes:
    """Return a UTF-8 JSON representation suitable for download."""

    content = json.dumps(
        bundle.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return content.encode("utf-8")


def parse_session_bundle(payload: bytes | str | dict[str, Any]) -> SessionBundle:
    """Validate and checksum-check a portable session bundle."""

    data = _coerce_payload_to_dict(payload)
    bundle = SessionBundle.model_validate(data)
    expected_checksum = _compute_checksum(_bundle_body_without_checksum(bundle))
    if bundle.checksum != expected_checksum:
        raise ValueError("Invalid session bundle checksum.")
    return bundle


def portable_messages_to_history(messages: tuple[PortableMessage, ...]) -> list[dict[str, Any]]:
    """Convert portable messages back into the chat-history shape used by the app."""

    history: list[dict[str, Any]] = []
    for message in messages:
        entry: dict[str, Any] = {
            "role": message.role,
            "content": message.content,
        }
        if message.agent:
            entry["agent"] = message.agent
        if message.provenance is not None:
            entry["provenance"] = message.provenance.model_dump(mode="python")
        history.append(entry)
    return history


def _portable_messages_from_history(messages: list[dict[str, Any]]) -> list[PortableMessage]:
    portable: list[PortableMessage] = []
    for message in messages:
        role = str(message.get("role", "user")).strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = _extract_text(message.get("content", ""))
        if not content:
            continue

        payload: dict[str, Any] = {"role": role, "content": content}
        agent = message.get("agent")
        if isinstance(agent, str) and agent.strip():
            payload["agent"] = agent.strip()

        provenance = message.get("provenance")
        if isinstance(provenance, ResponseProvenance):
            payload["provenance"] = provenance
        elif isinstance(provenance, dict):
            payload["provenance"] = ResponseProvenance.model_validate(provenance)

        portable.append(PortableMessage.model_validate(payload))
    return portable


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            text = str(block.get("text", "")).strip()
            if text:
                parts.append(text)
        return " ".join(parts).strip()
    return ""


def _coerce_payload_to_dict(payload: bytes | str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, bytes):
        if len(payload) > MAX_SESSION_BUNDLE_BYTES:
            raise ValueError("Session bundle is too large.")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Session bundle must be valid UTF-8 JSON.") from exc
    else:
        text = payload
        if len(text.encode("utf-8")) > MAX_SESSION_BUNDLE_BYTES:
            raise ValueError("Session bundle is too large.")

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Session bundle must be valid JSON.") from exc

    if not isinstance(raw, dict):
        raise ValueError("Session bundle root must be a JSON object.")
    return raw


def _bundle_body_without_checksum(bundle: SessionBundle) -> dict[str, Any]:
    body = bundle.model_dump(mode="json")
    body.pop("checksum", None)
    return body


def _compute_checksum(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
