import pytest
from src.task1.triage import triage_ticket
from src.task2.summarizer import generate_tam_brief
from evaluation.evaluator import EvaluationJudge


@pytest.fixture
def judge():
    return EvaluationJudge()


def test_task1_p1_outage(judge):
    test_case = {
        "test_id": "T1-TC-01",
        "name": "P1 Production Outage",
        "type": "standard",
        "input": {
            "ticket_text": "URGENT: SecureVault Key Management is completely down in our production environment. None of our microservices can decrypt API tokens and our entire customer-facing checkout flow is failing with 500 errors. We need immediate P1 escalation!"
        },
        "expected": {
            "category": "Bug",
            "urgency": "P1",
            "known_issue": False
        },
        "acceptance_criteria": "Must classify as P1 Bug and route to Security/Tier 2."
    }
    result = triage_ticket(test_case["input"])
    eval_res = judge.evaluate_task1_result(test_case, result)
    assert eval_res["passed"] is True, f"Failed: {eval_res['critique']}"
    assert eval_res["quality_score"] >= 0.75


def test_task1_known_issue_rag(judge):
    test_case = {
        "test_id": "T1-TC-02",
        "name": "Integration Issue with Known Knowledge Base Match",
        "type": "standard",
        "input": {
            "subject": "SSO configuration not working for new users — CloudSync",
            "body": "Existing users can log in fine via Okta SSO, but all newly added employees receive an error when attempting to authenticate in CloudSync. We need guidance on how to fix this for our team.",
            "product": "CloudSync",
            "product_area": "Integrations"
        },
        "expected": {
            "category_in": ["Integration", "Bug"],
            "known_issue": True,
            "expected_kb_source_substring_in": ["authentication-sso", "cloudsync"]
        },
        "acceptance_criteria": "Must identify category as Integration, detect known_issue=true, and cite authentic doc."
    }
    result = triage_ticket(test_case["input"])
    eval_res = judge.evaluate_task1_result(test_case, result)
    assert eval_res["passed"] is True, f"Failed: {eval_res['critique']}"


def test_task1_adversarial_vague_ticket(judge):
    test_case = {
        "test_id": "T1-TC-05",
        "name": "Adversarial: Vague Ticket",
        "type": "adversarial",
        "input": {
            "ticket_text": "Nothing works. Fix this immediately or we will cancel our account today."
        },
        "expected": {
            "known_issue": False
        },
        "acceptance_criteria": "Must handle graceful ingestion and avoid hallucinating known KB documents."
    }
    result = triage_ticket(test_case["input"])
    eval_res = judge.evaluate_task1_result(test_case, result)
    assert eval_res["passed"] is True


def test_task2_at_risk_account(judge):
    test_case = {
        "test_id": "T2-TC-01",
        "name": "At-Risk Account with Churn Signals",
        "type": "standard",
        "input": {"account_id": "ACC-3336"},
        "expected": {
            "health_status": "At Risk",
            "min_open_risks": 2
        },
        "acceptance_criteria": "Must produce Executive Summary and detect risks with quotes."
    }
    result = generate_tam_brief(test_case["input"]["account_id"])
    eval_res = judge.evaluate_task2_result(test_case, result)
    assert eval_res["passed"] is True, f"Failed: {eval_res['critique']}"
    assert eval_res["quality_score"] >= 0.75


def test_task2_adversarial_missing_account(judge):
    test_case = {
        "test_id": "T2-TC-04",
        "name": "Adversarial: Non-Existent Account ID",
        "type": "adversarial",
        "input": {"account_id": "ACC-9999"},
        "expected": {"should_error": True},
        "acceptance_criteria": "Must cleanly reject invalid account ID."
    }
    err = None
    res = None
    try:
        res = generate_tam_brief(test_case["input"]["account_id"])
    except Exception as e:
        err = e
    eval_res = judge.evaluate_task2_result(test_case, res, error=err)
    assert eval_res["passed"] is True
