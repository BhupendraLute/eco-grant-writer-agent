"""Show proposal node — displays the current draft to the user."""

import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

logger = logging.getLogger(__name__)


@node
async def ShowProposal(ctx: Context, node_input=None):
    """Shows the latest drafted proposal if it exists in the workflow state."""
    proposal = ctx.state.get("drafted_proposal")
    phase = ctx.state.get("phase", "intake")

    if not proposal:
        # Show partial progress if sections exist
        sections = ctx.state.get("sections_drafted", {})
        if sections:
            parts = []
            for name, content in sections.items():
                parts.append(f"## {name}\n\n{content}")
            partial = "\n\n---\n\n".join(parts)
            msg = f"📝 Here are the sections drafted so far:\n\n{partial}"
        else:
            msg = (
                "📋 No proposal has been drafted yet.\n\n"
                "Please provide your project notes to get started, or select a grant program."
            )
    else:
        msg = f"📄 Here is the latest drafted proposal:\n\n{proposal}"

    logger.info("ShowProposal: Displayed proposal (phase=%s)", phase)
    return types.Content(parts=[types.Part(text=msg)])
