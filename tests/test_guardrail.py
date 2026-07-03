"""Guardrail-specific tests — verifies that the security judge and PII scrubber work correctly."""

import pytest

from grant_writer.security.judge import judge_proposal, prepare_judge_draft, JudgeVerdict


class TestPrepareJudgeDraft:
    def test_redacts_budget_section(self):
        draft = (
            "## Executive Summary\nGreat project.\n"
            "## Itemized Budget\n| Item | Cost |\n| Tools | ₹50,000 |\n"
            "## Next Section\nMore content."
        )
        result = prepare_judge_draft(draft)
        assert "REDACTED_AUTHORIZED_BUDGET_SECTION" in result
        assert "50,000" not in result

    def test_redacts_proposed_budget_metadata(self):
        draft = "**Proposed Budget:** ₹15,00,000 INR\nContent here."
        result = prepare_judge_draft(draft)
        assert "REDACTED_AUTHORIZED_BUDGET_METADATA" in result
        assert "15,00,000" not in result

    def test_leaves_non_budget_content(self):
        draft = "## Executive Summary\nThis is about cleaning rivers.\n## Impact\nBig impact."
        result = prepare_judge_draft(draft)
        assert "cleaning rivers" in result
        assert "Big impact" in result


class TestJudgeVerdict:
    def test_safe_verdict(self):
        verdict = JudgeVerdict(is_safe=True, confidence=0.95, findings=[])
        assert verdict.is_safe
        assert verdict.confidence == 0.95
        assert len(verdict.findings) == 0

    def test_unsafe_verdict(self):
        verdict = JudgeVerdict(
            is_safe=False,
            confidence=0.88,
            findings=["Bank account detected", "PII leak"]
        )
        assert not verdict.is_safe
        assert len(verdict.findings) == 2
