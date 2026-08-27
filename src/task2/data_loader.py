import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional, Tuple


ACCOUNTS_PATH = Path("data/accounts.json")
TICKETS_PATH = Path("data/tickets.json")

# Current assessment reference date (August 2026)
REFERENCE_DATE = date(2026, 8, 27)

CHURN_PATTERNS = [
    r"\b(cancel(?:ling|lation|led)?|churn|leaving|switch(?:ing)?|terminate|refund|competitor|alternative|evaluating other)\b",
    r"\b(unacceptable|unusable|frustrat(?:ed|ing)|disappoint(?:ed|ing)|breach(?:ed)?|sla penalty|degradation|slowly|timing out)\b"
]


class AccountDataLoader:
    """
    Data loading, deterministic querying, timeline analysis, and rule-based risk detection for TAM accounts.
    """

    def __init__(self, accounts_path: Path = ACCOUNTS_PATH, tickets_path: Path = TICKETS_PATH):
        self.accounts_path = accounts_path
        self.tickets_path = tickets_path
        self._accounts: Dict[str, Dict[str, Any]] = {}
        self._tickets_by_account: Dict[str, List[Dict[str, Any]]] = {}
        self._max_dataset_date: Optional[datetime] = None
        self._load_data()

    def _parse_iso(self, date_str: str) -> Optional[datetime]:
        try:
            clean_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
        except Exception:
            return None

    def _load_data(self):
        if not self.accounts_path.exists():
            raise FileNotFoundError(f"Accounts file not found at {self.accounts_path}")

        with open(self.accounts_path, "r", encoding="utf-8") as f:
            accounts_list = json.load(f)

        self._accounts = {
            acc["account_id"].strip().upper(): acc
            for acc in accounts_list
            if "account_id" in acc
        }

        if not self.tickets_path.exists():
            raise FileNotFoundError(f"Tickets file not found at {self.tickets_path}")

        with open(self.tickets_path, "r", encoding="utf-8") as f:
            tickets_list = json.load(f)

        all_dates = []
        for tkt in tickets_list:
            acc_id = tkt.get("account_id", "").strip().upper()
            if not acc_id:
                continue

            if acc_id not in self._tickets_by_account:
                self._tickets_by_account[acc_id] = []
            self._tickets_by_account[acc_id].append(tkt)

            if tkt.get("created_at"):
                dt = self._parse_iso(tkt["created_at"])
                if dt:
                    all_dates.append(dt)

        if all_dates:
            self._max_dataset_date = max(all_dates)
        else:
            self._max_dataset_date = datetime.now(timezone.utc)

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves account summary by account_id (e.g. 'ACC-3336').
        Returns None if account does not exist.
        """
        clean_id = account_id.strip().upper()
        return self._accounts.get(clean_id)

    def get_renewal_status(self, renewal_date_str: Optional[str]) -> Tuple[str, Optional[int]]:
        """
        Calculates renewal timeline relative to current assessment date (2026-08-27).
        Returns human-readable status and days delta.
        """
        if not renewal_date_str:
            return "Renewal date not specified", None
        try:
            r_date = datetime.strptime(renewal_date_str.strip(), "%Y-%m-%d").date()
            delta_days = (r_date - REFERENCE_DATE).days
            if delta_days < 0:
                return f"{renewal_date_str} (Past due by {abs(delta_days)} days — urgent follow-up required)", delta_days
            elif delta_days == 0:
                return f"{renewal_date_str} (Due today — renewal action required immediately)", 0
            else:
                return f"{renewal_date_str} (Upcoming in {delta_days} days)", delta_days
        except Exception:
            return str(renewal_date_str), None

    def get_tickets_last_90_days(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all support tickets for an account within the last 90 days.
        Deterministically sorted by created_at DESC, then ticket_id.
        """
        clean_id = account_id.strip().upper()
        account_tickets = self._tickets_by_account.get(clean_id, [])

        if not account_tickets:
            acc = self.get_account(clean_id)
            if acc and acc.get("company"):
                comp_name = acc["company"].strip().lower()
                account_tickets = [
                    t for t_list in self._tickets_by_account.values()
                    for t in t_list
                    if t.get("company", "").strip().lower() == comp_name
                ]

        cutoff_date = self._max_dataset_date - timedelta(days=90)

        filtered = []
        for tkt in account_tickets:
            created_str = tkt.get("created_at")
            if created_str:
                dt = self._parse_iso(created_str)
                if dt and dt >= cutoff_date:
                    filtered.append((dt, tkt.get("ticket_id", ""), tkt))
                elif not dt:
                    filtered.append((self._max_dataset_date, tkt.get("ticket_id", ""), tkt))
            else:
                filtered.append((self._max_dataset_date, tkt.get("ticket_id", ""), tkt))

        # Deterministic sorting: newest first, then ticket_id
        filtered.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [item[2] for item in filtered]

    def detect_deterministic_risks(self, account: Dict[str, Any], tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rule-based deterministic risk detection on account metadata and ticket history.
        Extracts verified, high-impact verbatim evidence quotes directly from records.
        """
        detected_risks = []

        # 1. Check Historical Escalation Notes
        for note in account.get("escalation_notes") or []:
            note_lower = note.lower()
            if "compet" in note_lower or "vendor" in note_lower or "evaluat" in note_lower:
                detected_risks.append({
                    "risk_type": "Competitor Evaluation",
                    "severity": "Critical",
                    "ticket_id": None,
                    "reason": "Executive stakeholder is actively evaluating competing alternative vendors.",
                    "evidence_quote": note
                })
            elif "p1" in note_lower or "consecutive" in note_lower or "escalat" in note_lower:
                detected_risks.append({
                    "risk_type": "Escalation",
                    "severity": "High",
                    "ticket_id": None,
                    "reason": "Account has suffered multiple high-priority P1 outages impacting trust.",
                    "evidence_quote": note
                })
            else:
                detected_risks.append({
                    "risk_type": "Escalation",
                    "severity": "Medium",
                    "ticket_id": None,
                    "reason": "Recorded account escalation issue.",
                    "evidence_quote": note
                })

        # 2. Check Usage Trend & Renewal Posture
        usage_trend = account.get("usage_trend", "")
        licensed = account.get("seats_licensed") or 1
        active = account.get("seats_active") or 0
        pct = round((active / licensed) * 100.0, 1)

        if usage_trend in ["Inactive", "Declining"]:
            detected_risks.append({
                "risk_type": "Usage Drop",
                "severity": "High" if usage_trend == "Inactive" else "Medium",
                "ticket_id": None,
                "reason": f"Account usage trend is currently '{usage_trend}' ({active}/{licensed} active seats).",
                "evidence_quote": f"Usage trend: {usage_trend} ({active}/{licensed} active seats, {pct}% utilization)"
            })

        # 3. Check Tickets for Churn / Escalation / Severe Performance Issues
        for tkt in tickets:
            tkt_id = tkt.get("ticket_id", "N/A")
            urgency = tkt.get("urgency", "")
            subject = tkt.get("subject", "")
            body = tkt.get("body", "")
            combined_text = f"{subject}\n{body}"

            # Check P1 severity
            if urgency == "P1":
                detected_risks.append({
                    "risk_type": "Escalation",
                    "severity": "Critical",
                    "ticket_id": tkt_id,
                    "reason": f"Critical P1 production incident in {tkt.get('product', 'product')}.",
                    "evidence_quote": subject
                })

            # Check for high-impact performance / blocker signals
            matched_sentence = ""
            for pat in CHURN_PATTERNS:
                match = re.search(pat, combined_text, re.IGNORECASE)
                if match:
                    sentences = [s.strip() for s in re.split(r"[\n\.\?!]", combined_text) if len(s.strip()) > 15]
                    for s in sentences:
                        if match.group(0).lower() in s.lower():
                            matched_sentence = s
                            break
                    if not matched_sentence:
                        matched_sentence = subject

                    risk_category = "Product Blocker" if any(w in match.group(0).lower() for w in ["degradation", "slowly", "timing out", "unusable"]) else "Churn Risk"
                    detected_risks.append({
                        "risk_type": risk_category,
                        "severity": "High",
                        "ticket_id": tkt_id,
                        "reason": f"Severe impact reported in {tkt.get('product', 'product')} ({tkt.get('product_area', 'module')}).",
                        "evidence_quote": matched_sentence[:180]
                    })
                    break

        # Deterministic sorting: Critical -> High -> Medium -> Low
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        detected_risks.sort(key=lambda r: (severity_order.get(r["severity"], 9), r.get("ticket_id") or ""))
        return detected_risks
