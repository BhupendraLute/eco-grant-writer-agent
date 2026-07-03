"""Integration test to trace the entire workflow and reproduce validation errors."""

import pytest
from unittest.mock import MagicMock, patch
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from grant_writer.agent import root_agent


@pytest.mark.asyncio
async def test_full_workflow_turns():
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)

    session = await session_service.create_session(app_name="test-app", user_id="user")

    # Turn 1: Initial notes
    content = types.Content(
        role="user",
        parts=[types.Part(text="Clean up local rivers in Delhi with 50 volunteers and ₹15 lakh budget.")]
    )
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)

    # Let's inspect session phase
    session = await session_service.get_session(app_name="test-app", user_id="user", session_id=session.id)
    print("Phase after Turn 1:", session.state.get("phase"))

    # Turn 2: Since intake is complete (phase=matching), let's send a search query/select to match
    content = types.Content(
        role="user",
        parts=[types.Part(text="Show me the options")]
    )
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)

    # Should be suspended at grant_selection
    is_interrupted = any(event.long_running_tool_ids for event in events)
    assert is_interrupted

    # Resume: Select grant Option A
    interrupt_id = ""
    for event in events:
        if event.long_running_tool_ids:
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "adk_request_input":
                    interrupt_id = part.function_call.id

    content = types.Content(
        role='user',
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=interrupt_id,
                    name="adk_request_input",
                    response={"result": "A"}
                )
            )
        ]
    )
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)

    # After matching, it goes to drafting
    session = await session_service.get_session(app_name="test-app", user_id="user", session_id=session.id)
    print("Phase after matching:", session.state.get("phase"))
