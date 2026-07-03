"""LLM-as-a-Judge for security guardrail evaluation.

Uses structured JSON output for reliable parsing, with a deterministic
regex-based fallback when the LLM is unavailable.
"""

import re
import json
import logging

from pydantic import BaseModel, Field

from grant_writer.llm import generate_json, LLMResponseError

logger = logging.getLogger(__name__)


class JudgeVerdict(BaseModel):
    """Structured verdict from the security judge."""

    is_safe: bool = Field(..., description="True if the draft is safe to publish")
    confidence: float = Field(
        default=1.0,
        description="Confidence score from 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
    findings: list[str] = Field(
        default_factory=list,
        description="List of specific security findings, if any",
    )


def prepare_judge_draft(
    draft: str,
    budget_final: float | None = None,
    currency_symbol: str = "₹",
) -> str:
    """Redacts authorized budget figures from the draft before judging.

    Prevents false-positive triggers from the authorized budget amounts
    that are expected to be in the proposal metadata header.

    Args:
        draft: The full proposal draft text.
        budget_final: The authorized budget amount to redact.
        currency_symbol: The currency symbol used in the proposal.

    Returns:
        The draft with authorized budget sections redacted.
    """
    clean_draft = draft

    # 1. Redact the entire itemized budget table / section
    clean_draft = re.sub(
        r"##\s*(?:Itemized\s+)?Budget(?:[^\n]*)\n(?:.*?(?=\n##|$))",
        "## Budget\n[REDACTED_AUTHORIZED_BUDGET_SECTION]\n",
        clean_draft,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # 2. Redact budget metadata lines
    clean_draft = re.sub(
        r"(?:\*\*|###?|#)?\s*(?:Proposed\s+Budget|Total\s+Budget|Proposed\s+Grant\s+Amount|Requested\s+Amount)"
        r"\s*:\s*[^\n]+",
        "Proposed Budget: [REDACTED_AUTHORIZED_BUDGET_METADATA]",
        clean_draft,
        flags=re.IGNORECASE,
    )

    return clean_draft


def _judge_local_fallback(draft: str) -> JudgeVerdict:
    """Deterministic regex-based security check as fallback when LLM is unavailable.

    Args:
        draft: The (redacted) draft text to check.

    Returns:
        A JudgeVerdict based on regex pattern matching.
    """
    findings = []

    # Check for currency amounts in the body
    currency_matches = re.findall(
        r"(?:[\$₹€£¥元]|rs\.?)\s*([\d,]+)",
        draft,
        re.IGNORECASE,
    )
    if currency_matches:
        findings.append(
            f"Found {len(currency_matches)} monetary amount(s) in the draft body"
        )

    # Check for bank account patterns
    if re.search(r"bank\s+account|\b\d{9,18}\b", draft, re.IGNORECASE):
        findings.append("Potential bank account number or bank reference detected")

    is_safe = len(findings) == 0
    return JudgeVerdict(is_safe=is_safe, confidence=0.8, findings=findings)


def judge_proposal(draft: str, budget_final: float | None = None, currency_symbol: str = "₹") -> JudgeVerdict:
    """Evaluates a proposal draft for security/privacy violations.

    Uses a two-layer approach:
    1. LLM-as-a-Judge with structured JSON output (primary)
    2. Deterministic regex scanning (fallback)

    Args:
        draft: The full proposal draft text.
        budget_final: The authorized budget amount (redacted before judging).
        currency_symbol: The currency symbol used in the proposal.

    Returns:
        A JudgeVerdict with safety determination and findings.
    """
    # Prepare redacted draft
    judge_draft = prepare_judge_draft(draft, budget_final, currency_symbol)

    # Attempt LLM-as-a-Judge with structured output
    judge_prompt = (
        "You are a security compliance judge reviewing a grant proposal.\n"
        "Analyze the following draft for security/privacy violations.\n\n"
        "Check for:\n"
        "1. Specific monetary/currency amounts (e.g., '$10,000', '₹50,000') in the body text "
        "(NOT in the standard metadata header which has been redacted).\n"
        "2. Bank account numbers or financial routing codes.\n"
        "3. Personal identification numbers (Aadhaar, PAN, SSN).\n"
        "4. Individual salary or compensation details.\n\n"
        "Return a JSON object with exactly these keys:\n"
        '  "is_safe": boolean (true if no violations found),\n'
        '  "confidence": float between 0.0 and 1.0,\n'
        '  "findings": list of strings describing each violation found (empty if safe).\n\n'
        f"Proposal Draft:\n{judge_draft}"
    )

    try:
        raw_json = generate_json(judge_prompt, min_response_length=2)
        data = json.loads(raw_json)
        verdict = JudgeVerdict(**data)
        logger.info("LLM judge verdict: is_safe=%s confidence=%.2f", verdict.is_safe, verdict.confidence)
        return verdict

    except (LLMResponseError, json.JSONDecodeError, Exception) as exc:
        logger.warning("LLM-as-a-Judge failed (%s), using local fallback", exc)
        return _judge_local_fallback(judge_draft)
