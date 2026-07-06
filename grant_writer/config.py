"""Centralized configuration for the Eco Grant Writer agent.

Single source of truth for environment loading, model selection,
input limits, timeouts, and path resolution.
"""

import os
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment Loading
# ---------------------------------------------------------------------------

def load_env() -> None:
    """Parses and loads variables from .env files into os.environ.

    Searches multiple candidate paths to handle different launch contexts
    (package dir, project root, cwd). Skips comments and blank lines.
    """
    base_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(base_dir)
    candidate_paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(project_root, ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            val = value.strip().strip("'").strip('"')
                            os.environ[key.strip()] = val
            except Exception as exc:
                logger.warning("Failed to load .env from %s: %s", path, exc)


# Load credentials at import time
load_env()

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

LLM_MODEL: str = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
"""Model identifier used for all Gemini API calls."""

# ---------------------------------------------------------------------------
# Agent Limits
# ---------------------------------------------------------------------------

MAX_INPUT_LENGTH: int = 15_000
"""Maximum characters accepted in a single user message."""

MAX_REACT_ITERATIONS: int = 3
"""Maximum self-correction iterations in the ReAct drafting loop."""

MAX_SECTIONS_PER_TURN: int = 5
"""Maximum proposal sections drafted in a single turn."""

# ---------------------------------------------------------------------------
# MCP Configuration
# ---------------------------------------------------------------------------

MCP_TIMEOUT_SECONDS: float = 30.0
"""Timeout for MCP server subprocess connections."""

# ---------------------------------------------------------------------------
# Path Helpers
# ---------------------------------------------------------------------------

def resolve_project_path(filename: str) -> str:
    """Resolves a filename relative to the project root (parent of grant_writer/).

    Falls back to checking the grant_writer/ directory and cwd.
    """
    base_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(base_dir)
    candidates = [
        os.path.join(project_root, filename),
        os.path.join(base_dir, filename),
        os.path.join(os.getcwd(), filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Return the project root path even if it doesn't exist yet
    return os.path.join(project_root, filename)


def get_python_executable() -> str:
    """Finds the python executable in the local virtual environment .venv.

    Falls back to sys.executable if not found.
    """
    import sys
    base_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(base_dir)

    # Check Windows virtualenv
    win_py = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    if os.path.exists(win_py):
        return win_py

    # Check Unix virtualenv
    unix_py = os.path.join(project_root, ".venv", "bin", "python")
    if os.path.exists(unix_py):
        return unix_py

    return sys.executable


PYTHON_EXECUTABLE: str = get_python_executable()

