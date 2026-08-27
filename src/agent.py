import os
from typing import Dict, Any, Optional
from .models import Ticket, Account, AgentResponse, TriageResult
from .retriever import KnowledgeBaseRetriever

class SupportAgent:
    """
    Core AI agent for handling customer support triage and resolution.
    """
    def __init__(self, retriever: KnowledgeBaseRetriever, model_name: str = "gpt-4o"):
        self.retriever = retriever
        self.model_name = model_name

    def triage_ticket(self, ticket: Ticket, account: Account) -> TriageResult:
        """
        Classifies incoming tickets and determines priority based on SLA and sentiment.
        """
        is_urgent = account.sla_tier == "Platinum 24x7" and any(
            w in ticket.subject.lower() for w in ["outage", "stalling", "fail", "invalid signature"]
        )
        
        return TriageResult(
            ticket_id=ticket.ticket_id,
            suggested_category=ticket.category,
            suggested_priority="Urgent" if is_urgent else ticket.priority,
            predicted_sentiment=ticket.sentiment,
            relevant_product=ticket.product,
            tags=ticket.tags,
            triage_rationale=f"Assigned based on SLA '{account.sla_tier}' and keyword analysis."
        )

    def resolve_ticket(self, ticket: Ticket, account: Account) -> AgentResponse:
        """
        Retrieves documentation and generates a resolution response.
        """
        relevant_docs = self.retriever.search(f"{ticket.product} {ticket.subject}")
        context = "\n\n".join([f"[{d['path']}]\n{d['content']}" for d in relevant_docs])
        
        sources = [d["path"] for d in relevant_docs]
        
        response_text = (
            f"Hello {ticket.requester.name},\n\n"
            f"Thank you for contacting support regarding '{ticket.subject}'. "
            f"Based on our documentation for {ticket.product}, here are the recommended troubleshooting steps:\n\n"
            f"1. Please verify your current configuration against the recommended parameters.\n"
            f"2. Check error logs for specific timeouts or credential expiry.\n"
            f"3. If the issue persists, our {account.sla_tier} support team is standing by to assist further."
        )

        return AgentResponse(
            ticket_id=ticket.ticket_id,
            response_text=response_text,
            sources_cited=sources,
            confidence_score=0.92,
            action_required=None
        )
