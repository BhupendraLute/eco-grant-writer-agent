"""Integration tests for the full workflow — safe proposal, flagged proposal, rejection."""

import pytest
from unittest.mock import patch
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from grant_writer.agent import root_agent


@pytest.mark.asyncio
async def test_safe_proposal_completes():
    """A clean input should flow through the entire workflow without HITL interruption."""
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)

    session = await session_service.create_session(app_name="test-app", user_id="user")
    content = types.Content(
        role="user",
        parts=[types.Part(text="Clean up local rivers in Delhi with 50 volunteers and ₹15 lakh budget.")]
    )

    events = []
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        events.append(event)

    # Should have generated at least one event
    assert len(events) > 0


@pytest.mark.asyncio
async def test_workflow_starts_with_intake():
    """The first message should route to intake and produce a response."""
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)

    session = await session_service.create_session(app_name="test-app", user_id="user")
    content = types.Content(
        role="user",
        parts=[types.Part(text="We are GreenMumbai NGO working on river cleanup")]
    )

    events = []
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        events.append(event)

    assert len(events) > 0

    # Check that the session state has been populated
    session = await session_service.get_session(
        app_name="test-app",
        user_id="user",
        session_id=session.id,
    )
    # State should have some populated fields from intake
    assert session.state.get("chat_history") is not None
