from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class OpenRiskItem(BaseModel):
    """
    Structured risk item with direct quote evidence.
    """
    risk_type: Literal[
        "Escalation",
        "Churn Risk",
        "SLA Breach",
        "Competitor Evaluation",
        "Product Blocker",
        "Usage Drop",
        "Customer Frustration"
    ] = Field(..., description="Category of risk")
    severity: Literal["Critical", "High", "Medium", "Low"] = Field(
        ..., description="Severity rating"
    )
    ticket_id: Optional[str] = Field(
        default=None, description="Ticket ID if associated with a support ticket, or null if account-level"
    )
    reason: str = Field(
        ..., description="Defensible explanation of the risk and its impact"
    )
    evidence_quote: str = Field(
        ..., description="Direct verbatim quote or account escalation record justifying the risk"
    )


class TAMBrief(BaseModel):
    """
    Comprehensive 3-Section TAM Account Brief for QBR and Account Reviews.
    """
    account_id: str = Field(..., description="Target Account Identifier")
    company: str = Field(..., description="Company Name")
    tam_assigned: Optional[str] = Field(default=None, description="Assigned TAM Name")
    health_status: str = Field(..., description="Account health status (e.g., At Risk, Healthy)")
    arr_usd: float = Field(..., description="Annual Recurring Revenue in USD")
    seat_utilization_pct: float = Field(..., description="Active seats / Licensed seats percentage")
    total_tickets_last_90d: int = Field(..., description="Total number of support tickets in the last 90 days")

    # Section 1: Executive Summary (3 to 5 sentences)
    executive_summary: str = Field(
        ..., description="Concise 3-5 sentence executive overview of account status, adoption, and posture"
    )

    # Section 2: Open Risks & Flagged Issues (Structured list with evidence quotes)
    open_risks: List[OpenRiskItem] = Field(
        default_factory=list,
        description="Structured list of open risks with severity, ticket ID, and direct evidence quotes"
    )

    # Section 3: Recommended Talking Points for TAM
    talking_points: List[str] = Field(
        ..., description="Actionable, strategic talking points for the TAM's upcoming QBR meeting"
    )


class TAMBriefRequest(BaseModel):
    """
    Request payload model for TAM Brief generation.
    """
    account_id: str = Field(
        ...,
        description="Account ID to look up (e.g., ACC-3336)",
        examples=["ACC-3336", "ACC-8673", "ACC-3033"]
    )
