import pytest
import asyncio
from unittest.mock import MagicMock, patch
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from grant_writer.agent import root_agent

@pytest.fixture(autouse=True)
def mock_gemini():
    """Mocks the google.genai.Client to simulate the LLM-as-a-Judge model."""
    with patch("grant_writer.agent.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        def mock_generate_content(model, contents):
            mock_resp = MagicMock()
            # Split the contents to extract only the draft portion (ignoring prompt instructions)
            parts = contents.split("Proposal Draft:\n")
            draft_content = parts[1] if len(parts) > 1 else contents
            
            # The template itself includes the general budget once (e.g., "$25,000").
            # If '$' appears more than once in the draft content, it means a dollar amount was leaked.
            dollar_count = draft_content.count("$")
            has_bank = "bank account" in draft_content.lower()
            
            if dollar_count > 1 or has_bank:
                mock_resp.text = "VIOLATION"
            else:
                mock_resp.text = "SAFE"
            return mock_resp
            
        mock_client.models.generate_content.side_effect = mock_generate_content
        yield mock_client_cls

@pytest.mark.asyncio
async def test_safe_proposal():
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
    
    session = await session_service.create_session(app_name="test-app", user_id="user")
    content = types.Content(role='user', parts=[types.Part(text="Clean up the local rivers.")])
    
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)
        
    is_interrupted = any(event.long_running_tool_ids for event in events)
    assert not is_interrupted, "Safe proposal was flagged unnecessarily."

@pytest.mark.asyncio
async def test_flag_dollar_amount():
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
    
    session = await session_service.create_session(app_name="test-app", user_id="user")
    content = types.Content(role='user', parts=[types.Part(text="Waterway cleanup budget: $50,000.")])
    
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)
        
    is_interrupted = any(event.long_running_tool_ids for event in events)
    assert is_interrupted, "Draft containing dollar amount was not flagged."

@pytest.mark.asyncio
async def test_flag_bank_account():
    app = App(name="test-app", root_agent=root_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
    
    session = await session_service.create_session(app_name="test-app", user_id="user")
    content = types.Content(role='user', parts=[types.Part(text="Transfer funds to Bank Account 123456789.")])
    
    events = []
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content):
        events.append(event)
        
    is_interrupted = any(event.long_running_tool_ids for event in events)
    assert is_interrupted, "Draft containing bank account details was not flagged."
