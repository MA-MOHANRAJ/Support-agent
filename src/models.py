from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PrimaryContact(BaseModel):
    name: str
    email: str
    role: str
    phone: Optional[str] = None

class Account(BaseModel):
    account_id: str
    company_name: str
    tier: str
    industry: str
    arr_usd: float
    mrr_usd: float
    active_users: int
    licensed_seats: int
    products_enabled: List[str]
    account_health_score: int
    sla_tier: str
    csm_assigned: str
    primary_contact: PrimaryContact
    billing_cycle: str
    status: str
    created_at: str
    contract_renewal_date: str

class Requester(BaseModel):
    name: str
    email: str
    role: str

class Ticket(BaseModel):
    ticket_id: str
    account_id: str
    product: str
    category: str
    priority: str
    status: str
    sentiment: str
    subject: str
    description: str
    requester: Requester
    assigned_agent: Optional[str] = "Unassigned"
    tags: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    resolution_time_hours: Optional[float] = None
    satisfaction_score: Optional[int] = None
    resolution_summary: Optional[str] = None

class TriageResult(BaseModel):
    ticket_id: str
    suggested_category: str
    suggested_priority: str
    predicted_sentiment: str
    relevant_product: str
    tags: List[str]
    triage_rationale: str

class AgentResponse(BaseModel):
    ticket_id: str
    response_text: str
    sources_cited: List[str] = Field(default_factory=list)
    confidence_score: float = 1.0
    action_required: Optional[str] = None
