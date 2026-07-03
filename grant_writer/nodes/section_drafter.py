"""Section-by-section drafter node with ReAct self-correction loop."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

from grant_writer.config import MAX_REACT_ITERATIONS
from grant_writer.llm import generate, generate_text, generate_json, LLMResponseError
from grant_writer.models import ChatMessage
from grant_writer.tools.budget import calculate_budget_allocation
from grant_writer.tools.ngo_validator import validate_ngo_registration
from grant_writer.prompts.drafter import (
    DRAFT_SECTION,
    REACT_SELF_CORRECT,
    CONVERSATIONAL_RESPONSE,
)

logger = logging.getLogger(__name__)


def _evaluate_section_compliance(section_name: str, content: str, guidelines: dict) -> tuple[bool, list[str]]:
    """Quick deterministic compliance check for a single section.

    Returns (is_compliant, list_of_violations).
    """
    violations = []
    reqs = guidelines.get("requirements", {})

    # Check word count limits
    word_limits = reqs.get("word_count_limits", {})
    if section_name in word_limits:
        max_words = word_limits[section_name]
        actual_words = len(content.split())
        if actual_words > max_words * 1.2:  # Allow 20% tolerance
            violations.append(
                f"Section '{section_name}' exceeds word limit: {actual_words} words "
                f"(max: {max_words})"
            )

    # Check prohibited expenses (for budget sections)
    if "budget" in section_name.lower():
        for expense in reqs.get("prohibited_expenses", []):
            if expense.lower() in content.lower():
                violations.append(f"Prohibited expense mentioned: '{expense}'")

    return len(violations) == 0, violations


@node(rerun_on_resume=True)
async def SectionDrafter(ctx: Context, node_input: str | None = None):
    """Drafts proposal sections one at a time with ReAct self-correction.

    Flow:
    1. Identifies the next section to draft from mandatory_sections
    2. Generates section content using focused LLM prompts with tool support
    3. Runs a mini compliance check per section
    4. Self-corrects up to MAX_REACT_ITERATIONS times
    5. Stores section in state and presents to user
    """
    chat_history = ctx.state.get("chat_history", [])
    sections_drafted = ctx.state.get("sections_drafted", {})
    mandatory_sections = ctx.state.get("mandatory_sections", [])

    # Parse guidelines
    guidelines_json = ctx.state.get("target_grant_guidelines", "{}")
    try:
        guidelines = json.loads(guidelines_json)
    except json.JSONDecodeError:
        guidelines = {}

    grant_name = ctx.state.get("target_grant", guidelines.get("grant_name", "Selected Grant"))
    agency = guidelines.get("issuing_agency", "Funding Agency")
    reqs = guidelines.get("requirements", {})

    # Determine which section to draft
    current_idx = ctx.state.get("current_section_index", 0)
    if current_idx >= len(mandatory_sections):
        # All sections drafted — assemble and move to compliance
        ctx.state["phase"] = "review"
        logger.info("SectionDrafter: All %d sections drafted, moving to review", len(mandatory_sections))
        return _assemble_and_respond(ctx, chat_history, mandatory_sections, sections_drafted)

    section_name = mandatory_sections[current_idx]
    ctx.state["current_section"] = section_name
    logger.info("SectionDrafter: Drafting section %d/%d: '%s'", current_idx + 1, len(mandatory_sections), section_name)

    # Build context from previously drafted sections
    prev_context = ""
    if sections_drafted:
        prev_context = "Previously drafted sections:\n" + "\n".join(
            f"## {name}\n{content[:300]}..." for name, content in sections_drafted.items()
        )

    # Build guidelines summary
    guidelines_summary = (
        f"Max Budget: {reqs.get('max_budget_inr', 'N/A')}\n"
        f"Required Metrics: {', '.join(reqs.get('required_metrics', []))}\n"
        f"Prohibited Expenses: {', '.join(reqs.get('prohibited_expenses', []))}\n"
        f"Word Count Limits: {json.dumps(reqs.get('word_count_limits', {}))}"
    )

    # Format chat history for context
    chat_history_str = "\n".join(f"{m.role}: {m.content}" for m in chat_history)

    # Build the section drafting prompt
    prompt = DRAFT_SECTION.format(
        section_name=section_name,
        grant_name=grant_name,
        agency=agency,
        currency_symbol=ctx.state.get("currency_symbol", "₹"),
        budget_amount=ctx.state.get("budget_amount", 0),
        currency=ctx.state.get("currency", "INR"),
        guidelines_summary=guidelines_summary,
        organization_name=ctx.state.get("organization_name", ""),
        project_summary=ctx.state.get("project_summary", ""),
        location=ctx.state.get("location", ""),
        project_duration=ctx.state.get("project_duration", ""),
        volunteers_count=ctx.state.get("volunteers_count", 0),
        raw_notes=ctx.state.get("raw_notes", "")[:2000],
        chat_history=chat_history_str,
        previous_sections_context=prev_context,
    )

    # --- ReAct Self-Correction Loop ---
    section_content = ""
    is_compliant = False

    for iteration in range(1, MAX_REACT_ITERATIONS + 1):
        logger.info("SectionDrafter: ReAct iteration %d for '%s'", iteration, section_name)

        try:
            # Generate with tool support
            response = generate(
                prompt,
                tools=[calculate_budget_allocation, validate_ngo_registration],
                min_response_length=20,
            )

            # Handle tool execution
            if response.function_calls:
                logger.info("SectionDrafter: Executing %d tool call(s)", len(response.function_calls))
                tool_output = ""
                for fc in response.function_calls:
                    if fc.name == "calculate_budget_allocation":
                        args = fc.args
                        tool_output += "\n\nBudget Allocation:\n" + calculate_budget_allocation(
                            total_budget=args.get("total_budget", ctx.state.get("budget_amount", 0)),
                            categories=args.get("categories"),
                        )
                    elif fc.name == "validate_ngo_registration":
                        args = fc.args
                        tool_output += "\n\nNGO Verification:\n" + validate_ngo_registration(
                            darpan_id=args.get("darpan_id", ""),
                        )
                # Re-generate with tool output
                section_content = generate_text(
                    prompt + tool_output,
                    min_response_length=20,
                )
            else:
                section_content = response.text.strip()

            # Check compliance
            is_compliant, violations = _evaluate_section_compliance(
                section_name, section_content, guidelines
            )
            if is_compliant:
                logger.info("SectionDrafter: Section '%s' passed compliance on iteration %d", section_name, iteration)
                break
            else:
                logger.info("SectionDrafter: Violations in '%s': %s", section_name, violations)
                # Self-correct
                prompt = REACT_SELF_CORRECT.format(
                    section_name=section_name,
                    violations="\n".join(f"- {v}" for v in violations),
                    previous_draft=section_content,
                    guidelines_summary=guidelines_summary,
                )

        except (LLMResponseError, Exception) as exc:
            logger.error("SectionDrafter: LLM failed on iteration %d: %s", iteration, exc)
            # Generate a structural fallback
            section_content = (
                f"## {section_name}\n\n"
                f"[Draft content for {section_name} based on: {ctx.state.get('project_summary', '')}]\n\n"
                f"Location: {ctx.state.get('location', 'N/A')}\n"
                f"Budget: {ctx.state.get('currency_symbol', '₹')}{ctx.state.get('budget_amount', 0):,.0f}\n"
            )
            is_compliant = True
            break

    # Store the drafted section
    sections_drafted[section_name] = section_content
    ctx.state["sections_drafted"] = sections_drafted
    ctx.state["current_section_index"] = current_idx + 1

    # Generate conversational response
    completed = list(sections_drafted.keys())
    remaining = [s for s in mandatory_sections if s not in sections_drafted]

    try:
        resp_prompt = CONVERSATIONAL_RESPONSE.format(
            section_name=section_name,
            completed_sections=", ".join(completed),
            remaining_sections=", ".join(remaining) if remaining else "None — all done!",
        )
        raw_json = generate_json(resp_prompt, min_response_length=2)
        response_data = json.loads(raw_json)
    except (LLMResponseError, json.JSONDecodeError, Exception):
        if remaining:
            response_data = {
                "message": f"✍️ Drafted **{section_name}**! {len(remaining)} section(s) remaining.",
                "options": ["Continue to next section", "Review this section", "Show full draft so far"],
            }
        else:
            response_data = {
                "message": f"🎉 All sections drafted! Let me run compliance checks.",
                "options": ["Run compliance check", "Review full proposal"],
            }

    chat_history.append(ChatMessage(role="assistant", content=response_data.get("message", "")))
    ctx.state["chat_history"] = chat_history

    return types.Content(parts=[types.Part(text=json.dumps(response_data))])


def _assemble_and_respond(ctx, chat_history, mandatory_sections, sections_drafted):
    """Assembles all sections into the full proposal."""
    grant_name = ctx.state.get("target_grant", "Grant Proposal")
    agency = ctx.state.get("_agency", "")
    currency_symbol = ctx.state.get("currency_symbol", "₹")
    budget = ctx.state.get("budget_amount", 0)
    currency = ctx.state.get("currency", "INR")

    # Build full proposal
    parts = [
        f"# GRANT PROPOSAL: {grant_name}\n",
        f"**Organization:** {ctx.state.get('organization_name', 'N/A')}",
        f"**Proposed Budget:** {currency_symbol}{budget:,.0f} {currency}",
        f"**Location:** {ctx.state.get('location', 'N/A')}",
        f"**Duration:** {ctx.state.get('project_duration', 'N/A')}\n",
        "---\n",
    ]

    for section_name in mandatory_sections:
        content = sections_drafted.get(section_name, f"[Section not yet drafted: {section_name}]")
        parts.append(f"## {section_name}\n\n{content}\n")

    full_proposal = "\n".join(parts)
    ctx.state["drafted_proposal"] = full_proposal

    response_data = {
        "message": "🎉 All sections are drafted! Running compliance and security checks now.",
        "options": ["Run checks", "Review full proposal first"],
    }
    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
    ctx.state["chat_history"] = chat_history

    return types.Content(parts=[types.Part(text=json.dumps(response_data))])
