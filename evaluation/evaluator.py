import json
import re
from typing import Dict, Any, Tuple, Optional
from src.task1.llm import LLMClient
from src.task1.schemas import TriageResult
from src.task2.schemas import TAMBrief
from src.task2.data_loader import AccountDataLoader


JUDGE_SYSTEM_PROMPT = """You are an impartial AI Quality and Evaluation Judge for Enterprise Customer Support & Account Management systems.
Evaluate the candidate AI output against the input context, ground-truth database records, and expected acceptance criteria.

Provide your evaluation as a valid JSON object with:
{
  "quality_score": 0.95, // float between 0.0 and 1.0
  "passed": true, // boolean
  "critique": "1-2 sentence assessment of correctness, grounding, and professionalism",
  "criteria_scores": {
    "grounding_and_factuality": 1.0,
    "classification_and_routing": 0.9,
    "actionability_and_tone": 0.95
  }
}
"""

JUDGE_TASK1_USER_PROMPT = """Evaluate this Task 1 Ticket Triage output.

INPUT TICKET:
{input_data}

CANDIDATE TRIAGE RESULT:
{candidate_output}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

Return your evaluation in strict JSON format.
"""

JUDGE_TASK2_USER_PROMPT = """Evaluate this Task 2 TAM Account Brief output against the ground truth account and ticket database.

DATABASE GROUND TRUTH CONTEXT:
{input_data}

CANDIDATE TAM BRIEF:
{candidate_output}

ACCEPTANCE CRITERIA:
{acceptance_criteria}

Return your evaluation in strict JSON format.
"""


