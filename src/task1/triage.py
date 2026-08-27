import json
import re
from typing import Union, Dict, Any, Optional

from src.rag.retrieve import (
    load_vectorstore,
    load_model,
    retrieve
)
from src.task1.llm import LLMClient
from src.task1.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.task1.schemas import TriageResult, TicketInput


class TicketTriage:
    """
    Intelligent Ticket Triage Agent (Task 1).
    Ingests raw incoming tickets (free-text or JSON), performs RAG retrieval against
    the knowledge base, and outputs structured classification, urgency (P1-P4),
    reasoning, KB doc citation, recommended team, and professional draft response.
    """

    def __init__(self):
        print("Initializing Ticket Triage Agent...")
        try:
            self.index, self.metadata = load_vectorstore()
            self.model = load_model()
            self.rag_enabled = True
        except Exception as e:
            print(f"Warning: RAG vectorstore not available ({e}). Running without RAG context.")
            self.index, self.metadata, self.model = None, None, None
            self.rag_enabled = False

        self.llm = LLMClient()
        print("Ticket Triage Agent ready.")

    def normalize_ticket(self, ticket: Union[str, Dict[str, Any], TicketInput]) -> Dict[str, Any]:
        """
        Normalizes input ticket from free-text string, dictionary, or TicketInput object into
        a standard internal dictionary format containing 'subject' and 'body'.
        """
        if isinstance(ticket, TicketInput):
            data = ticket.model_dump(exclude_none=True)
            if "raw_text" in data and not data.get("body"):
                data["body"] = data.pop("raw_text")
            if "body" in data and not data.get("subject"):
                data["subject"] = data["body"].split("\n", 1)[0][:100]
            return data

        if isinstance(ticket, str):
            text = ticket.strip()
            lines = text.split("\n", 1)
            subject = lines[0].strip()[:100]
            body = text
            return {
                "subject": subject,
                "body": body,
                "product": None,
                "product_area": None,
                "company": None,
                "plan_tier": None
            }

        if isinstance(ticket, dict):
            normalized = ticket.copy()

            # Handle free-text field keys ("ticket_text" or "raw_text")
            if "ticket_text" in normalized and not normalized.get("body"):
                normalized["body"] = normalized.pop("ticket_text")
            elif "raw_text" in normalized and not normalized.get("body"):
                normalized["body"] = normalized.pop("raw_text")

            # Handle description vs body
            if "description" in normalized and "body" not in normalized:
                normalized["body"] = normalized["description"]

            # Ensure both subject and body exist
            if "body" in normalized and "subject" not in normalized:
                normalized["subject"] = normalized["body"].split("\n", 1)[0][:100]
            elif "subject" in normalized and "body" not in normalized:
                normalized["body"] = normalized["subject"]

            # Remove ground-truth category or urgency if accidentally passed in input
            normalized.pop("category", None)
            normalized.pop("urgency", None)

            return normalized

        raise ValueError(f"Unsupported ticket input type: {type(ticket)}")

    def _build_rag_context(self, ticket_data: Dict[str, Any], top_k: int = 3) -> tuple[str, list]:
        """
        Retrieves top relevant documentation chunks from the vector store.
        """
        if not self.rag_enabled:
            return "Knowledge base unavailable.", []

        subject = ticket_data.get("subject", "")
        body = ticket_data.get("body", "")
        product = ticket_data.get("product") or ""
        product_area = ticket_data.get("product_area") or ""

        query = f"{product} {product_area} {subject} {body[:300]}".strip()

        kb_results = retrieve(
            query=query,
            model=self.model,
            index=self.index,
            metadata=self.metadata,
            top_k=top_k
        )

        if not kb_results:
            return "No matching knowledge base documents found.", []

        kb_context_parts = []
        for res in kb_results:
            kb_context_parts.append(
                f"Source: {res['source']}\n"
                f"Similarity Score: {res.get('score', 0.0):.4f}\n"
                f"Content:\n{res['text']}\n"
            )

        return "\n---\n".join(kb_context_parts), kb_results

    def triage(self, ticket: Union[str, Dict[str, Any], TicketInput]) -> TriageResult:
        """
        Triages an incoming support ticket and returns a validated TriageResult.
        """
        # 1. Normalize input into standard subject + body
        ticket_data = self.normalize_ticket(ticket)

        # 2. Retrieve relevant KB context
        kb_context, _ = self._build_rag_context(ticket_data, top_k=3)

        # 3. Format Ticket Details for Prompt
        details_lines = []
        if ticket_data.get("ticket_id"):
            details_lines.append(f"Ticket ID: {ticket_data['ticket_id']}")
        if ticket_data.get("company"):
            details_lines.append(f"Company: {ticket_data['company']}")
        if ticket_data.get("product"):
            details_lines.append(f"Product: {ticket_data['product']}")
        if ticket_data.get("product_area"):
            details_lines.append(f"Product Area: {ticket_data['product_area']}")
        if ticket_data.get("plan_tier"):
            details_lines.append(f"Plan Tier: {ticket_data['plan_tier']}")

        details_lines.append(f"Subject: {ticket_data.get('subject', '')}")
        details_lines.append(f"Body:\n{ticket_data.get('body', '')}")

        ticket_details = "\n".join(details_lines)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            ticket_details=ticket_details,
            kb_context=kb_context
        )

        # 4. Generate structured response with LLM
        raw_response = self.llm.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        # 5. Clean and parse JSON
        cleaned = raw_response.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
            else:
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            result_dict = json.loads(cleaned)
        except json.JSONDecodeError as e:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                result_dict = json.loads(match.group(0))
            else:
                raise ValueError(f"Failed to parse LLM response into JSON: {raw_response}") from e

        # If product was explicitly passed in ticket, ensure it matches or populates
        if ticket_data.get("product") and not result_dict.get("product"):
            result_dict["product"] = ticket_data["product"]

        # Strict RAG safety check: if known_issue is False, ensure knowledge_base_source is null
        if not result_dict.get("known_issue"):
            result_dict["known_issue"] = False
            result_dict["knowledge_base_source"] = None

        # 6. Validate with Pydantic
        return TriageResult.model_validate(result_dict)


# Singleton instance for callable function
_triage_instance: Optional[TicketTriage] = None


def triage_ticket(ticket: Union[str, Dict[str, Any], TicketInput]) -> TriageResult:
    """
    Exposed callable Python function for ticket triage.
    Accepts raw text string, dictionary, or TicketInput and returns structured TriageResult.
    """
    global _triage_instance
    if _triage_instance is None:
        _triage_instance = TicketTriage()
    return _triage_instance.triage(ticket)