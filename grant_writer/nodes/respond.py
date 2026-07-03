"""Direct response node for supervisor orchestrator greetings/out-of-scope replies."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

from grant_writer.models import ChatMessage

logger = logging.getLogger(__name__)


@node
async def RespondDirectly(ctx: Context, node_input: str | None = None):
    """Directly replies to the user for greetings or out-of-scope requests."""
    chat_history = ctx.state.get("chat_history", [])
    reply = ctx.state.get("respond_reply", "I'm sorry, I can only help you draft environmental grant proposals.")

    # Append direct reply to chat history
    chat_history.append(ChatMessage(role="assistant", content=reply))
    ctx.state["chat_history"] = chat_history

    response_data = {
        "message": reply,
        "options": ["Search matching grants", "Help me draft a section"],
    }

    logger.info("RespondDirectly: Dispatched direct response to user")
    return types.Content(parts=[types.Part(text=json.dumps(response_data))])
