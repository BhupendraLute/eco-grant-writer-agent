"""Final assembler node — merges sections into a submission-ready proposal."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

from grant_writer.models import ChatMessage

logger = logging.getLogger(__name__)


@node
async def FinalAssembler(ctx: Context, node_input: str | None = None):
    """Assembles all drafted sections into the final formatted proposal.

    This node runs after both compliance and security checks have passed.
    It merges the individual sections from state into a cohesive document
    and generates a congratulatory response.
    """
    sections_drafted = ctx.state.get("sections_drafted", {})
    mandatory_sections = ctx.state.get("mandatory_sections", [])
    chat_history = ctx.state.get("chat_history", [])

    grant_name = ctx.state.get("target_grant", "Grant Proposal")
    org_name = ctx.state.get("organization_name", "")
    currency_symbol = ctx.state.get("currency_symbol", "₹")
    budget = ctx.state.get("budget_amount", 0)
    currency = ctx.state.get("currency", "INR")
    location = ctx.state.get("location", "")
    duration = ctx.state.get("project_duration", "")

    # If proposal is already assembled, just return it
    existing = ctx.state.get("drafted_proposal", "")
    if existing and ctx.state.get("phase") == "complete":
        logger.info("FinalAssembler: Proposal already assembled, returning existing")
        response_data = {
            "message": "📄 Your grant proposal is finalized and ready for submission!",
            "options": ["View proposal", "Make changes", "Start new proposal"],
        }
        return types.Content(parts=[types.Part(text=json.dumps(response_data))])

    # Build the formatted proposal
    parts = [
        f"# GRANT PROPOSAL: {grant_name}\n",
    ]

    # Metadata header
    if org_name:
        parts.append(f"**Organization:** {org_name}")
    parts.append(f"**Target Grant:** {grant_name}")
    parts.append(f"**Proposed Budget:** {currency_symbol}{budget:,.0f} {currency}")
    if location:
        parts.append(f"**Location:** {location}")
    if duration:
        parts.append(f"**Duration:** {duration}")
    parts.append("\n---\n")

    # Assemble sections in order
    for section_name in mandatory_sections:
        content = sections_drafted.get(section_name)
        if content:
            parts.append(f"## {section_name}\n\n{content}\n")
        else:
            parts.append(f"## {section_name}\n\n[Section not yet drafted]\n")

    # Any extra sections not in mandatory list
    for section_name, content in sections_drafted.items():
        if section_name not in mandatory_sections:
            parts.append(f"## {section_name}\n\n{content}\n")

    full_proposal = "\n".join(parts)
    ctx.state["drafted_proposal"] = full_proposal
    ctx.state["phase"] = "complete"

    logger.info(
        "FinalAssembler: Assembled proposal (%d chars, %d sections)",
        len(full_proposal),
        len(sections_drafted),
    )

    response_data = {
        "message": (
            f"🎉 Your **{grant_name}** proposal is complete!\n\n"
            f"📊 **{len(sections_drafted)}** sections drafted\n"
            f"✅ Compliance audit passed\n"
            f"🛡️ Security checks cleared\n\n"
            f"The full proposal is ready for review in the document panel."
        ),
        "options": ["View full proposal", "Refine a section", "Start new proposal"],
    }

    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
    ctx.state["chat_history"] = chat_history

    return types.Content(parts=[types.Part(text=json.dumps(response_data))])