class EvaluationJudge:
    """
    Hybrid Evaluator supporting rule-based assertions and LLM-as-a-Judge scoring.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.data_loader = AccountDataLoader()

    def evaluate_task1_result(
        self,
        test_case: Dict[str, Any],
        result: Optional[TriageResult],
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a Task 1 triage execution against rule-based expectations and LLM judge.
        """
        expected = test_case.get("expected", {})
        rule_passed = True
        rule_failures = []

        if error:
            return {
                "test_id": test_case["test_id"],
                "name": test_case["name"],
                "type": test_case["type"],
                "passed": False,
                "quality_score": 0.0,
                "critique": f"Execution raised unexpected exception: {str(error)}",
                "rule_passed": False,
                "rule_failures": [str(error)]
            }

        # Rule 1: Product check
        if "product" in expected and result.product:
            if expected["product"].lower() not in result.product.lower():
                rule_failures.append(f"Expected product '{expected['product']}', got '{result.product}'")

        # Rule 2: Category check
        if "category" in expected:
            if expected["category"].lower() != result.category.lower():
                rule_failures.append(f"Expected category '{expected['category']}', got '{result.category}'")
        elif "category_in" in expected:
            if result.category.lower() not in [c.lower() for c in expected["category_in"]]:
                rule_failures.append(f"Category '{result.category}' not in allowed list {expected['category_in']}")

        # Rule 3: Urgency check
        if "urgency" in expected:
            if expected["urgency"] != result.urgency:
                rule_failures.append(f"Expected urgency '{expected['urgency']}', got '{result.urgency}'")
        elif "urgency_in" in expected:
            if result.urgency not in expected["urgency_in"]:
                rule_failures.append(f"Urgency '{result.urgency}' not in allowed list {expected['urgency_in']}")

        # Rule 4: Known issue check
        if "known_issue" in expected:
            if expected["known_issue"] != result.known_issue:
                rule_failures.append(f"Expected known_issue={expected['known_issue']}, got {result.known_issue}")

        # Rule 5: KB Source path check
        if expected.get("known_issue"):
            src_norm = (result.knowledge_base_source or "").replace("\\", "/").lower()
            if "expected_kb_source_substring" in expected:
                if expected["expected_kb_source_substring"].lower() not in src_norm:
                    rule_failures.append(f"Knowledge base source '{result.knowledge_base_source}' did not contain expected substring '{expected['expected_kb_source_substring']}'")
            elif "expected_kb_source_substring_in" in expected:
                if not any(sub.lower() in src_norm for sub in expected["expected_kb_source_substring_in"]):
                    rule_failures.append(f"Knowledge base source '{result.knowledge_base_source}' did not match any of {expected['expected_kb_source_substring_in']}")

        rule_passed = len(rule_failures) == 0

        # LLM-as-a-Judge evaluation for tone, reasoning, and grounding
        try:
            judge_prompt = JUDGE_TASK1_USER_PROMPT.format(
                input_data=json.dumps(test_case["input"], indent=2),
                candidate_output=result.model_dump_json(indent=2),
                acceptance_criteria=test_case["acceptance_criteria"]
            )
            raw_judge = self.llm.generate(
                system_prompt=JUDGE_SYSTEM_PROMPT,
                user_prompt=judge_prompt,
                temperature=0.0,
                seed=42,
                max_tokens=600
            )

            cleaned = raw_judge.strip()
            if "```" in cleaned:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
                if match:
                    cleaned = match.group(1).strip()

            judge_data = json.loads(cleaned)
            judge_score = float(judge_data.get("quality_score", 0.95))
            judge_critique = judge_data.get("critique", "Quality assessment passed.")
        except Exception as e:
            judge_score = 0.95 if rule_passed else 0.40
            judge_critique = f"Rule-based assessment (Judge LLM: {e})"

        # Combined scoring: 50% rules + 50% LLM judge
        rule_score = 1.0 if rule_passed else max(0.0, 1.0 - (0.25 * len(rule_failures)))
        final_score = round(0.5 * rule_score + 0.5 * judge_score, 2)
        passed = final_score >= 0.70 and (rule_passed or test_case["type"] == "adversarial")

        return {
            "test_id": test_case["test_id"],
            "name": test_case["name"],
            "type": test_case["type"],
            "passed": passed,
            "quality_score": final_score,
            "critique": judge_critique,
            "rule_passed": rule_passed,
            "rule_failures": rule_failures,
            "output_preview": {
                "product": result.product,
                "category": result.category,
                "urgency": result.urgency,
                "known_issue": result.known_issue,
                "recommended_team": result.recommended_team
            }
        }

    def evaluate_task2_result(
        self,
        test_case: Dict[str, Any],
        result: Optional[TAMBrief],
        error: Optional[Exception] = None,
        is_deterministic: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a Task 2 TAM brief execution against rule-based expectations and LLM judge.
        """
        expected = test_case.get("expected", {})
        rule_passed = True
        rule_failures = []

        # Handle expected error cases (adversarial)
        if expected.get("should_error"):
            if error:
                return {
                    "test_id": test_case["test_id"],
                    "name": test_case["name"],
                    "type": test_case["type"],
                    "passed": True,
                    "quality_score": 1.0,
                    "critique": f"Successfully handled adversarial input with expected error: {str(error)}",
                    "rule_passed": True,
                    "rule_failures": []
                }
            else:
                return {
                    "test_id": test_case["test_id"],
                    "name": test_case["name"],
                    "type": test_case["type"],
                    "passed": False,
                    "quality_score": 0.0,
                    "critique": "Expected error for invalid account ID, but execution returned result without error.",
                    "rule_passed": False,
                    "rule_failures": ["Did not raise expected error for missing account"]
                }

        if error:
            return {
                "test_id": test_case["test_id"],
                "name": test_case["name"],
                "type": test_case["type"],
                "passed": False,
                "quality_score": 0.0,
                "critique": f"Execution raised unexpected exception: {str(error)}",
                "rule_passed": False,
                "rule_failures": [str(error)]
            }

        # Rule 1: Executive Summary sentence count (3 to 5 sentences)
        sentences = [s for s in re.split(r"[.!?]\s+", result.executive_summary.strip()) if len(s) > 5]
        sentence_count = len(sentences)
        if not (2 <= sentence_count <= 6):  # Tolerant window for punctuation
            rule_failures.append(f"Executive summary should be 3-5 sentences, found {sentence_count}")

        # Rule 2: Health status match
        if "health_status" in expected and result.health_status != expected["health_status"]:
            rule_failures.append(f"Expected health '{expected['health_status']}', got '{result.health_status}'")

        # Rule 3: Minimum open risks
        if "min_open_risks" in expected and len(result.open_risks) < expected["min_open_risks"]:
            rule_failures.append(f"Expected at least {expected['min_open_risks']} open risks, found {len(result.open_risks)}")

        # Rule 4: Required quote substrings
        if "required_quote_substrings" in expected:
            quotes = " ".join([r.evidence_quote for r in result.open_risks])
            for q in expected["required_quote_substrings"]:
                if q.lower() not in quotes.lower():
                    rule_failures.append(f"Missing required evidence quote substring: '{q}'")

        # Rule 5: Minimum talking points
        if "min_talking_points" in expected and len(result.talking_points) < expected["min_talking_points"]:
            rule_failures.append(f"Expected at least {expected['min_talking_points']} talking points, found {len(result.talking_points)}")

        # Rule 6: Determinism assertion
        if expected.get("deterministic") and is_deterministic is False:
            rule_failures.append("Consecutive runs for identical input did not produce deterministic output.")

        rule_passed = len(rule_failures) == 0

        # Build ground-truth context for Judge
        acc_id = test_case["input"].get("account_id", "")
        ground_truth_account = self.data_loader.get_account(acc_id)
        ground_truth_tickets = self.data_loader.get_tickets_last_90_days(acc_id)

        judge_input_context = {
            "requested_account_id": acc_id,
            "account_record_in_database": ground_truth_account,
            "total_tickets_in_database_last_90d": len(ground_truth_tickets),
            "tickets_summary": [
                {"ticket_id": t.get("ticket_id"), "subject": t.get("subject"), "urgency": t.get("urgency")}
                for t in ground_truth_tickets
            ]
        }

        # LLM-as-a-Judge evaluation for executive brief quality
        try:
            judge_prompt = JUDGE_TASK2_USER_PROMPT.format(
                input_data=json.dumps(judge_input_context, indent=2),
                candidate_output=result.model_dump_json(indent=2),
                acceptance_criteria=test_case["acceptance_criteria"]
            )
            raw_judge = self.llm.generate(
                system_prompt=JUDGE_SYSTEM_PROMPT,
                user_prompt=judge_prompt,
                temperature=0.0,
                seed=42,
                max_tokens=600
            )

            cleaned = raw_judge.strip()
            if "```" in cleaned:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
                if match:
                    cleaned = match.group(1).strip()

            judge_data = json.loads(cleaned)
            judge_score = float(judge_data.get("quality_score", 0.95))
            judge_critique = judge_data.get("critique", "TAM brief assessment passed.")
        except Exception as e:
            judge_score = 0.95 if rule_passed else 0.45
            judge_critique = f"Rule-based assessment (Judge LLM: {e})"

        rule_score = 1.0 if rule_passed else max(0.0, 1.0 - (0.25 * len(rule_failures)))
        final_score = round(0.5 * rule_score + 0.5 * judge_score, 2)
        passed = final_score >= 0.70 and rule_passed

        return {
            "test_id": test_case["test_id"],
            "name": test_case["name"],
            "type": test_case["type"],
            "passed": passed,
            "quality_score": final_score,
            "critique": judge_critique,
            "rule_passed": rule_passed,
            "rule_failures": rule_failures,
            "output_preview": {
                "company": result.company,
                "health_status": result.health_status,
                "open_risks_count": len(result.open_risks),
                "talking_points_count": len(result.talking_points)
            }
        }
