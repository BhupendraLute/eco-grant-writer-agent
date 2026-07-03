"""Compliance auditor node — dual-layer compliance checking."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.adk.events.request_input import RequestInput
from google.genai import types

from grant_writer.llm import generate_text, LLMResponseError
from grant_writer.models import ChatMessage
from grant_writer.prompts.compliance import COMPLIANCE_AUDIT

logger = logging.getLogger(__name__)


def evaluate_compliance_local(draft: str, guidelines: dict) -> tuple[bool, str, list[str]]:
    """Deterministic compliance check against grant guidelines.

    Checks:
    1. All mandatory sections are present
    2. Budget is within limits
    3. Required metrics are mentioned
    4. No prohibited expenses appear

    Returns:
        Tuple of (is_compliant, audit_report, violations_list).
    """
    reqs = guidelines.get("requirements", {})
    violations = []

    # 1. Check mandatory sections
    mandatory = reqs.get("mandatory_sections", [])
    for section in mandatory:
        if section.lower() not in draft.lower():
            violations.append(f"Missing mandatory section: '{section}'")

    # 2. Check budget limit
    max_budget_inr = reqs.get("max_budget_inr")
    if max_budget_inr:
        import re
        # Try to find the proposed budget in the draft
        budget_match = re.search(r"(?:₹|INR)\s*([\d,]+)", draft)
        if budget_match:
            try:
                proposed = int(budget_match.group(1).replace(",", ""))
                if proposed > max_budget_inr:
                    violations.append(
                        f"Budget ₹{proposed:,} exceeds maximum ₹{max_budget_inr:,}"
                    )
            except ValueError:
                pass

    # 3. Check required metrics are addressed
    for metric in reqs.get("required_metrics", []):
        # Check for key words from the metric
        metric_keywords = [w.lower() for w in metric.split() if len(w) > 3]
        if metric_keywords and not any(kw in draft.lower() for kw in metric_keywords):
            violations.append(f"Required metric not addressed: '{metric}'")

    # 4. Check prohibited expenses
    for expense in reqs.get("prohibited_expenses", []):
        if expense.lower() in draft.lower():
            violations.append(f"Prohibited expense mentioned: '{expense}'")

    if violations:
        report = "Compliance Audit: VIOLATIONS FOUND\n" + "\n".join(f"- {v}" for v in violations)
        return False, report, violations
    else:
        return True, "Compliance Audit: APPROVED (All checks passed)", []


@node(rerun_on_resume=True)
async def ComplianceAuditor(ctx: Context, node_input: str | None = None):
    """Reviews the assembled proposal for compliance with grant guidelines.

    Uses a dual-layer approach:
    1. Deterministic checks (sections, budget, metrics, prohibited items)
    2. LLM-based semantic audit (nuanced issues)

    Routes to:
    - "passed": Compliance passed → security guardrail
    - "violations": Compliance failed → back to drafter for fixes
    """
    draft = ctx.state.get("drafted_proposal", "")
    guidelines_json = ctx.state.get("target_grant_guidelines", "{}")
    chat_history = ctx.state.get("chat_history", [])

    try:
        guidelines = json.loads(guidelines_json)
    except json.JSONDecodeError:
        guidelines = {}

    grant_name = guidelines.get("grant_name", ctx.state.get("target_grant", "Selected Grant"))
    logger.info("ComplianceAuditor: Auditing proposal for '%s'", grant_name)

    # --- Layer 1: Deterministic compliance checks ---
    is_compliant, local_report, violations = evaluate_compliance_local(draft, guidelines)
    logger.info("ComplianceAuditor: Local check: compliant=%s violations=%d", is_compliant, len(violations))

    # --- Layer 2: LLM semantic audit ---
    llm_report = ""
    try:
        audit_prompt = COMPLIANCE_AUDIT.format(
            guidelines_json=json.dumps(guidelines, indent=2),
            proposal_draft=draft[:8000],  # Truncate to avoid token limits
        )
        llm_report = generate_text(audit_prompt, min_response_length=20)

        if "COMPLIANCE STATUS: APPROVED" not in llm_report.upper():
            is_compliant = False
            logger.info("ComplianceAuditor: LLM audit found additional issues")

    except (LLMResponseError, Exception) as exc:
        logger.warning("ComplianceAuditor: LLM audit failed (%s), relying on local checks", exc)

    # Store compliance report (separate key — NOT overwriting guidelines!)
    full_report = local_report
    if llm_report:
        full_report += "\n\n--- LLM Audit ---\n" + llm_report
    ctx.state["compliance_report"] = full_report
    ctx.state["is_compliant"] = is_compliant

    if not is_compliant:
        logger.warning("ComplianceAuditor: VIOLATIONS FOUND")

        # Check if user already force-approved
        if ctx.resume_inputs:
            user_response = ctx.resume_inputs.get("compliance_review_choice")
            if user_response:
                val_raw = str(user_response.get("result", "") if isinstance(user_response, dict) else user_response).strip()
                val = val_raw.lower()
                if val in ("a", "force", "approve", "force approve"):
                    logger.info("ComplianceAuditor: User force-approved despite violations")
                    ctx.state["is_compliant"] = True
                    ctx.route = "passed"
                    return draft
                elif val in ("b", "reject", "abort"):
                    raise ValueError("Draft rejected by user due to compliance violations.")
                else:
                    # User typed natural language response/info!
                    logger.info("ComplianceAuditor: User provided extra details: '%s'", val_raw)
                    
                    # Track user response in chat history so drafting node sees it
                    chat_history.append(ChatMessage(role="user", content=val_raw))
                    ctx.state["chat_history"] = chat_history
                    
                    # Reset section index to the first missing/non-compliant section
                    mandatory = guidelines.get("requirements", {}).get("mandatory_sections", [])
                    reset_idx = 0
                    for idx, section in enumerate(mandatory):
                        if section.lower() not in draft.lower():
                            reset_idx = idx
                            break
                            
                    ctx.state["current_section_index"] = reset_idx
                    ctx.state["is_compliant"] = False
                    ctx.route = "violations"
                    
                    response_data = {
                        "message": f"✍️ Got it! I've added your details to the conversation history. "
                                  f"I will now loop back and rewrite the **{mandatory[reset_idx]}** section.",
                        "options": ["Continue drafting"],
                    }
                    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
                    ctx.state["chat_history"] = chat_history
                    return types.Content(parts=[types.Part(text=json.dumps(response_data))])

        # Request human review
        prompt_msg = (
            f"⚠️ Compliance Audit Flagged Violations:\n\n{local_report}\n\n"
            "Please supply the missing information or details in the chat box below to resolve these issues."
        )
        return RequestInput(message=prompt_msg, interrupt_id="compliance_review_choice")

    # Compliance passed
    logger.info("ComplianceAuditor: All checks passed")
    ctx.route = "passed"

    response_data = {
        "message": "✅ Compliance audit passed! Running security checks now...",
        "options": [],
    }
    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
    ctx.state["chat_history"] = chat_history

    return draft
