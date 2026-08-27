from typing import Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field


Category = Literal[
    "Data Loss",
    "Feature Request",
    "Performance",
    "How-To",
    "Onboarding",
    "Bug",
    "Billing",
    "Integration",
]

UrgencyTier = Literal["P1", "P2", "P3", "P4"]


class TicketInput(BaseModel):
    """
    Structured input representation for a support ticket.
    Accepts raw text or structured attributes.
    """
    subject: Optional[str] = None
    body: Optional[str] = None
    raw_text: Optional[str] = None
    ticket_id: Optional[str] = None
    company: Optional[str] = None
    product: Optional[str] = None
    product_area: Optional[str] = None
    plan_tier: Optional[str] = None


class TriageResult(BaseModel):
    """
    Structured triage output produced by the Intelligent Ticket Triage Agent.
    """
    product: Optional[str] = Field(
        default=None,
        description="Identified product name (e.g. SecureVault, WorkflowEngine, AnalyticsHub, DataBridge Pro, CloudSync)"
    )
    product_area: str = Field(
        ...,
        description="Specific module or feature area within the product"
    )
    category: Category = Field(
        ...,
        description="Classified issue category"
    )
    urgency: UrgencyTier = Field(
        ...,
        pattern=r"^P[1-4]$",
        description="Urgency tier from P1 (critical/outage) to P4 (low/informational)"
    )
    reasoning: str = Field(
        ...,
        description="Explanation for the assigned category, urgency tier, and routing"
    )
    known_issue: bool = Field(
        ...,
        description="Whether the ticket matches a known issue pattern in the Knowledge Base"
    )
    knowledge_base_source: Optional[str] = Field(
        default=None,
        description="Exact file path / document identifier of the matching KB doc if known_issue is true"
    )
    recommended_team: str = Field(
        ...,
        description="Recommended internal responder team to handle the ticket"
    )
    draft_response: str = Field(
        ...,
        description="Professional first-response draft for the support agent to send to the customer"
    )