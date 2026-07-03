"""Security guardrail node — PII detection + LLM-as-a-Judge + HITL gate."""

import json
import logging

from google.adk.workflow import node
from google.adk.agents.context import Context
from google.adk.events.request_input import RequestInput
from google.genai import types

from grant_writer.models import ChatMessage
from grant_writer.security.pii_scrubber import scrub_pii, detect_pii_findings
from grant_writer.security.judge import judge_proposal

logger = logging.getLogger(__name__)


@node(rerun_on_resume=True)
async def SecurityGuardrail(ctx: Context, node_input: str | None = None):
    """Multi-layered security gate for the proposal draft.

    Layers:
    1. PII Scrubber (deterministic) — detects bank accounts, Aadhaar, etc.
    2. LLM-as-a-Judge — structured JSON verdict with confidence score
    3. HITL gate — human review via RequestInput if flagged

    If the draft passes, routes to the final assembler.
    """
    draft = ctx.state.get("drafted_proposal", "")
    chat_history = ctx.state.get("chat_history", [])

    logger.info("SecurityGuardrail: Running security checks on draft (%d chars)", len(draft))

    # --- Layer 1: PII Scrubbing ---
    pii_findings = detect_pii_findings(draft)
    if pii_findings:
        logger.warning(
            "SecurityGuardrail: PII scrubber found %d finding(s): %s",
            len(pii_findings),
            [f["type"] for f in pii_findings],
        )

    # --- Layer 2: LLM-as-a-Judge ---
    budget_amount = ctx.state.get("budget_amount", 0)
    currency_symbol = ctx.state.get("currency_symbol", "₹")
    verdict = judge_proposal(draft, budget_final=budget_amount, currency_symbol=currency_symbol)

    # Combine findings
    all_findings = []
    if pii_findings:
        all_findings.extend([f"PII detected: {f['type']} — '{f['match'][:30]}...'" for f in pii_findings])
    if not verdict.is_safe:
        all_findings.extend(verdict.findings)

    is_safe = len(all_findings) == 0

    if not is_safe:
        logger.warning("SecurityGuardrail: FLAGGED — %d finding(s)", len(all_findings))

        # Check if user already approved (resume from HITL)
        if ctx.resume_inputs:
            user_response = ctx.resume_inputs.get("security_financial_review")
            if user_response:
                val = str(
                    user_response.get("result", "") if isinstance(user_response, dict) else user_response
                ).strip().lower()
                if val in ("a", "approve", "approved", "yes"):
                    logger.info("SecurityGuardrail: User approved despite findings")
                    ctx.state["security_approved"] = True
                    ctx.state["phase"] = "complete"
                    response_data = {
                        "message": "✅ Security review bypassed by user approval. Proposal is finalized!",
                        "options": ["View final proposal", "Export as markdown"],
                    }
                    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
                    ctx.state["chat_history"] = chat_history
                    return types.Content(parts=[types.Part(text=json.dumps(response_data))])
                elif val in ("b", "reject", "abort"):
                    raise ValueError("Draft rejected by user due to security concerns.")

        # Request human review
        findings_text = "\n".join(f"  • {f}" for f in all_findings)
        prompt_msg = (
            f"🛡️ Security Guardrail Triggered\n\n"
            f"The following potential issues were detected:\n{findings_text}\n\n"
            f"Judge confidence: {verdict.confidence:.0%}\n\n"
            "Please review:\n"
            "  A) Approve (bypass safety check and proceed)\n"
            "  B) Reject (abort execution)"
        )
        return RequestInput(message=prompt_msg, interrupt_id="security_financial_review")

    # All clear
    logger.info("SecurityGuardrail: Draft passed all security checks")
    ctx.state["security_approved"] = True
    ctx.state["phase"] = "complete"

    response_data = {
        "message": "🛡️ ✅ Security and compliance checks all passed! Your proposal is ready.",
        "options": ["View final proposal", "Make more changes", "Export as markdown"],
    }
    chat_history.append(ChatMessage(role="assistant", content=response_data["message"]))
    ctx.state["chat_history"] = chat_history

    return types.Content(parts=[types.Part(text=json.dumps(response_data))])
