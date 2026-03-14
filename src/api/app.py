"""
KODA API — orchestrates the multi-agent system.

Flow: User message → Router (triage) + Crisis Radar (parallel) → Domain Agent → Response.
Sessions are ephemeral. No persistent user data.
"""

from contextlib import asynccontextmanager

from config.settings import CORS_ALLOWED_ORIGINS, validate_cors_origins
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.conversation import Conversation
from src.core.provenance import ResponseProvenance
from src.orchestration import build_default_chat_service

# ── App setup ──────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle handler.

    Validates critical configuration at process start so misconfiguration
    fails loudly before accepting any traffic.
    """
    # Raises ValueError immediately if CORS origins are empty or contain '*'.
    # This prevents a silent wildcard policy from reaching production.
    validate_cors_origins(CORS_ALLOWED_ORIGINS)
    yield
    # (shutdown logic here if needed)


app = FastAPI(
    title="KODA API",
    description="AI Companion for First-Generation Academics",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    # Origins are configured via the CORS_ALLOWED_ORIGINS environment variable.
    # Default: localhost only. Override in production with the CloudFront domain.
    # OWASP A05:2021 — a wildcard '*' is intentionally prohibited here.
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["POST", "DELETE", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Shared chat service ────────────────────────────

chat_service = build_default_chat_service()

# ── Session store (in-memory, ephemeral) ───────────

sessions: dict[str, Conversation] = {}

# ── Request / Response schemas ─────────────────────


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    language: str = "en"  # BCP 47 tag; used as fallback when message language is ambiguous


class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent_used: str
    crisis_detected: bool
    crisis_resources: dict | None = None
    provenance: ResponseProvenance


# ── Endpoints ──────────────────────────────────────


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    conv = _get_or_create_session(request.session_id)
    result = chat_service.respond(
        request.message,
        conv.get_messages(),
        ui_language=request.language,
        conversation_metadata=conv.metadata,
    )
    conv.add_user_message(request.message)
    conv.add_assistant_message(result.response)
    conv.metadata["current_agent"] = result.agent
    conv.metadata["crisis_detected"] = result.crisis

    return ChatResponse(
        session_id=conv.session_id,
        response=result.response,
        agent_used=result.agent,
        crisis_detected=result.crisis,
        crisis_resources=result.crisis_resources,
        provenance=result.provenance,
    )


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """Destroy a session explicitly."""
    sessions.pop(session_id, None)
    return {"status": "deleted"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "agents": list(chat_service.agent_keys)}


def _get_or_create_session(session_id: str | None) -> Conversation:
    if session_id and session_id in sessions:
        conv = sessions[session_id]
        if not conv.is_expired():
            return conv
        del sessions[session_id]
    conv = Conversation()
    sessions[conv.session_id] = conv
    return conv
