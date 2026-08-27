# Lazy and lightweight exports to prevent circular/heavy dependency loading

def __getattr__(name):
    if name in ("TriageResult", "TicketInput", "Category", "UrgencyTier"):
        from . import schemas
        return getattr(schemas, name)
    elif name in ("TicketTriage", "triage_ticket"):
        from . import triage
        return getattr(triage, name)
    elif name == "LLMClient":
        from . import llm
        return getattr(llm, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
