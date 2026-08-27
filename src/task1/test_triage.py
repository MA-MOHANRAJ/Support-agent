import sys
import json

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.task1.triage import triage_ticket


def test_free_text_ticket():
    print("\n" + "=" * 70)
    print("TEST 1: RAW FREE-TEXT TICKET (P1 OUTAGE)")
    print("=" * 70)

    raw_text = (
        "URGENT: SecureVault Key Management is completely down in our production environment. "
        "None of our microservices can decrypt API tokens and our entire customer-facing checkout "
        "flow is failing with 500 errors. We need immediate P1 escalation!"
    )
    print("Input:\n", raw_text)

    result = triage_ticket(raw_text)
    print("\nTriage Result:")
    print(result.model_dump_json(indent=2))


def test_structured_ticket():
    print("\n" + "=" * 70)
    print("TEST 2: STRUCTURED SUBJECT + BODY (NO DATASET LABELS)")
    print("=" * 70)

    structured_ticket = {
        "subject": "Webhook from CloudSync not reaching Snowflake",
        "body": (
            "We have observed over 450 webhook delivery failures from CloudSync to Snowflake "
            "over the last 4 hours. Error logs show 401 Unauthorized during handshake. "
            "This is impacting our analytics reporting pipeline."
        ),
        "product": "CloudSync",
        "company": "Gavin Belson Co"
    }
    print("Input:", json.dumps(structured_ticket, indent=2))

    result = triage_ticket(structured_ticket)
    print("\nTriage Result:")
    print(result.model_dump_json(indent=2))


def test_ticket_text_dict():
    print("\n" + "=" * 70)
    print("TEST 3: DICTIONARY WITH 'ticket_text' KEY (PRODUCTION API FORMAT)")
    print("=" * 70)

    api_payload = {
        "ticket_text": "How do I invite new users and configure SAML SSO in CloudSync? We just started onboarding 50 new team members."
    }
    print("Input:", json.dumps(api_payload, indent=2))

    result = triage_ticket(api_payload)
    print("\nTriage Result:")
    print(result.model_dump_json(indent=2))


def main():
    test_free_text_ticket()
    test_structured_ticket()
    test_ticket_text_dict()


if __name__ == "__main__":
    main()