import json
import os
from typing import List, Dict, Any
from .models import Ticket, Account

def load_accounts(data_path: str) -> Dict[str, Account]:
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    accounts = {}
    for item in raw_data:
        acc = Account(**item)
        accounts[acc.account_id] = acc
    return accounts

def load_tickets(data_path: str) -> List[Ticket]:
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    return [Ticket(**item) for item in raw_data]
