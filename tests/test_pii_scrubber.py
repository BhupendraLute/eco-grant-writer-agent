"""Unit tests for the PII scrubber module."""

import pytest

from grant_writer.security.pii_scrubber import scrub_pii, detect_pii_findings


class TestDetectPiiFindings:
    def test_bank_account(self):
        findings = detect_pii_findings("Account number: 123456789012")
        types = [f["type"] for f in findings]
        assert "bank_account" in types

    def test_aadhaar_number(self):
        findings = detect_pii_findings("Aadhaar: 1234 5678 9012")
        types = [f["type"] for f in findings]
        assert "aadhaar" in types

    def test_pan_card(self):
        findings = detect_pii_findings("PAN: ABCDE1234F")
        types = [f["type"] for f in findings]
        assert "pan_card" in types

    def test_email_address(self):
        findings = detect_pii_findings("Contact: admin@nonprofit.org")
        types = [f["type"] for f in findings]
        assert "email" in types

    def test_ifsc_code(self):
        findings = detect_pii_findings("IFSC: SBIN0012345")
        types = [f["type"] for f in findings]
        assert "ifsc_code" in types

    def test_salary_mention(self):
        findings = detect_pii_findings("Director salary is ₹85,000 per month")
        types = [f["type"] for f in findings]
        assert "salary" in types

    def test_clean_text(self):
        findings = detect_pii_findings("Our project aims to clean local rivers.")
        assert len(findings) == 0

    def test_bank_keyword(self):
        findings = detect_pii_findings("Transfer to bank account number 1234567890123")
        types = [f["type"] for f in findings]
        assert any(t in types for t in ["bank_account", "bank_keyword"])


class TestScrubPii:
    def test_scrubs_email(self):
        text = "Contact us at info@greenearth.org for details"
        scrubbed, findings = scrub_pii(text)
        assert "[REDACTED_EMAIL]" in scrubbed
        assert "info@greenearth.org" not in scrubbed
        assert len(findings) > 0

    def test_scrubs_pan(self):
        text = "PAN number is ABCDE1234F"
        scrubbed, findings = scrub_pii(text)
        assert "[REDACTED_PAN]" in scrubbed
        assert "ABCDE1234F" not in scrubbed

    def test_clean_text_unchanged(self):
        text = "A clean proposal about river conservation."
        scrubbed, findings = scrub_pii(text)
        assert scrubbed == text
        assert len(findings) == 0

    def test_multiple_findings(self):
        text = "Email: a@b.com, PAN: ABCDE1234F"
        scrubbed, findings = scrub_pii(text)
        assert len(findings) >= 2
        assert "a@b.com" not in scrubbed
        assert "ABCDE1234F" not in scrubbed
