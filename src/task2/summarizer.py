import json
import re
import hashlib
from typing import Optional, Dict, Any, List

from src.task1.llm import LLMClient
from src.task2.data_loader import AccountDataLoader
from src.task2.schemas import TAMBrief, OpenRiskItem
from src.task2.prompts import TAM_SYSTEM_PROMPT, TAM_USER_PROMPT_TEMPLATE


def robust_json_loads(text: str) -> Dict[str, Any]:
    """
    Cleans and robustly parses JSON responses from LLM, handling markdown fences,
    trailing commas, unescaped characters, and common formatting glitches.
    """
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Attempt 1: Direct JSON load
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2: Extract first balanced JSON object { ... }
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Fix trailing commas
            sanitized = re.sub(r",\s*([\]\}])", r"\1", candidate)
            # Fix unquoted keys if any
            sanitized = re.sub(r'(\w+):', r'"\1":', sanitized)
            try:
                return json.loads(sanitized)
            except Exception:
                pass

    raise ValueError(f"Failed to parse LLM response into valid JSON:\n{text}")


class TAMSummarizer:
    """
    TAM Account Health Summariser (Task 2).
    Generates actionable, deterministic 3-section QBR account briefs with rule-assisted churn risk detection,
    direct ticket quotation justifications, and self-healing JSON retry capabilities.
    """

    def __init__(self, data_loader: Optional[AccountDataLoader] = None):
        self.data_loader = data_loader or AccountDataLoader()
        self.llm = LLMClient()
        self._cache: Dict[str, TAMBrief] = {}

    def _compute_input_hash(self, user_prompt: str) -> str:
        """
        Computes a deterministic MD5 hash of the formatted prompt.
        """
        return hashlib.md5(user_prompt.encode("utf-8")).hexdigest()

    def generate_brief(self, account_id: str, use_cache: bool = True) -> TAMBrief:
        """
        Generates a comprehensive TAM Brief for the given account_id.
        Ensures strict multi-layer determinism and resilience via:
        - Deterministic ticket & risk sorting
        - Rule-based risk preprocessing
        - temperature=0.0 and fixed seed
        - Self-healing JSON repair retry
        - Deterministic prompt caching
        """
        # 1. Fetch Account Data (deterministic lookup)
        account = self.data_loader.get_account(account_id)
        if not account:
            raise ValueError(f"Account ID '{account_id}' not found in accounts dataset.")

        # 2. Fetch Last 90 Days Tickets (deterministically sorted newest first)
        tickets = self.data_loader.get_tickets_last_90_days(account_id)

        # 3. Deterministic Pre-risk Detection (rule-based extraction of evidence quotes)
        detected_risks = self.data_loader.detect_deterministic_risks(account, tickets)

        # 4. Calculate metrics and renewal timeline
        licensed = account.get("seats_licensed") or 1
        active = account.get("seats_active") or 0
        seat_utilization_pct = round((active / licensed) * 100.0, 1)

        renewal_status_text, _ = self.data_loader.get_renewal_status(account.get("renewal_date"))

        escalation_notes = account.get("escalation_notes") or []
        if escalation_notes:
            formatted_notes = "\n".join([f"- {note}" for note in escalation_notes])
        else:
            formatted_notes = "None recorded."

        # 5. Format Pre-detected Risks Context
        if detected_risks:
            risk_blocks = []
            for r in detected_risks:
                t_id_str = f" [Ticket: {r['ticket_id']}]" if r.get('ticket_id') else " [Account-Level]"
                risk_blocks.append(
                    f"• Type: {r['risk_type']} | Severity: {r['severity']}{t_id_str}\n"
                    f"  Reason: {r['reason']}\n"
                    f"  Evidence Quote: \"{r['evidence_quote']}\""
                )
            detected_risks_context = "\n".join(risk_blocks)
        else:
            detected_risks_context = "No critical risk signals identified in rule scan."

        # 6. Format Tickets Context
        if tickets:
            tickets_blocks = []
            for t in tickets:
                t_block = (
                    f"Ticket ID: {t.get('ticket_id', 'N/A')}\n"
                    f"Date: {t.get('created_at', 'N/A')}\n"
                    f"Product: {t.get('product', 'N/A')} ({t.get('product_area', 'N/A')})\n"
                    f"Category: {t.get('category', 'N/A')} | Urgency: {t.get('urgency', 'N/A')} | Status: {t.get('status', 'N/A')}\n"
                    f"Subject: {t.get('subject', '')}\n"
                    f"Body:\n{t.get('body', '')}\n"
                )
                tickets_blocks.append(t_block)
            tickets_context = "\n---\n".join(tickets_blocks)
        else:
            tickets_context = "No support tickets opened in the last 90 days."

        # 7. Build User Prompt
        primary_contact = account.get("primary_contact") or {}
        user_prompt = TAM_USER_PROMPT_TEMPLATE.format(
            account_id=account.get("account_id", account_id),
            company=account.get("company", "Unknown"),
            tam=account.get("tam", "Unassigned"),
            plan_tier=account.get("plan_tier", "Standard"),
            industry=account.get("industry", "N/A"),
            region=account.get("region", "N/A"),
            arr_usd=float(account.get("arr_usd") or 0.0),
            seats_licensed=licensed,
            seats_active=active,
            seat_utilization_pct=seat_utilization_pct,
            customer_since=account.get("customer_since", "N/A"),
            renewal_status_text=renewal_status_text,
            last_qbr_date=account.get("last_qbr_date", "N/A"),
            health_status=account.get("health_status", "N/A"),
            usage_trend=account.get("usage_trend", "N/A"),
            open_tickets=account.get("open_tickets", 0),
            p1_tickets_last_30d=account.get("p1_tickets_last_30d", 0),
            primary_contact_name=primary_contact.get("name", "N/A"),
            primary_contact_title=primary_contact.get("title", "N/A"),
            products=", ".join(account.get("products") or []),
            integrations_active=", ".join(account.get("integrations_active") or []) or "None",
            escalation_notes=formatted_notes,
            risk_count=len(detected_risks),
            detected_risks_context=detected_risks_context,
            ticket_count=len(tickets),
            tickets_context=tickets_context
        )

        prompt_hash = self._compute_input_hash(user_prompt)

        # Check deterministic cache
        if use_cache and prompt_hash in self._cache:
            return self._cache[prompt_hash]

        # 8. Call LLM with Self-Healing Parse Retry Loop
        result_dict = None
        for attempt in range(2):
            try:
                if attempt == 0:
                    raw_response = self.llm.generate(
                        system_prompt=TAM_SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        temperature=0.0,
                        seed=42,
                        max_tokens=2500
                    )
                else:
                    # Repair retry prompt
                    repair_prompt = f"{user_prompt}\n\nIMPORTANT: Previous output failed JSON parsing. Return ONLY a complete, well-formed JSON object without markdown fences or unclosed strings."
                    raw_response = self.llm.generate(
                        system_prompt=TAM_SYSTEM_PROMPT,
                        user_prompt=repair_prompt,
                        temperature=0.0,
                        seed=42,
                        max_tokens=2500
                    )

                result_dict = robust_json_loads(raw_response)
                break
            except Exception as parse_err:
                if attempt == 1:
                    # Deterministic fallback synthesis if LLM fails repeatedly
                    result_dict = {
                        "executive_summary": f"{account.get('company')} is on the {account.get('plan_tier')} plan with ${float(account.get('arr_usd') or 0.0):,.2f} ARR and {seat_utilization_pct}% seat utilization. The account is currently classified as {account.get('health_status')} with an {account.get('usage_trend')} usage trend and {account.get('open_tickets', 0)} open tickets. Contract renewal is {renewal_status_text}.",
                        "open_risks": detected_risks,
                        "talking_points": [
                            f"Review recent performance and open support tickets across {', '.join(account.get('products') or ['enabled products'])}.",
                            f"Discuss adoption roadmap and seat utilization strategies with {primary_contact.get('name', 'the primary contact')}.",
                            f"Align on commercial renewal terms and value milestones ahead of {renewal_status_text}."
                        ]
                    }

        # 9. Merge & Normalize Output Schema
        result_dict["account_id"] = account.get("account_id", account_id)
        result_dict["company"] = account.get("company", "Unknown")
        result_dict["tam_assigned"] = account.get("tam")
        result_dict["health_status"] = account.get("health_status", "Unknown")
        result_dict["arr_usd"] = float(account.get("arr_usd") or 0.0)
        result_dict["seat_utilization_pct"] = seat_utilization_pct
        result_dict["total_tickets_last_90d"] = len(tickets)

        if not result_dict.get("open_risks") and detected_risks:
            result_dict["open_risks"] = detected_risks

        # 10. Validate with Pydantic
        brief = TAMBrief.model_validate(result_dict)

        # Store in deterministic cache
        self._cache[prompt_hash] = brief
        return brief


# Singleton instance for callable function
_tam_instance: Optional[TAMSummarizer] = None


def generate_tam_brief(account_id: str, use_cache: bool = True) -> TAMBrief:
    """
    Exposed callable Python function for Task 2: TAM Account Health Summariser.
    Accepts an account_id string and returns a structured, deterministic TAMBrief.
    """
    global _tam_instance
    if _tam_instance is None:
        _tam_instance = TAMSummarizer()
    return _tam_instance.generate_brief(account_id, use_cache=use_cache)
