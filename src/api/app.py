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

from src.agents.academic_basics.hidden_curriculum import HiddenCurriculumAgent
from src.agents.compass import CompassAgent
from src.agents.crisis import CrisisRadar
from src.agents.financing.student_aid import StudentAidAgent
from src.agents.role_models.anti_impostor import AntiImpostorAgent
from src.agents.router import RouterAgent
from src.agents.study_choice.degree_explorer import DegreeExplorerAgent
from src.core.conversation import Conversation

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

# ── Agent registry ─────────────────────────────────

router_agent = RouterAgent()
crisis_radar = CrisisRadar()

AGENTS = {
    "COMPASS": CompassAgent(),
    "FINANCING": StudentAidAgent(),
    "STUDY_CHOICE": DegreeExplorerAgent(),
    "ACADEMIC_BASICS": HiddenCurriculumAgent(),
    "ROLE_MODELS": AntiImpostorAgent(),
}

# ── Session store (in-memory, ephemeral) ───────────

sessions: dict[str, Conversation] = {}

# ── Request / Response schemas ─────────────────────


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent_used: str
    crisis_detected: bool
    crisis_resources: dict | None = None


# ── Endpoints ──────────────────────────────────────


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    conv = _get_or_create_session(request.session_id)
    conv.add_user_message(request.message)

    # 1. Crisis Radar (parallel in production)
    crisis = crisis_radar.scan(request.message)

    # 2. Route to domain agent
    agent_key = router_agent.route(request.message)
    agent = AGENTS.get(agent_key, AGENTS["COMPASS"])

    # 3. Generate response
    text = agent.respond(conv.get_messages(), conv.metadata)

    # 4. Prepend crisis resources if triggered
    if crisis["is_crisis"] and crisis["resources"]:
        text = _format_crisis_prefix(crisis["resources"]) + text

    # 5. Store and return
    conv.add_assistant_message(text)
    conv.metadata["current_agent"] = agent_key

    return ChatResponse(
        session_id=conv.session_id,
        response=text,
        agent_used=agent_key,
        crisis_detected=crisis["is_crisis"],
        crisis_resources=crisis.get("resources"),
    )


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    """Destroy a session explicitly."""
    sessions.pop(session_id, None)
    return {"status": "deleted"}


@app.get("/api/health")
async def health():
    return {"status": "ok", "agents": list(AGENTS.keys())}


# ── Helpers ────────────────────────────────────────


def _get_or_create_session(session_id: str | None) -> Conversation:
    if session_id and session_id in sessions:
        conv = sessions[session_id]
        if not conv.is_expired():
            return conv
        del sessions[session_id]
    conv = Conversation()
    sessions[conv.session_id] = conv
    return conv


def _format_crisis_prefix(resources: dict) -> str:
    lines = ["⚠️ I notice you may be going through a difficult time. Here are immediate resources:"]
    for value in resources.values():
        lines.append(f"• {value}")
    lines.append("")
    return "\n".join(lines) + "\n"
