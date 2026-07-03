"""PII and financial data detection and scrubbing.

Implements the PII/Financial Scrubbing Pipeline called for in SECURITY.md
to prevent accidental leakage of sensitive nonprofit data into public proposals.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detection Patterns
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Bank account numbers (9-18 digit sequences)
    ("bank_account", re.compile(r"\b\d{9,18}\b")),
    # Aadhaar numbers (12 digits, optionally space-separated)
    ("aadhaar", re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")),
    # PAN card numbers (Indian tax ID: ABCDE1234F)
    ("pan_card", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")),
    # Email addresses
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # Phone numbers (10+ digits, optionally with country code)
    ("phone", re.compile(r"(?:\+\d{1,3}[\s-]?)?\b\d{10,13}\b")),
    # IFSC codes (Indian bank branch codes)
    ("ifsc_code", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    # Individual salary mentions
    ("salary", re.compile(
        r"(?:salary|salaries|pay|compensation|wage|wages|stipend)"
        r"\s*(?:of|is|:)?\s*(?:₹|\$|€|£|rs\.?)\s*[\d,]+",
        re.IGNORECASE,
    )),
    # "Bank account" keyword near numbers
    ("bank_keyword", re.compile(
        r"bank\s+account\s*(?:number|no|#|:)?\s*[\d\s-]+",
        re.IGNORECASE,
    )),
]

# Redaction map: finding_type → replacement text
_REDACTION_MAP: dict[str, str] = {
    "bank_account": "[REDACTED_ACCOUNT]",
    "aadhaar": "[REDACTED_AADHAAR]",
    "pan_card": "[REDACTED_PAN]",
    "email": "[REDACTED_EMAIL]",
    "phone": "[REDACTED_PHONE]",
    "ifsc_code": "[REDACTED_IFSC]",
    "salary": "[REDACTED_SALARY_INFO]",
    "bank_keyword": "[REDACTED_BANK_INFO]",
}


def detect_pii_findings(text: str) -> list[dict[str, str]]:
    """Scans text for PII and financial data patterns.

    Args:
        text: The text to scan.

    Returns:
        List of findings, each a dict with keys: 'type', 'match', 'position'.
    """
    findings: list[dict[str, str]] = []
    for pii_type, pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "type": pii_type,
                "match": match.group(),
                "position": f"{match.start()}-{match.end()}",
            })
    return findings


def scrub_pii(text: str) -> tuple[str, list[dict[str, str]]]:
    """Detects and redacts PII/financial data from text.

    Args:
        text: The input text to scrub.

    Returns:
        Tuple of (scrubbed_text, list_of_findings).
        Each finding is a dict with 'type', 'match', 'position'.
    """
    findings = detect_pii_findings(text)

    if not findings:
        return text, []

    scrubbed = text
    # Process longer matches first to avoid offset issues
    sorted_findings = sorted(findings, key=lambda f: len(f["match"]), reverse=True)
    for finding in sorted_findings:
        replacement = _REDACTION_MAP.get(finding["type"], "[REDACTED]")
        scrubbed = scrubbed.replace(finding["match"], replacement)

    logger.warning(
        "PII scrubber found %d finding(s): %s",
        len(findings),
        ", ".join(f["type"] for f in findings),
    )

    return scrubbed, findings
