"""Unit tests for the supervisor orchestrator node using MockContext."""

import pytest
from grant_writer.nodes.router import Router
from grant_writer.models import GrantWriterState


class MockContext:
    """Mock Context for node unit tests."""

    def __init__(self, state: dict):
        self.state = state
        self.route = None


@pytest.mark.asyncio
async def test_orchestrator_greeting():
    ctx = MockContext(state=GrantWriterState().model_dump())

    # Send a greet message
    res = await Router._func(ctx, "Hello there!")

    assert ctx.route == "respond"
    assert "Hello!" in ctx.state.get("respond_reply", "")
    assert len(ctx.state.get("chat_history", [])) == 1


@pytest.mark.asyncio
async def test_orchestrator_general_question():
    ctx = MockContext(state=GrantWriterState().model_dump())

    # Send an out-of-scope trivia question
    res = await Router._func(ctx, "What is the capital of France?")

    assert ctx.route == "respond"
    assert "only help" in ctx.state.get("respond_reply", "")


@pytest.mark.asyncio
async def test_orchestrator_notes_routing():
    ctx = MockContext(state=GrantWriterState().model_dump())

    # Send project notes
    res = await Router._func(ctx, "We are launching a tree plantation drive.")

    assert ctx.route == "intake"


@pytest.mark.asyncio
async def test_orchestrator_show_routing():
    ctx = MockContext(state=GrantWriterState(drafted_proposal="Full draft content").model_dump())

    # Send request to view proposal
    res = await Router._func(ctx, "Show me the proposal.")

    assert ctx.route == "show"
