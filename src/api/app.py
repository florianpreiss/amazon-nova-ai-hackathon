"""
KODA API — orchestrates the multi-agent system.

Flow: User message → Router (triage) + Crisis Radar (parallel) → Domain Agent → Response.
Sessions are ephemeral. No persistent user data.
"""

from contextlib import asynccontextmanager

from config.settings import CORS_ALLOWED_ORIGINS, validate_cors_origins
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.provenance import ResponseProvenance
from src.core.session_bundle import SessionBundle
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


class SessionImportResponse(BaseModel):
    session_id: str
    language: str
    message_count: int


# ── Endpoints ──────────────────────────────────────


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    result = chat_service.respond(
        request.message,
        session_id=request.session_id,
        ui_language=request.language,
    )

    return ChatResponse(
        session_id=result.session_id,
        response=result.response,
        agent_used=result.agent,
        crisis_detected=result.crisis,
        crisis_resources=result.crisis_resources,
        provenance=result.provenance,
    )


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """Destroy a session explicitly."""
    chat_service.end_session(session_id)
    return {"status": "deleted"}


@app.get("/api/session/{session_id}/export", response_model=SessionBundle)
async def export_session(session_id: str):
    """Export a user-owned session bundle for later continuation."""
    bundle = chat_service.export_session_bundle(session_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return bundle


@app.post("/api/session/import", response_model=SessionImportResponse)
async def import_session(bundle: SessionBundle):
    """Import a previously downloaded user-owned session bundle."""
    try:
        imported = chat_service.import_session_bundle(bundle)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SessionImportResponse(
        session_id=imported.session_id,
        language=imported.ui_language,
        message_count=imported.snapshot.message_count,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "agents": list(chat_service.agent_keys)}
