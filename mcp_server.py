"""MCP Server — serves grant requirements from a local JSON database.

Exposes two tools via stdio transport:
- get_grant_guidelines: Fetches requirements for a specific grant
- list_available_grants: Returns all available grant programs
"""

import json
import logging
import os
import sys

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Initialize the FastMCP server
mcp = FastMCP("GrantRequirementsServer")

# Path to the JSON file
REQUIREMENTS_FILE = os.path.join(os.path.dirname(__file__), "grant_requirements.json")


def _load_grants() -> list[dict]:
    """Loads and validates grant data from the requirements file."""
    if not os.path.exists(REQUIREMENTS_FILE):
        sys.stderr.write(f"Error: Requirements file not found at {REQUIREMENTS_FILE}\n")
        return []
    try:
        with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        grants = data.get("grants", [])
        # Basic schema validation
        for grant in grants:
            if "grant_name" not in grant or "grant_id" not in grant:
                sys.stderr.write(f"Warning: Grant missing required fields: {grant}\n")
        return grants
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Error: Invalid JSON in requirements file: {exc}\n")
        return []
    except Exception as exc:
        sys.stderr.write(f"Error reading requirements file: {exc}\n")
        return []


@mcp.tool()
def list_available_grants() -> str:
    """Returns a JSON array of all available grant programs with their names, IDs, and deadlines.

    This tool requires no arguments and returns summary information
    for all grants in the database.
    """
    sys.stderr.write("Log: Received request to list all grants\n")
    sys.stderr.flush()

    grants = _load_grants()
    if not grants:
        return "[]"

    summaries = []
    for grant in grants:
        summaries.append({
            "grant_id": grant.get("grant_id", ""),
            "grant_name": grant.get("grant_name", ""),
            "issuing_agency": grant.get("issuing_agency", ""),
            "deadline": grant.get("deadline", ""),
            "max_budget_inr": grant.get("requirements", {}).get("max_budget_inr", 0),
        })

    return json.dumps(summaries, indent=2)


@mcp.tool()
def get_grant_guidelines(grant_name: str) -> str:
    """Retrieves specific requirements and guidelines for a given grant name or ID.

    Args:
        grant_name: The name or ID of the grant (e.g. 'Regional Waterway Restoration Fund', 'ENV-2026-RIVER').
    """
    # Log to stderr to avoid corrupting stdio JSON-RPC transport protocol
    sys.stderr.write(f"Log: Received request for grant: {grant_name}\n")
    sys.stderr.flush()

    grants = _load_grants()
    if not grants:
        return f"Error: No grants available in database."

    search_query = grant_name.strip().lower()

    # Try exact match first, then collect partial matches
    matches = []
    for grant in grants:
        gid = str(grant.get("grant_id", "")).lower()
        gname = str(grant.get("grant_name", "")).lower()

        if search_query == gid or search_query == gname:
            # Exact match, return immediately
            return json.dumps(grant, indent=2)

        if search_query in gid or search_query in gname:
            matches.append(grant)

    if len(matches) == 1:
        return json.dumps(matches[0], indent=2)
    elif len(matches) > 1:
        matched_list = ", ".join(
            f"'{g.get('grant_name')}' ({g.get('grant_id')})" for g in matches
        )
        return f"Multiple grants matched your query: {matched_list}. Please be more specific."
    else:
        all_options = ", ".join(
            f"'{g.get('grant_name')}' ({g.get('grant_id')})" for g in grants
        )
        return f"Grant '{grant_name}' not found. Available grants: {all_options}"


if __name__ == "__main__":
    # Runs on stdio transport by default
    mcp.run(transport="stdio")
