"""Intake interview node — guided data extraction from messy notes."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

from grant_writer.llm import generate_json, LLMResponseError
from grant_writer.models import ChatMessage
from grant_writer.tools.currency import detect_currency, extract_budget
from grant_writer.prompts.intake import (
    EXTRACT_STRUCTURED_DATA,
    IDENTIFY_MISSING_FIELDS,
    FOLLOWUP_QUESTION,
)

logger = logging.getLogger(__name__)

# Minimum fields needed to proceed to grant matching
_REQUIRED_FIELDS = {"project_summary", "location"}


def _has_minimum_data(state: dict) -> bool:
    """Check if we have enough data to move to grant matching."""
    return all(state.get(field) for field in _REQUIRED_FIELDS)


@node
async def IntakeInterview(ctx: Context, node_input: str | None = None):
    """Guides the user through an intelligent intake interview.

    First message: Extracts structured data from raw notes via LLM,
    then identifies what's missing and asks smart follow-up questions.

    Subsequent messages: Incorporates new information and asks follow-ups
    until sufficient data is gathered for grant matching.
    """
    node_input = node_input or ""
    raw_notes = ctx.state.get("raw_notes", "")
    chat_history = ctx.state.get("chat_history", [])

    # --- First interaction: Extract structured data from initial notes ---
    if not raw_notes:
        ctx.state["raw_notes"] = node_input
        logger.info("Intake: Processing initial notes (%d chars)", len(node_input))

        # Quick currency/budget detection (deterministic)
        currency, symbol = detect_currency(node_input)
        budget = extract_budget(node_input)
        ctx.state["currency"] = currency
        ctx.state["currency_symbol"] = symbol
        if budget:
            ctx.state["budget_amount"] = budget

        # LLM extraction of structured fields
        try:
            prompt = EXTRACT_STRUCTURED_DATA.format(notes=node_input)
            raw_json = generate_json(prompt, min_response_length=2)
            data = json.loads(raw_json)

            # Update state with extracted fields
            for field in [
                "organization_name", "project_summary", "location",
                "ngo_registration_id", "project_duration",
            ]:
                if data.get(field):
                    ctx.state[field] = data[field]

            if data.get("budget_amount") and not budget:
                ctx.state["budget_amount"] = float(data["budget_amount"])
            if data.get("volunteers_count"):
                ctx.state["volunteers_count"] = int(data["volunteers_count"])
            if data.get("currency") and data["currency"] != "INR":
                ctx.state["currency"] = data["currency"]

            logger.info("Intake: Extracted fields: %s", list(data.keys()))

        except (LLMResponseError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Intake: LLM extraction failed (%s), using deterministic parsing", exc)

        # Check if we already have enough data
        if _has_minimum_data(ctx.state):
            # Ask one clarifying question before proceeding
            response_data = _generate_missing_fields_response(ctx.state)
        else:
            response_data = _generate_missing_fields_response(ctx.state)

    # --- Subsequent interactions: Incorporate new data ---
    else:
        logger.info("Intake: Processing follow-up message")
        try:
            history_text = "\n".join(
                f"{m.role}: {m.content}" for m in chat_history[-6:]
            )
            prompt = FOLLOWUP_QUESTION.format(
                chat_history=history_text,
                user_message=node_input,
                organization_name=ctx.state.get("organization_name", ""),
                project_summary=ctx.state.get("project_summary", ""),
                location=ctx.state.get("location", ""),
                budget_amount=ctx.state.get("budget_amount", 0),
                currency=ctx.state.get("currency", "INR"),
                currency_symbol=ctx.state.get("currency_symbol", "₹"),
                ngo_registration_id=ctx.state.get("ngo_registration_id", ""),
                project_duration=ctx.state.get("project_duration", ""),
                volunteers_count=ctx.state.get("volunteers_count", 0),
            )
            raw_json = generate_json(prompt, min_response_length=2)
            data = json.loads(raw_json)

            # Apply updated fields
            for field, value in data.get("updated_fields", {}).items():
                if value and field in ctx.state:
                    ctx.state[field] = value

            # Check if intake is complete
            if data.get("intake_complete") and _has_minimum_data(ctx.state):
                ctx.state["intake_complete"] = True
                ctx.state["phase"] = "matching"
                logger.info("Intake: Complete — moving to grant matching")

            response_data = {
                "message": data.get("message", "Thanks! Let me process that."),
                "options": data.get("options", []),
            }

        except (LLMResponseError, json.JSONDecodeError, Exception) as exc:
            logger.warning("Intake: Follow-up LLM failed (%s)", exc)
            # If we have minimum data, just proceed
            if _has_minimum_data(ctx.state):
                ctx.state["intake_complete"] = True
                ctx.state["phase"] = "matching"
                response_data = {
                    "message": "✅ Great, I have enough information to find matching grants for you!",
                    "options": ["Find matching grants", "Add more details first"],
                }
            else:
                response_data = {
                    "message": "Thanks! Could you tell me more about your project location and what it aims to achieve?",
                    "options": ["River cleanup in Mumbai", "Urban forest in Delhi", "Climate education program"],
                }

    # Add assistant message to chat history
    msg_text = response_data.get("message", "")
    chat_history.append(ChatMessage(role="assistant", content=msg_text))
    ctx.state["chat_history"] = chat_history

    logger.info("Intake: phase=%s intake_complete=%s", ctx.state.get("phase"), ctx.state.get("intake_complete"))
    return types.Content(parts=[types.Part(text=json.dumps(response_data))])


def _generate_missing_fields_response(state: dict) -> dict:
    """Generates a response identifying missing fields using the LLM."""
    try:
        prompt = IDENTIFY_MISSING_FIELDS.format(
            organization_name=state.get("organization_name", "Not provided"),
            project_summary=state.get("project_summary", "Not provided"),
            location=state.get("location", "Not provided"),
            budget_amount=state.get("budget_amount", 0),
            currency=state.get("currency", "INR"),
            currency_symbol=state.get("currency_symbol", "₹"),
            ngo_registration_id=state.get("ngo_registration_id", "Not provided"),
            project_duration=state.get("project_duration", "Not provided"),
            volunteers_count=state.get("volunteers_count", 0),
        )
        raw_json = generate_json(prompt, min_response_length=2)
        data = json.loads(raw_json)

        # If few things are missing, mark intake as potentially complete
        missing = data.get("missing_fields", [])
        if len(missing) <= 1 and _has_minimum_data(state):
            state["intake_complete"] = True
            state["phase"] = "matching"

        return {
            "message": data.get("message", "I've captured your project details!"),
            "options": data.get("options", []),
        }

    except (LLMResponseError, json.JSONDecodeError, Exception):
        # Deterministic fallback
        missing = []
        if not state.get("project_summary"):
            missing.append("project description")
        if not state.get("location"):
            missing.append("location")
        if not state.get("budget_amount"):
            missing.append("budget")

        if missing:
            msg = f"📋 Thanks for the notes! I still need: **{', '.join(missing)}**. Could you share those?"
        else:
            state["intake_complete"] = True
            state["phase"] = "matching"
            msg = "✅ I have all the key details! Let me find the best matching grant for your project."

        return {"message": msg, "options": ["Find matching grants"]}
