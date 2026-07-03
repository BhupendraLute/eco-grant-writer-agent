"""Unit tests for the compliance auditor logic."""

import pytest

from grant_writer.nodes.compliance_auditor import evaluate_compliance_local


SAMPLE_GUIDELINES = {
    "grant_name": "Test Grant",
    "requirements": {
        "max_budget_inr": 2000000,
        "mandatory_sections": [
            "Executive Summary",
            "Ecological Impact Assessment",
            "Community Mobilization Plan",
            "Itemized Budget",
        ],
        "required_metrics": [
            "Estimated tonnes of waste removed",
            "Number of local volunteers engaged",
        ],
        "prohibited_expenses": [
            "Full-time staff salaries",
            "Office rent",
        ],
    },
}


class TestEvaluateComplianceLocal:
    def test_fully_compliant_draft(self):
        draft = (
            "## Executive Summary\nGreat project.\n"
            "## Ecological Impact Assessment\nEnvironmental benefits.\n"
            "## Community Mobilization Plan\nVolunteer engagement.\n"
            "## Itemized Budget\n₹1,500,000 total.\n"
            "Estimated tonnes of waste removed: 80\n"
            "Number of local volunteers engaged: 300\n"
        )
        is_compliant, report, violations = evaluate_compliance_local(draft, SAMPLE_GUIDELINES)
        assert is_compliant
        assert len(violations) == 0
        assert "APPROVED" in report

    def test_missing_section(self):
        draft = (
            "## Executive Summary\nGreat project.\n"
            "## Ecological Impact Assessment\nEnvironmental benefits.\n"
            # Missing: Community Mobilization Plan and Itemized Budget
        )
        is_compliant, report, violations = evaluate_compliance_local(draft, SAMPLE_GUIDELINES)
        assert not is_compliant
        assert any("Community Mobilization Plan" in v for v in violations)

    def test_prohibited_expense_detected(self):
        draft = (
            "## Executive Summary\nProject overview.\n"
            "## Ecological Impact Assessment\nImpact details.\n"
            "## Community Mobilization Plan\nVolunteer plan.\n"
            "## Itemized Budget\n₹1,500,000\n"
            "Includes Full-time staff salaries for the team.\n"
            "Estimated tonnes of waste removed: 50\n"
            "Number of local volunteers engaged: 200\n"
        )
        is_compliant, report, violations = evaluate_compliance_local(draft, SAMPLE_GUIDELINES)
        assert not is_compliant
        assert any("prohibited" in v.lower() for v in violations)

    def test_empty_guidelines(self):
        draft = "Some proposal text."
        is_compliant, report, violations = evaluate_compliance_local(draft, {})
        assert is_compliant
        assert len(violations) == 0

    def test_budget_over_limit(self):
        draft = (
            "## Executive Summary\nProject.\n"
            "## Ecological Impact Assessment\nImpact.\n"
            "## Community Mobilization Plan\nPlan.\n"
            "## Itemized Budget\nProposed Budget: ₹3,000,000\n"
            "Estimated tonnes of waste removed: 50\n"
            "Number of local volunteers engaged: 100\n"
        )
        is_compliant, report, violations = evaluate_compliance_local(draft, SAMPLE_GUIDELINES)
        assert not is_compliant
        assert any("exceeds" in v.lower() for v in violations)
