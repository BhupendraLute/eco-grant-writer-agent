"""Eco Grant Writer Agent — workflow orchestrator.

This module wires together the workflow graph using Google ADK 2.0.
All logic lives in the nodes/ package; this file is purely structural.
"""

from google.adk.workflow import Workflow, START

from grant_writer.models import GrantWriterState
from grant_writer.nodes.router import Router
from grant_writer.nodes.intake import IntakeInterview
from grant_writer.nodes.grant_matcher import GrantMatcher
from grant_writer.nodes.section_drafter import SectionDrafter
from grant_writer.nodes.compliance_auditor import ComplianceAuditor
from grant_writer.nodes.security_guardrail import SecurityGuardrail
from grant_writer.nodes.assembler import FinalAssembler
from grant_writer.nodes.show import ShowProposal
from grant_writer.nodes.respond import RespondDirectly

# ── Workflow Graph ───────────────────────────────────────────────────
#
#   START → Router ─┬─ "intake"  → IntakeInterview → GrantMatcher
#                    ├─ "match"   → GrantMatcher
#                    ├─ "draft"   → SectionDrafter
#                    ├─ "show"    → ShowProposal
#                    └─ "respond" → RespondDirectly
#
#   GrantMatcher → SectionDrafter → ComplianceAuditor
#
#   ComplianceAuditor ─┬─ "passed"     → SecurityGuardrail → FinalAssembler
#                      └─ "violations" → SectionDrafter
#

root_agent = Workflow(
    name="grant_writer_workflow",
    description=(
        "Intelligent guided grant proposal drafting agent. "
        "Walks nonprofits through intake, grant matching, "
        "section-by-section drafting, compliance auditing, "
        "and security review."
    ),
    state_schema=GrantWriterState,
    edges=[
        # Entry point
        (START, Router),

        # Router dispatches by intent
        (Router, {
            "intake": IntakeInterview,
            "match": GrantMatcher,
            "draft": SectionDrafter,
            "show": ShowProposal,
            "respond": RespondDirectly,
        }),

        # Guided flow
        (IntakeInterview, GrantMatcher),
        (GrantMatcher, SectionDrafter),
        (SectionDrafter, ComplianceAuditor),

        # Compliance gate
        (ComplianceAuditor, {
            "passed": SecurityGuardrail,
            "violations": SectionDrafter,
        }),

        # Security gate → final assembly
        (SecurityGuardrail, FinalAssembler),
    ],
)
