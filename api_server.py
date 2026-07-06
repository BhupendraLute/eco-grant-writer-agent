"""
Eco Grant Writer — FastAPI Backend Server

Wraps the existing ADK Runner and exposes REST endpoints
for the Next.js frontend to communicate with the agent.
"""

import asyncio
import json
import logging
import re
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ADK Runner (lazy-init)
# ---------------------------------------------------------------------------

_runner = None
_session_service = None


def _init_agent():
    """Initialize the ADK workflow runner and session service (once)."""
    global _runner, _session_service

    from grant_writer.config import load_env
    load_env()

    try:
        from google.adk.runners import Runner
    except ImportError:
        from google.adk import Runner  # type: ignore[attr-defined]

    try:
        from google.adk.sessions import InMemorySessionService
    except ImportError:
        from google.adk.sessions.in_memory_session_service import InMemorySessionService  # type: ignore

    from grant_writer.agent import root_agent

    _session_service = InMemorySessionService()
    _runner = Runner(
        agent=root_agent,
        app_name="eco_grant_writer",
        session_service=_session_service,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the ADK agent on server startup."""
    _init_agent()
    logger.info("ADK Runner initialized successfully")
    yield


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Eco Grant Writer API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str
    interrupt_id: str | None = None


class SessionResponse(BaseModel):
    session_id: str


class AgentState(BaseModel):
    phase: str = "intake"
    organization_name: str = ""
    project_summary: str = ""
    location: str = ""
    budget_amount: float = 0.0
    currency: str = "INR"
    currency_symbol: str = "₹"
    ngo_registration_id: str = ""
    project_duration: str = ""
    volunteers_count: int = 0
    intake_complete: bool = False
    target_grant: str = ""
    grant_confirmed: bool = False
    mandatory_sections: list[str] = []
    sections_drafted: dict[str, str] = {}
    current_section: str = ""
    drafted_proposal: str = ""
    is_compliant: bool = False
    security_approved: bool = False


class ChatResponse(BaseModel):
    message: str
    options: list[str] = []
    option_to_val: dict[str, str] = {}
    state: AgentState
    interrupt_id: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_response(text: str) -> dict:
    """Parse agent response text into {message, options, option_to_val}."""
    if not text:
        return {"message": "Hmm, I didn't get a response. Could you try again?", "options": [], "option_to_val": {}}

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            options = list(data.get("options", []))
            return {
                "message": str(data.get("message", text)),
                "options": options,
                "option_to_val": {o: o for o in options},
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Parse letter choices (e.g., A) ..., B) ...)
    options = []
    option_to_val = {}
    matches = re.findall(r'(?:^\s*|[^\w])([A-Z])\)\s*(.+?)(?=\n|$)', text)
    if matches:
        for letter, opt in matches:
            opt_clean = opt.strip()
            if opt_clean and opt_clean not in options:
                options.append(opt_clean)
                option_to_val[opt_clean] = letter

    return {"message": text, "options": options, "option_to_val": option_to_val}


def _derive_phase(state: dict) -> str:
    """Derive the current workflow phase from state flags."""
    if state.get("phase"):
        return state["phase"]
    if state.get("security_approved") and state.get("is_compliant"):
        return "complete"
    if state.get("drafted_proposal") or state.get("sections_drafted"):
        return "drafting"
    if state.get("grant_confirmed"):
        return "drafting"
    if state.get("intake_complete"):
        return "matching"
    return "intake"


def _extract_state(state_dict: dict) -> AgentState:
    """Extract AgentState from a raw state dict."""
    fields = AgentState.model_fields.keys()
    filtered = {}
    for k in fields:
        if k in state_dict:
            filtered[k] = state_dict[k]
    # Derive phase
    filtered["phase"] = _derive_phase(state_dict)
    return AgentState(**filtered)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    """Create a new agent session."""
    if not _session_service:
        raise HTTPException(500, "Agent not initialized")

    session = await _session_service.create_session(
        app_name="eco_grant_writer",
        user_id="nextjs_user",
    )
    return SessionResponse(session_id=session.id)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the agent and receive response + state."""
    if not _runner or not _session_service:
        raise HTTPException(500, "Agent not initialized")

    from google.genai import types as gtypes
    from google.adk.events.request_input import RequestInput

    # Build the message content
    if req.interrupt_id:
        part = gtypes.Part(
            function_response=gtypes.FunctionResponse(
                id=req.interrupt_id,
                name=req.interrupt_id,
                response={"result": req.message},
            )
        )
        content = gtypes.Content(role="user", parts=[part])
    else:
        content = gtypes.Content(
            role="user",
            parts=[gtypes.Part(text=req.message)],
        )

    last_text = ""
    state_deltas: dict = {}
    interrupt_id: str | None = None

    async for event in _runner.run_async(
        session_id=req.session_id,
        user_id="nextjs_user",
        new_message=content,
    ):
        # 1. Check for HITL RequestInput
        if hasattr(event, "output") and event.output is not None:
            if isinstance(event.output, RequestInput):
                msg = event.output.message or ""
                last_text = json.dumps({"message": msg, "options": []})
                interrupt_id = event.output.interrupt_id

        # 2. Collect text or HITL inputs from Content events
        if hasattr(event, "content") and event.content:
            if hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        last_text = part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        if part.function_call.name == "adk_request_input":
                            args = part.function_call.args or {}
                            msg = args.get("message") or ""
                            last_text = json.dumps({"message": msg, "options": []})
                            interrupt_id = args.get("interruptId") or part.function_call.id

        # 3. Accumulate state deltas
        if hasattr(event, "actions") and event.actions:
            if hasattr(event.actions, "state_delta") and event.actions.state_delta:
                state_deltas.update(event.actions.state_delta)

    # Retrieve full session state
    state_dict = dict(state_deltas)
    try:
        session = await _session_service.get_session(
            app_name="eco_grant_writer",
            user_id="nextjs_user",
            session_id=req.session_id,
        )
        if hasattr(session, "state") and session.state:
            state_dict.update(dict(session.state))
    except Exception:
        pass

    parsed = _parse_response(last_text)

    # Inject compliance review choice buttons
    if interrupt_id == "compliance_review_choice":
        parsed["options"] = ["Force Approve", "Reject Draft"]
        parsed["option_to_val"] = {
            "Force Approve": "force approve",
            "Reject Draft": "reject",
        }

    agent_state = _extract_state(state_dict)

    return ChatResponse(
        message=parsed["message"],
        options=parsed.get("options", []),
        option_to_val=parsed.get("option_to_val", {}),
        state=agent_state,
        interrupt_id=interrupt_id,
    )


@app.get("/api/state/{session_id}", response_model=AgentState)
async def get_state(session_id: str):
    """Get the current state for a session."""
    if not _session_service:
        raise HTTPException(500, "Agent not initialized")

    try:
        session = await _session_service.get_session(
            app_name="eco_grant_writer",
            user_id="nextjs_user",
            session_id=session_id,
        )
        if hasattr(session, "state") and session.state:
            return _extract_state(dict(session.state))
    except Exception as e:
        raise HTTPException(404, f"Session not found: {e}")

    return AgentState()


@app.get("/api/grants")
async def list_grants():
    """List available grants from the local database."""
    grants_path = Path(__file__).parent / "grant_requirements.json"
    if not grants_path.exists():
        return {"grants": []}

    with open(grants_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Return simplified grant list
    grants = []
    if isinstance(data, dict) and "grants" in data:
        for g in data["grants"]:
            grants.append({
                "id": g.get("id", ""),
                "name": g.get("name", ""),
                "funder": g.get("funder", ""),
                "max_funding": g.get("max_funding", ""),
                "focus_areas": g.get("focus_areas", []),
            })
    elif isinstance(data, list):
        for g in data:
            grants.append({
                "id": g.get("id", ""),
                "name": g.get("name", ""),
                "funder": g.get("funder", ""),
                "max_funding": g.get("max_funding", ""),
                "focus_areas": g.get("focus_areas", []),
            })

    return {"grants": grants}


# ---------------------------------------------------------------------------
# Run with: uvicorn api_server:app --port 8000 --reload
# ---------------------------------------------------------------------------
