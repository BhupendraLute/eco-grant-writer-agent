"""Shared test fixtures and mocks for the Eco Grant Writer test suite."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_gemini():
    """Mocks the google.genai.Client to simulate LLM calls across all tests.

    Handles:
    - Drafting calls (returns mock proposal text)
    - Security judge calls (checks for leaked financial data)
    - Compliance auditor calls (returns APPROVED)
    - JSON-mode calls (returns valid JSON)
    """
    with patch("grant_writer.llm.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        def mock_generate_content(model, contents, *args, **kwargs):
            mock_resp = MagicMock()
            mock_resp.function_calls = None

            config = kwargs.get("config")
            is_json_mode = (
                config and hasattr(config, "response_mime_type")
                and config.response_mime_type == "application/json"
            )

            if isinstance(contents, str):
                contents_lower = contents.lower()
            else:
                contents_lower = ""

            if "security compliance judge" in contents_lower:
                # Security judge call
                parts = contents.split("Proposal Draft:\n")
                draft_content = parts[1] if len(parts) > 1 else contents
                has_leak = (
                    "50,000" in draft_content
                    or "123456789" in draft_content
                    or "bank account" in draft_content.lower()
                )
                if has_leak:
                    mock_resp.text = '{"is_safe": false, "confidence": 0.95, "findings": ["Financial data detected"]}'
                else:
                    mock_resp.text = '{"is_safe": true, "confidence": 0.98, "findings": []}'

            elif "compliance auditor" in contents_lower:
                mock_resp.text = "All checks passed.\nCOMPLIANCE STATUS: APPROVED"

            elif is_json_mode:
                # Generic JSON mode — return a plausible response
                if "supervisor orchestrator" in contents_lower:
                    user_msg = ""
                    parts = contents.split('Latest User Message:\n"')
                    if len(parts) > 1:
                        user_msg = parts[1].split('"')[0].lower()

                    import re
                    words = set(re.findall(r"\b\w+\b", user_msg))

                    if {"hello", "hi", "hey", "greetings"}.intersection(words):
                        mock_resp.text = '{"intent": "greet", "reply": "Hello! I am your Eco Grant Writer Assistant. How can I help you today?", "reason": "User greeted the agent."}'
                    elif "capital of" in user_msg or "france" in user_msg or "trivia" in user_msg:
                        mock_resp.text = '{"intent": "general", "reply": "I\'m sorry, I can only help you draft environmental grant proposals.", "reason": "General out-of-scope question."}'
                    elif "options" in user_msg or "match" in user_msg or "search" in user_msg or "find" in user_msg:
                        mock_resp.text = '{"intent": "match", "reply": "", "reason": "User wants to match grants."}'
                    elif "show" in user_msg or "proposal" in user_msg:
                        mock_resp.text = '{"intent": "show", "reply": "", "reason": "User wants to view proposal."}'
                    else:
                        mock_resp.text = '{"intent": "intake", "reply": "", "reason": "Proceeding with notes/interview."}'
                elif "intake" in contents_lower or "extract" in contents_lower:
                    mock_resp.text = (
                        '{"organization_name": "Green Delhi", "project_summary": "River cleanup", '
                        '"location": "Delhi", "budget_amount": 1500000, "currency": "INR", '
                        '"ngo_registration_id": "", "project_duration": "6 months", '
                        '"volunteers_count": 50}'
                    )
                elif "missing" in contents_lower:
                    mock_resp.text = (
                        '{"message": "Great notes! What is your NGO registration ID?", '
                        '"options": ["Skip for now", "DL/2026/12345"], '
                        '"missing_fields": ["ngo_registration_id"]}'
                    )
                elif "follow" in contents_lower:
                    mock_resp.text = (
                        '{"intake_complete": true, "updated_fields": {}, '
                        '"message": "Perfect, moving to grant matching!", "options": ["Find grants"]}'
                    )
                elif "conversational" in contents_lower or "response" in contents_lower:
                    mock_resp.text = (
                        '{"message": "Section drafted! Continue?", '
                        '"options": ["Next section", "Review"]}'
                    )
                else:
                    mock_resp.text = '{"message": "OK", "options": []}'

            else:
                # Default drafting call
                mock_resp.text = (
                    "## Executive Summary\n\n"
                    "This project aims to restore local waterways through "
                    "community engagement and ecological restoration.\n\n"
                    "Estimated tonnes of waste removed: 80\n"
                    "Number of local volunteers engaged: 300\n"
                )

            return mock_resp

        mock_client.models.generate_content.side_effect = mock_generate_content

        # Reset the global client singleton for each test
        import grant_writer.llm as llm_module
        llm_module._gemini_client = mock_client

        yield mock_client_cls
