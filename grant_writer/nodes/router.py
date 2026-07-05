"""Router node — supervisor orchestrator routing logic."""

import json
import logging
import re

from google.adk.workflow import node
from google.adk.agents.context import Context

from grant_writer.config import MAX_INPUT_LENGTH
from grant_writer.models import ChatMessage
from grant_writer.llm import generate_json
from grant_writer.prompts.orchestrator import ORCHESTRATOR_PROMPT

logger = logging.getLogger(__name__)


@node
async def Router(ctx: Context, node_input: str | None = None):
    """Supervisor orchestrator node that classifies user intent and routes dynamically.

    Intents:
        - "greet" / "general" → Routes to RespondDirectly
        - "show" → Routes to ShowProposal
        - "intake" → Routes to IntakeInterview
        - "match" → Routes to GrantMatcher
        - "draft" → Routes to SectionDrafter
    """
    node_input = node_input or ""

    # Input validation
    if not node_input or not node_input.strip():
        logger.warning("Empty input received")
        ctx.route = "intake"
        return node_input

    if len(node_input) > MAX_INPUT_LENGTH:
        raise ValueError(
            f"Input exceeds maximum length of {MAX_INPUT_LENGTH:,} characters "
            f"({len(node_input):,} received). Please shorten your message."
        )

    # Sanitize: strip control characters
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", node_input)

    # Append to chat history
    history = ctx.state.get("chat_history") or []
    history.append(ChatMessage(role="user", content=sanitized))
    ctx.state["chat_history"] = history

    # Gather state parameters for LLM supervisor
    phase = ctx.state.get("phase", "intake")
    intake_complete = bool(ctx.state.get("intake_complete", False))
    target_grant = ctx.state.get("target_grant", "")
    grant_confirmed = bool(ctx.state.get("grant_confirmed", False))
    mandatory = ctx.state.get("mandatory_sections", [])
    drafted = ctx.state.get("sections_drafted", {})
    proposal = ctx.state.get("drafted_proposal", "")

    # LLM intent classification
    try:
        orchestrator_prompt = ORCHESTRATOR_PROMPT.format(
            phase=phase,
            intake_complete=intake_complete,
            target_grant=target_grant or "None",
            grant_confirmed=grant_confirmed,
            mandatory_sections=", ".join(mandatory) if mandatory else "None",
            sections_drafted_count=len(drafted),
            mandatory_sections_count=len(mandatory),
            drafted_proposal_present=bool(proposal),
            user_message=sanitized,
        )
        raw_json = generate_json(orchestrator_prompt, min_response_length=2)
        data = json.loads(raw_json)
        intent = str(data.get("intent", "intake")).strip().lower()
        reply = str(data.get("reply", "")).strip()
        logger.info("Orchestrator: Classified intent='%s' reason='%s'", intent, data.get("reason", ""))
    except Exception as exc:
        logger.warning("Orchestrator: LLM failed (%s), using fallback heuristics", exc)
        # Deterministic fallback
        input_lower = sanitized.lower()
        if len(sanitized.strip()) < 30 and any(w in input_lower for w in ["hello", "hi", "greetings", "hey"]):
            intent = "greet"
            reply = "Hello! 🌱 I'm your Eco Grant Writer Assistant. How can I help you draft your grant proposal?"
        elif any(w in input_lower for w in ["show", "view", "display", "proposal"]):
            intent = "show"
            reply = ""
        else:
            if phase in ("drafting", "review"):
                intent = "draft"
            elif phase == "matching":
                intent = "match"
            else:
                intent = "intake"
            reply = ""

    # Route classification
    if intent in ("greet", "general"):
        ctx.state["respond_reply"] = reply or "I'm sorry, I can only help you with environmental grant proposal drafting."
        ctx.route = "respond"
    elif intent == "show":
        ctx.route = "show"
    elif intent == "match":
        ctx.route = "match"
    elif intent == "draft":
        ctx.route = "draft"
    else:
        ctx.route = "intake"

    logger.info("Orchestrator: Routed user to '%s'", ctx.route)
    return sanitized
