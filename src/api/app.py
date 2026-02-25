"""
KODA API — orchestrates the multi-agent system.

Flow: User message → Router (triage) + Crisis Radar (parallel) → Domain Agent → Response.
Sessions are ephemeral. No persistent user data.
"""

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

app = FastAPI(
    title="KODA API",
    description="AI Companion for First-Generation Academics",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
