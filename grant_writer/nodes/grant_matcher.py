"""Grant matcher node — connects to MCP server and matches user's project to grants."""

import asyncio
import json
import logging
import os
import sys

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.adk.events.request_input import RequestInput
from google.genai import types

from grant_writer.config import MCP_TIMEOUT_SECONDS, resolve_project_path, PYTHON_EXECUTABLE
from grant_writer.models import ChatMessage

logger = logging.getLogger(__name__)


async def _fetch_all_grants_from_mcp() -> list[dict]:
    """Connects to the MCP server and fetches all available grants."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_script = resolve_project_path("mcp_server.py")
    server_params = StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=[server_script],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(
                    "list_available_grants",
                    arguments={},
                )
                text = "".join(
                    content.text for content in response.content if hasattr(content, "text")
                )
                return json.loads(text)
    except Exception as exc:
        logger.warning("MCP list_available_grants failed: %s", exc)
        return []


async def _fetch_grant_guidelines(grant_name: str) -> str:
    """Fetches specific grant guidelines from the MCP server."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_script = resolve_project_path("mcp_server.py")
    server_params = StdioServerParameters(
        command=PYTHON_EXECUTABLE,
        args=[server_script],
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(
                    "get_grant_guidelines",
                    arguments={"grant_name": grant_name},
                )
                return "".join(
                    content.text for content in response.content if hasattr(content, "text")
                )
    except Exception as exc:
        logger.warning("MCP get_grant_guidelines failed for '%s': %s", grant_name, exc)
        return "{}"


def _score_grant(grant: dict, state: dict) -> int:
    """Scores a grant against the user's project profile."""
    score = 0
    project_lower = (
        state.get("project_summary", "") + " " +
        state.get("location", "") + " " +
        state.get("raw_notes", "")
    ).lower()

    # Match keywords from grant name
    import re
    grant_name = grant.get("grant_name", "")
    keywords = re.findall(r"\b\w{4,}\b", grant_name.lower())
    score += sum(2 for kw in keywords if kw in project_lower)

    # Match eligible locations
    for loc in grant.get("requirements", {}).get("eligible_locations", []):
        if loc.lower() in project_lower:
            score += 3

    # Budget compatibility
    max_budget = grant.get("requirements", {}).get("max_budget_inr", 0)
    user_budget = state.get("budget_amount", 0)
    if max_budget and user_budget and user_budget <= max_budget:
        score += 2

    return score


@node(rerun_on_resume=True)
async def GrantMatcher(ctx: Context, node_input: str | None = None):
    """Matches the user's project to the best-fit grant program.

    Connects to the MCP server, scores all available grants, presents
    the top matches, and asks the user to confirm their selection.
    """
    chat_history = ctx.state.get("chat_history", [])

    # Check if user is confirming a grant selection (resume from HITL)
    if ctx.resume_inputs:
        user_response = ctx.resume_inputs.get("grant_selection")
        if user_response:
            val = str(user_response.get("result", "") if isinstance(user_response, dict) else user_response).strip()
            logger.info("GrantMatcher: User selected '%s'", val)

            # The user's response should match one of the presented grants
            # Try to find the matching grant name
            target_grant = ctx.state.get("target_grant", "")
            if val.lower() in ("a", "1") or (target_grant and target_grant.lower() in val.lower()):
                ctx.state["grant_confirmed"] = True
                ctx.state["phase"] = "drafting"
            elif val.lower() in ("b", "2"):
                # Second option
                available = ctx.state.get("ranked_grants", [])
                if len(available) > 1:
                    ctx.state["target_grant"] = available[1]
                    ctx.state["grant_confirmed"] = True
                    ctx.state["phase"] = "drafting"
            else:
                ctx.state["grant_confirmed"] = True
                ctx.state["phase"] = "drafting"

            # Fetch full guidelines for confirmed grant
            if ctx.state.get("grant_confirmed"):
                grant_name = ctx.state.get("target_grant", "")
                try:
                    guidelines_json = await asyncio.wait_for(
                        _fetch_grant_guidelines(grant_name),
                        timeout=MCP_TIMEOUT_SECONDS,
                    )
                    ctx.state["target_grant_guidelines"] = guidelines_json

                    # Extract mandatory sections
                    try:
                        guidelines = json.loads(guidelines_json)
                        sections = guidelines.get("requirements", {}).get("mandatory_sections", [])
                        ctx.state["mandatory_sections"] = sections
                    except json.JSONDecodeError:
                        pass

                    logger.info("GrantMatcher: Confirmed '%s', guidelines loaded", grant_name)
                except asyncio.TimeoutError:
                    logger.error("MCP server timed out after %ss", MCP_TIMEOUT_SECONDS)

                response_data = {
                    "message": f"✅ Great choice! I'll draft your proposal for **{grant_name}**. "
                              f"Let me start with the first section.",
                    "options": ["Start drafting", "Show grant requirements first"],
                }
                chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
                ctx.state["chat_history"] = chat_history
                return types.Content(parts=[types.Part(text=json.dumps(response_data))])

    # --- Fetch and rank grants ---
    logger.info("GrantMatcher: Fetching grants from MCP server...")

    # Check for pre-selected grant (from Streamlit UI)
    pre_selected = ctx.state.get("target_grant", "")
    if pre_selected and ctx.state.get("grant_confirmed"):
        # Already confirmed, skip matching
        ctx.state["phase"] = "drafting"
        return types.Content(parts=[types.Part(text=json.dumps({
            "message": f"Using pre-selected grant: **{pre_selected}**",
            "options": ["Start drafting"],
        }))])

    # Fetch all available grants with timeout
    try:
        grants = await asyncio.wait_for(
            _fetch_all_grants_from_mcp(),
            timeout=MCP_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("MCP server timed out")
        grants = []

    # Fallback: load grants locally if MCP fails
    if not grants:
        logger.info("GrantMatcher: Using local fallback for grant list")
        try:
            req_file = resolve_project_path("grant_requirements.json")
            with open(req_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            grants = data.get("grants", [])
        except Exception as exc:
            logger.error("Failed to load local grants: %s", exc)
            grants = []

    if not grants:
        response_data = {
            "message": "⚠️ I couldn't connect to the grant database. Please try again or select a grant manually.",
            "options": [],
        }
        chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
        ctx.state["chat_history"] = chat_history
        return types.Content(parts=[types.Part(text=json.dumps(response_data))])

    # Score and rank grants
    scored = [(grant, _score_grant(grant, ctx.state)) for grant in grants]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Store top ranked names for resume handling
    top_grants = scored[:3]
    ctx.state["ranked_grants"] = [g.get("grant_name", "") for g, _ in top_grants]
    ctx.state["target_grant"] = top_grants[0][0].get("grant_name", "")

    # Build selection prompt
    options = []
    details = []
    for i, (grant, score) in enumerate(top_grants):
        name = grant.get("grant_name", "Unknown")
        agency = grant.get("issuing_agency", "")
        max_budget = grant.get("requirements", {}).get("max_budget_inr", 0)
        deadline = grant.get("deadline", "")
        options.append(name)
        marker = "⭐ " if i == 0 else ""
        details.append(
            f"{marker}**{name}**\n"
            f"   Agency: {agency}\n"
            f"   Max Budget: ₹{max_budget:,.0f}\n"
            f"   Deadline: {deadline}\n"
            f"   Match Score: {score}"
        )

    prompt_msg = (
        "🎯 I found matching grant programs for your project!\n\n"
        + "\n\n".join(details)
        + "\n\nWhich grant would you like to apply for?"
    )

    # Request user input for grant selection
    return RequestInput(
        message=prompt_msg + "\n\nPlease select:\n" + "\n".join(f"  {chr(65+i)}) {o}" for i, o in enumerate(options)),
        interrupt_id="grant_selection",
    )
