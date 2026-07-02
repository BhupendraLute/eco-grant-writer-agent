import json
import os
import sys
from fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("GrantRequirementsServer")

# Path to the JSON file
REQUIREMENTS_FILE = os.path.join(os.path.dirname(__file__), "grant_requirements.json")

@mcp.tool()
def get_grant_guidelines(grant_name: str) -> str:
    """Retrieves specific requirements and guidelines for a given grant name or ID.
    
    Args:
        grant_name: The name or ID of the grant (e.g. 'Regional Waterway Restoration Fund', 'ENV-2026-RIVER').
    """
    # Log to stderr to avoid corrupting stdio JSON-RPC transport protocol
    sys.stderr.write(f"Log: Received request for grant: {grant_name}\n")
    sys.stderr.flush()
    
    if not os.path.exists(REQUIREMENTS_FILE):
        return f"Error: Requirements file not found at {REQUIREMENTS_FILE}."
        
    try:
        with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return f"Error reading requirements file: {str(e)}"
        
    grants = data.get("grants", [])
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
        matched_list = ", ".join(f"'{g.get('grant_name')}' ({g.get('grant_id')})" for g in matches)
        return f"Multiple grants matched your query: {matched_list}. Please be more specific."
    else:
        all_options = ", ".join(f"'{g.get('grant_name')}' ({g.get('grant_id')})" for g in grants)
        return f"Grant '{grant_name}' not found. Available grants: {all_options}"

if __name__ == "__main__":
    # Runs on stdio transport by default
    mcp.run(transport="stdio")
