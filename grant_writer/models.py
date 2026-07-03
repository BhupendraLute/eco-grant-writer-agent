"""Pydantic models for the Eco Grant Writer agent state and messages."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class GrantWriterState(BaseModel):
    """Complete workflow state for the grant writer agent.

    Tracks the agent through five phases:
        intake → matching → drafting → review → complete
    """

    # ── Phase Tracking ──────────────────────────────────────────────
    phase: str = Field(
        default="intake",
        description="Current workflow phase: intake | matching | drafting | review | complete",
    )

    # ── Intake Data ─────────────────────────────────────────────────
    raw_notes: str = Field(default="", description="Original messy notes from the user")
    organization_name: str = Field(default="", description="Nonprofit organization name")
    project_summary: str = Field(default="", description="Brief summary of the proposed project")
    location: str = Field(default="", description="Project location (city/region)")
    budget_amount: float = Field(default=0.0, description="Proposed budget amount")
    currency: str = Field(default="INR", description="Currency code (e.g. INR, USD, EUR)")
    currency_symbol: str = Field(default="₹", description="Currency symbol")
    ngo_registration_id: str = Field(default="", description="NGO Darpan or equivalent registration ID")
    project_duration: str = Field(default="", description="Expected project duration")
    volunteers_count: int = Field(default=0, description="Number of existing/expected volunteers")
    intake_complete: bool = Field(default=False, description="Whether intake interview is finished")

    # ── Grant Matching ──────────────────────────────────────────────
    target_grant: str = Field(default="", description="Selected grant program name")
    target_grant_id: str = Field(default="", description="Selected grant program ID")
    target_grant_guidelines: str = Field(default="", description="JSON string of full grant guidelines")
    grant_confirmed: bool = Field(default=False, description="Whether user confirmed the grant selection")
    ranked_grants: list[str] = Field(default_factory=list, description="Top ranked grant choices presented to user")

    # ── Section-by-Section Drafting ─────────────────────────────────
    mandatory_sections: list[str] = Field(default_factory=list, description="List of required sections from guidelines")
    sections_drafted: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of section_name → drafted content",
    )
    current_section: str = Field(default="", description="Name of the section currently being drafted")
    current_section_index: int = Field(default=0, description="Index of the section currently being drafted")
    drafted_proposal: str = Field(default="", description="Fully assembled proposal text")

    # ── Compliance & Security ───────────────────────────────────────
    compliance_report: str = Field(default="", description="Last compliance audit report")
    is_compliant: bool = Field(default=False, description="Whether the draft passed compliance")
    security_approved: bool = Field(default=False, description="Whether the draft passed security guardrail")

    # ── Conversation ────────────────────────────────────────────────
    chat_history: list[ChatMessage] = Field(default_factory=list, description="Full conversation history")
    respond_reply: str = Field(default="", description="Direct response reply text from orchestrator")
