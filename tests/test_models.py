"""Unit tests for state models."""

import pytest

from grant_writer.models import GrantWriterState, ChatMessage


class TestChatMessage:
    def test_basic_creation(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_serialization(self):
        msg = ChatMessage(role="assistant", content="Draft ready")
        data = msg.model_dump()
        assert data == {"role": "assistant", "content": "Draft ready"}


class TestGrantWriterState:
    def test_defaults(self):
        state = GrantWriterState()
        assert state.phase == "intake"
        assert state.raw_notes == ""
        assert state.budget_amount == 0.0
        assert state.currency == "INR"
        assert state.currency_symbol == "₹"
        assert state.chat_history == []
        assert state.sections_drafted == {}
        assert state.mandatory_sections == []
        assert not state.intake_complete
        assert not state.grant_confirmed
        assert not state.is_compliant
        assert not state.security_approved

    def test_phase_tracking(self):
        state = GrantWriterState(phase="drafting")
        assert state.phase == "drafting"

    def test_chat_history(self):
        state = GrantWriterState(
            chat_history=[
                ChatMessage(role="user", content="My notes"),
                ChatMessage(role="assistant", content="Got it!"),
            ]
        )
        assert len(state.chat_history) == 2
        assert state.chat_history[0].role == "user"

    def test_sections_drafted(self):
        state = GrantWriterState(
            sections_drafted={
                "Executive Summary": "A great project",
                "Budget": "₹15,00,000",
            }
        )
        assert len(state.sections_drafted) == 2
        assert "Executive Summary" in state.sections_drafted
