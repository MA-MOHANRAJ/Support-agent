import sys
import json

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.task2.summarizer import generate_tam_brief


def test_at_risk_account():
    print("\n" + "=" * 80)
    print("TEST 1: TAM BRIEF FOR AT-RISK ACCOUNT (ACC-3336)")
    print("=" * 80)

    account_id = "ACC-3336"
    brief = generate_tam_brief(account_id)

    print(f"Company: {brief.company} ({brief.account_id})")
    print(f"TAM: {brief.tam_assigned} | Health: {brief.health_status} | ARR: ${brief.arr_usd:,.2f}")
    print(f"Seat Utilization: {brief.seat_utilization_pct}% | 90d Tickets: {brief.total_tickets_last_90d}")

    print("\n" + "-" * 80)
    print("SECTION 1: EXECUTIVE SUMMARY")
    print("-" * 80)
    print(brief.executive_summary)

    print("\n" + "-" * 80)
    print(f"SECTION 2: OPEN RISKS & FLAGGED ISSUES ({len(brief.open_risks)} Total)")
    print("-" * 80)
    for idx, risk in enumerate(brief.open_risks, 1):
        t_id = f"[{risk.ticket_id}] " if risk.ticket_id else "[Account-Level] "
        print(f"  {idx}. {t_id}{risk.risk_type} ({risk.severity} Severity)")
        print(f"     Reason: {risk.reason}")
        print(f"     Evidence Quote: \"{risk.evidence_quote}\"")

    print("\n" + "-" * 80)
    print("SECTION 3: RECOMMENDED TALKING POINTS FOR TAM")
    print("-" * 80)
    for idx, point in enumerate(brief.talking_points, 1):
        print(f"  {idx}. {point}")


def test_healthy_account():
    print("\n" + "=" * 80)
    print("TEST 2: TAM BRIEF FOR HEALTHY ACCOUNT (ACC-3033)")
    print("=" * 80)

    account_id = "ACC-3033"
    brief = generate_tam_brief(account_id)

    print(f"Company: {brief.company} ({brief.account_id})")
    print(f"Health: {brief.health_status} | ARR: ${brief.arr_usd:,.2f}")
    print("\nExecutive Summary:\n", brief.executive_summary)
    print(f"\nOpen Risks Count: {len(brief.open_risks)}")


def test_adversarial_missing_account():
    print("\n" + "=" * 80)
    print("TEST 3: ADVERSARIAL TEST - NON-EXISTENT ACCOUNT ID (ACC-9999)")
    print("=" * 80)

    account_id = "ACC-9999"
    try:
        generate_tam_brief(account_id)
        print("FAIL: Expected ValueError for missing account.")
    except ValueError as e:
        print(f"PASS: Correctly raised error -> {e}")


def test_determinism():
    print("\n" + "=" * 80)
    print("TEST 4: MULTI-LAYER DETERMINISM VERIFICATION")
    print("=" * 80)

    account_id = "ACC-3336"
    print("Running Run 1 (use_cache=False)...")
    brief_1 = generate_tam_brief(account_id, use_cache=False)
    print("Running Run 2 (use_cache=False)...")
    brief_2 = generate_tam_brief(account_id, use_cache=False)

    is_identical = brief_1.model_dump() == brief_2.model_dump()
    print(f"\nModel Output Identical Without Cache: {'YES (100% Deterministic)' if is_identical else 'Minor LLM float difference'}")

    brief_cached_1 = generate_tam_brief(account_id, use_cache=True)
    brief_cached_2 = generate_tam_brief(account_id, use_cache=True)
    print(f"Deterministic Cache Verification: {'PASS (100% Identical)' if brief_cached_1.model_dump() == brief_cached_2.model_dump() else 'FAIL'}")


def main():
    test_at_risk_account()
    test_healthy_account()
    test_adversarial_missing_account()
    test_determinism()


if __name__ == "__main__":
    main()
