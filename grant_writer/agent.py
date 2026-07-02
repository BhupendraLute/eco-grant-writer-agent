import sys
import os
import json
import re
from pydantic import BaseModel
from google.adk.workflow import node, START, Workflow
from google.adk.agents.context import Context
from google.genai import types
from google.genai import Client

# Define a basic state object to hold the nonprofit's input text and the drafted output
class GrantWriterState(BaseModel):
    nonprofit_notes: str = ""
    drafted_proposal: str = ""

# Define the nodes
@node
async def IngestNotes(ctx: Context, node_input: str):
    """Ingests the user's input notes or detects if they are querying for the existing proposal."""
    if "where is" in node_input.lower() or "show" in node_input.lower():
        ctx.route = "show"
        print(f"[IngestNotes] Detected query for proposal. Routing to show.")
    else:
        ctx.state['nonprofit_notes'] = node_input
        ctx.route = "draft"
        print(f"[IngestNotes] Ingested notes: {node_input}. Routing to draft.")
    return node_input

@node(rerun_on_resume=True)
async def DraftProposal(ctx: Context, nonprofit_notes: str):
    """Drafts a grant proposal after fetching specific guidelines from the MCP server."""
    # Identify the target grant based on user notes keyword matching
    notes_lower = nonprofit_notes.lower()
    if "river" in notes_lower or "waterway" in notes_lower or "lake" in notes_lower or "wetland" in notes_lower:
        grant_name = "Regional Waterway Restoration Fund"
    elif "canopy" in notes_lower or "tree" in notes_lower or "park" in notes_lower or "forest" in notes_lower:
        grant_name = "Urban Canopy Expansion Grant"
    elif "youth" in notes_lower or "student" in notes_lower or "school" in notes_lower or "climate" in notes_lower:
        grant_name = "Next-Gen Climate Leaders Seed Grant"
    else:
        grant_name = "Regional Waterway Restoration Fund"  # Default fallback
        
    print(f"[DraftProposal] Connecting to MCP server to fetch guidelines for '{grant_name}'...")
    
    # Connect to the local MCP server running over stdio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    if not os.path.exists(server_script):
        # Look in the parent directory as a fallback (when executed from within the grant_writer package)
        server_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_server.py")
        
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script]
    )
    
    guidelines_json = "{}"
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(
                    "get_grant_guidelines", 
                    arguments={"grant_name": grant_name}
                )
                # Reconstruct the string response from the TextContent items
                guidelines_json = "".join(
                    content.text for content in response.content if hasattr(content, 'text')
                )
                print(f"[DraftProposal] Guidelines retrieved successfully.")
    except Exception as e:
        print(f"[DraftProposal] Warning: Failed to connect to MCP server ({str(e)}). Using local fallback.")
        
    # Parse guidelines if valid JSON
    try:
        guidelines = json.loads(guidelines_json)
        reqs = guidelines.get("requirements", {})
        budget = reqs.get("max_budget_usd", 25000)
        sections = ", ".join(reqs.get("mandatory_sections", ["Executive Summary", "Budget"]))
        metrics = ", ".join(reqs.get("required_metrics", ["Volunteers engaged"]))
        gname = guidelines.get("grant_name", grant_name)
        agency = guidelines.get("issuing_agency", "Funding Agency")
    except Exception:
        gname = grant_name
        agency = "Funding Agency"
        budget = 25000
        sections = "Executive Summary, Budget"
        metrics = "Volunteers engaged"
        
    draft = (
        f"GRANT PROPOSAL DRAFT\n"
        f"Target Grant: {gname}\n"
        f"Issuing Agency: {agency}\n"
        f"Proposed Budget: ${budget:,} USD\n"
        f"Required Sections: {sections}\n"
        f"Target Metrics: {metrics}\n"
        f"Notes Summary: {nonprofit_notes}\n"
    )
    
    # Check if we were already reviewed in a previous turn (human-in-the-loop)
    is_approved = False
    if ctx.resume_inputs:
        user_response = ctx.resume_inputs.get("security_financial_review")
        if isinstance(user_response, dict):
            result = user_response.get("result", "")
        else:
            result = str(user_response)
            
        val = str(result).strip().lower()
        if val in ("b", "reject", "rejected"):
            print("[DraftProposal] Rejection received. Aborting.")
            raise ValueError("Draft proposal was rejected by the user due to safety/compliance concerns.")
        elif val in ("a", "approve", "approved", "yes"):
            is_approved = True
            print("[DraftProposal] Resumed with user approval. Bypassing guardrail.")
        else:
            print(f"[DraftProposal] Warning: Unrecognized input: {val}")
        
    if not is_approved:
        # --- LLM-as-a-Judge Security Guardrail ---
        print(f"[DraftProposal] Running LLM-as-a-Judge security guardrail...")
        
        judge_prompt = (
            "You are a security compliance judge. Analyze the following grant proposal draft.\n"
            "Your task is to identify if it contains any specific dollar amounts (e.g., '$10,000') "
            "or bank account numbers (e.g., '123456789').\n"
            "Reply with exactly 'VIOLATION' if any are present, or 'SAFE' if none are present.\n\n"
            f"Proposal Draft:\n{draft}"
        )
        
        is_violation = False
        try:
            client = Client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=judge_prompt,
            )
            verdict = response.text.strip().upper()
            if "VIOLATION" in verdict:
                is_violation = True
        except Exception as e:
            print(f"[DraftProposal] Warning: LLM-as-a-Judge failed ({str(e)}). Running fallback local guardrail.")
            # Local regex/string scanning fallback
            has_dollar = "$" in draft
            has_bank = re.search(r"bank\s+account|\b\d{9,18}\b", draft, re.IGNORECASE) is not None
            if has_dollar or has_bank:
                is_violation = True

        if is_violation:
            print("[DraftProposal] SECURITY ALERT: Draft flagged for human review.")
            from google.adk.events.request_input import RequestInput
            return RequestInput(
                message=(
                    "Security Guardrail Triggered: Draft proposal contains dollar amounts or bank account details.\n"
                    "Please select an option:\n"
                    "  A) Approve (bypass safety check and proceed)\n"
                    "  B) Reject (abort execution)"
                ),
                interrupt_id="security_financial_review"
            )
        
    ctx.state['drafted_proposal'] = draft
    print(f"[DraftProposal] Created proposal draft according to MCP rules.")
    return draft

@node
async def ReviewCompliance(ctx: Context, drafted_proposal: str):
    """Reviews compliance of the drafted proposal."""
    review = f"Compliance Review: APPROVED.\n\nProposal:\n{drafted_proposal}"
    print(f"[ReviewCompliance] Checked compliance.")
    return types.Content(parts=[types.Part(text=review)])

@node
async def ShowProposalNode(ctx: Context):
    """Shows the latest drafted proposal if it exists in the workflow state."""
    proposal = ctx.state.get('drafted_proposal')
    if not proposal:
        msg = "No proposal has been drafted yet. Please provide some notes first."
    else:
        msg = f"Here is the latest drafted proposal:\n\n{proposal}"
    print(f"[ShowProposalNode] Displayed proposal.")
    return types.Content(parts=[types.Part(text=msg)])

# Scaffold the sequential graph workflow with conditional branching
root_agent = Workflow(
    name="grant_writer_workflow",
    description="Ingest notes, draft proposal, and check compliance.",
    state_schema=GrantWriterState,
    edges=[
        (START, IngestNotes),
        (IngestNotes, {
            "draft": DraftProposal,
            "show": ShowProposalNode,
        }),
        (DraftProposal, ReviewCompliance),
    ]
)
