import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

# Ensure UTF-8 output encoding for Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.task1.triage import triage_ticket
from src.task2.summarizer import generate_tam_brief
from evaluation.evaluator import EvaluationJudge

EVAL_DIR = Path("evaluation")
DATASET_PATH = EVAL_DIR / "eval_dataset.json"
REPORT_JSON_PATH = EVAL_DIR / "eval_report.json"
REPORT_MD_PATH = EVAL_DIR / "eval_report.md"


def run_evaluation():
    print("=" * 80)
    print("AI QUALITY EVALUATION HARNESS — TASKS 1 & 2")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {DATASET_PATH}")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    task1_cases = eval_data.get("task1_test_cases", [])
    task2_cases = eval_data.get("task2_test_cases", [])

    judge = EvaluationJudge()
    results_task1 = []
    results_task2 = []

    start_total = time.time()

    # --------------------------------------------------------------------------
    # EVALUATE TASK 1: Intelligent Ticket Triage Agent
    # --------------------------------------------------------------------------
    print(f"\n[TASK 1] Evaluating {len(task1_cases)} Test Cases...")
    print("-" * 80)

    for tc in task1_cases:
        t0 = time.time()
        print(f"Running [{tc['test_id']}] {tc['name']} ({tc['type']})... ", end="", flush=True)

        res_obj = None
        err_obj = None

        try:
            inp = tc["input"]
            res_obj = triage_ticket(inp)
        except Exception as e:
            err_obj = e

        eval_res = judge.evaluate_task1_result(tc, res_obj, err_obj)
        elapsed = round(time.time() - t0, 2)
        eval_res["latency_seconds"] = elapsed
        results_task1.append(eval_res)

        status_tag = "PASS" if eval_res["passed"] else "FAIL"
        print(f"[{status_tag}] (Score: {eval_res['quality_score']:.2f}, Time: {elapsed}s)")
        if not eval_res["passed"]:
            print(f"   Reason: {eval_res['critique']}")
            if eval_res.get("rule_failures"):
                print(f"   Rule Failures: {eval_res['rule_failures']}")

    # --------------------------------------------------------------------------
    # EVALUATE TASK 2: TAM Account Health Summariser
    # --------------------------------------------------------------------------
    print(f"\n[TASK 2] Evaluating {len(task2_cases)} Test Cases...")
    print("-" * 80)

    for tc in task2_cases:
        t0 = time.time()
        print(f"Running [{tc['test_id']}] {tc['name']} ({tc['type']})... ", end="", flush=True)

        res_obj = None
        err_obj = None
        is_deterministic = None

        try:
            acc_id = tc["input"]["account_id"]
            res_obj = generate_tam_brief(acc_id)

            if tc.get("expected", {}).get("deterministic"):
                # Run second time to verify determinism
                res_obj_2 = generate_tam_brief(acc_id)
                is_deterministic = (res_obj.model_dump() == res_obj_2.model_dump())
        except Exception as e:
            err_obj = e

        eval_res = judge.evaluate_task2_result(tc, res_obj, err_obj, is_deterministic)
        elapsed = round(time.time() - t0, 2)
        eval_res["latency_seconds"] = elapsed
        results_task2.append(eval_res)

        status_tag = "PASS" if eval_res["passed"] else "FAIL"
        print(f"[{status_tag}] (Score: {eval_res['quality_score']:.2f}, Time: {elapsed}s)")
        if not eval_res["passed"]:
            print(f"   Reason: {eval_res['critique']}")
            if eval_res.get("rule_failures"):
                print(f"   Rule Failures: {eval_res['rule_failures']}")

    total_time = round(time.time() - start_total, 2)

    # --------------------------------------------------------------------------
    # COMPUTE METRICS
    # --------------------------------------------------------------------------
    all_results = results_task1 + results_task2
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r["passed"])
    pass_rate = round((passed_tests / total_tests) * 100.0, 1)
    avg_quality = round(sum(r["quality_score"] for r in all_results) / total_tests, 2)

    t1_pass = sum(1 for r in results_task1 if r["passed"])
    t1_avg = round(sum(r["quality_score"] for r in results_task1) / len(results_task1), 2)

    t2_pass = sum(1 for r in results_task2 if r["passed"])
    t2_avg = round(sum(r["quality_score"] for r in results_task2) / len(results_task2), 2)

    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Test Cases : {total_tests}")
    print(f"Tests Passed     : {passed_tests}/{total_tests} ({pass_rate}%)")
    print(f"Mean Quality Score: {avg_quality:.2f} / 1.00")
    print(f"Task 1 Pass Rate : {t1_pass}/{len(results_task1)} (Avg Score: {t1_avg:.2f})")
    print(f"Task 2 Pass Rate : {t2_pass}/{len(results_task2)} (Avg Score: {t2_avg:.2f})")
    print(f"Total Execution  : {total_time}s")

    # --------------------------------------------------------------------------
    # SAVE JSON REPORT
    # --------------------------------------------------------------------------
    summary_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate_pct": pass_rate,
            "average_quality_score": avg_quality,
            "total_duration_seconds": total_time,
            "task1": {
                "total": len(results_task1),
                "passed": t1_pass,
                "average_score": t1_avg
            },
            "task2": {
                "total": len(results_task2),
                "passed": t2_pass,
                "average_score": t2_avg
            }
        },
        "task1_results": results_task1,
        "task2_results": results_task2
    }

    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    # --------------------------------------------------------------------------
    # SAVE MARKDOWN REPORT
    # --------------------------------------------------------------------------
    md_lines = [
        "# AI Evaluation Harness Summary Report",
        "",
        f"**Generated on**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Overall Pass Rate**: **{pass_rate}%** ({passed_tests}/{total_tests} Passed)  ",
        f"**Average Quality Score**: **{avg_quality} / 1.00**  ",
        f"**Total Execution Time**: **{total_time}s**",
        "",
        "---",
        "",
        "## Summary by Task",
        "",
        "| Task | Tests | Passed | Pass Rate | Mean Score (0-1) | Status |",
        "|---|---|---|---|---|---|",
        f"| **Task 1: Intelligent Ticket Triage** | {len(results_task1)} | {t1_pass} | {(t1_pass/len(results_task1))*100:.1f}% | {t1_avg:.2f} | {'✅ PASS' if t1_pass == len(results_task1) else '⚠️ PARTIAL'} |",
        f"| **Task 2: TAM Health Summariser** | {len(results_task2)} | {t2_pass} | {(t2_pass/len(results_task2))*100:.1f}% | {t2_avg:.2f} | {'✅ PASS' if t2_pass == len(results_task2) else '⚠️ PARTIAL'} |",
        "",
        "---",
        "",
        "## Detailed Results: Task 1 (Ticket Triage)",
        "",
        "| Test ID | Test Name | Type | Status | Score | Latency | Critique |",
        "|---|---|---|---|---|---|---|"
    ]

    for r in results_task1:
        st = "✅ PASS" if r["passed"] else "❌ FAIL"
        crit = r["critique"].replace("|", "/")
        md_lines.append(f"| `{r['test_id']}` | {r['name']} | `{r['type']}` | {st} | **{r['quality_score']:.2f}** | {r['latency_seconds']}s | {crit} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Detailed Results: Task 2 (TAM Account Health Brief)",
        "",
        "| Test ID | Test Name | Type | Status | Score | Latency | Critique |",
        "|---|---|---|---|---|---|---|"
    ])

    for r in results_task2:
        st = "✅ PASS" if r["passed"] else "❌ FAIL"
        crit = r["critique"].replace("|", "/")
        md_lines.append(f"| `{r['test_id']}` | {r['name']} | `{r['type']}` | {st} | **{r['quality_score']:.2f}** | {r['latency_seconds']}s | {crit} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Quality Gates & Methodology",
        "- **Hybrid Scoring**: Combines deterministic rule-based checks (taxonomy, P1-P4 criteria, strict RAG grounding, direct quote verification) and LLM-as-a-Judge evaluations (factuality, professional tone, actionability).",
        "- **Adversarial Resilience**: Tests system robustness against vague/malformed customer tickets (`T1-TC-05`), missing account IDs (`T2-TC-04`), and zero-ticket history (`T2-TC-05`).",
        "- **Determinism Verification**: Confirms deterministic reproducibility across repeated runs with `temperature=0.0`, fixed seeds, and deterministic caching (`T2-TC-06`)."
    ])

    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n[REPORT SAVED] -> {REPORT_JSON_PATH}")
    print(f"[REPORT SAVED] -> {REPORT_MD_PATH}")

    return summary_report


if __name__ == "__main__":
    run_evaluation()
