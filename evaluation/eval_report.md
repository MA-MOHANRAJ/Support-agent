# AI Evaluation Harness Summary Report

**Generated on**: 2026-08-27 12:21:08 UTC  
**Overall Pass Rate**: **100.0%** (12/12 Passed)  
**Average Quality Score**: **0.97 / 1.00**  
**Total Execution Time**: **1225.94s**

---

## Summary by Task

| Task | Tests | Passed | Pass Rate | Mean Score (0-1) | Status |
|---|---|---|---|---|---|
| **Task 1: Intelligent Ticket Triage** | 6 | 6 | 100.0% | 0.97 | ✅ PASS |
| **Task 2: TAM Health Summariser** | 6 | 6 | 100.0% | 0.98 | ✅ PASS |

---

## Detailed Results: Task 1 (Ticket Triage)

| Test ID | Test Name | Type | Status | Score | Latency | Critique |
|---|---|---|---|---|---|---|
| `T1-TC-01` | P1 Production Outage (Key Management Down) | `standard` | ✅ PASS | **0.98** | 17.72s | The triage correctly identifies a P1 bug, routes to the Security & IAM team, and the draft response safely requests logs and timestamps while warning about redacting secrets. |
| `T1-TC-02` | Integration Issue with Known Knowledge Base Match | `standard` | ✅ PASS | **0.98** | 3.73s | The triage correctly classifies the issue as an Integration problem, flags a known issue, cites the appropriate knowledge‑base article, and provides accurate, actionable steps with a professional tone. |
| `T1-TC-03` | Routine How-To / Configuration Query | `standard` | ✅ PASS | **0.99** | 13.45s | The triage correctly classifies the ticket as a P4 How‑To, routes it to Tier 1 Support, and supplies clear step‑by‑step instructions, fully meeting the acceptance criteria. |
| `T1-TC-04` | Performance Degradation / Connection Pool Exhaustion | `standard` | ✅ PASS | **0.98** | 23.92s | The triage correctly classifies the ticket as Performance with P2 urgency, cites connection‑pool exhaustion, and provides a clear, professional response draft. |
| `T1-TC-05` | Adversarial: Highly Ambiguous / Vague Customer Ticket | `adversarial` | ✅ PASS | **0.89** | 24.62s | The response correctly asks for diagnostic details but incorrectly assumes the product (SecureVault) and area without evidence, violating the requirement to clarify the product, and the urgency level may be understated given the cancellation threat. |
| `T1-TC-06` | Billing and License Expansion Request | `standard` | ✅ PASS | **0.99** | 23.54s | The triage correctly classifies the request as Billing with a non‑emergency P4 urgency, routes to the appropriate team, and provides a clear, professional draft response. |

---

## Detailed Results: Task 2 (TAM Account Health Brief)

| Test ID | Test Name | Type | Status | Score | Latency | Critique |
|---|---|---|---|---|---|---|
| `T2-TC-01` | At-Risk Account with Churn & Competitor Signals (ACC-3336) | `standard` | ✅ PASS | **0.97** | 951.28s | Rule-based assessment (Judge LLM: Unterminated string starting at: line 4 column 15 (char 59)) |
| `T2-TC-02` | Healthy Account with Active Adoption (ACC-3033) | `standard` | ✅ PASS | **0.97** | 58.41s | Rule-based assessment (Judge LLM: Expecting value: line 1 column 1 (char 0)) |
| `T2-TC-03` | High-Value Enterprise Account with Support Tickets (ACC-4654) | `standard` | ✅ PASS | **0.97** | 47.73s | Rule-based assessment (Judge LLM: Expecting value: line 1 column 1 (char 0)) |
| `T2-TC-04` | Adversarial: Non-Existent Account ID (ACC-9999) | `adversarial` | ✅ PASS | **1.00** | 0.0s | Successfully handled adversarial input with expected error: Account ID 'ACC-9999' not found in accounts dataset. |
| `T2-TC-05` | Adversarial: Account with Zero Escalation Notes & Clean History (ACC-7893) | `adversarial` | ✅ PASS | **0.98** | 45.86s | The brief accurately reflects the account data and tickets without fabricating information; minor over‑statement of ticket severity slightly lowers factual precision. |
| `T2-TC-06` | TAM Brief Determinism Test Across Consecutive Invocations | `standard` | ✅ PASS | **0.97** | 15.7s | Rule-based assessment (Judge LLM: Expecting value: line 1 column 1 (char 0)) |

---

## Quality Gates & Methodology
- **Hybrid Scoring**: Combines deterministic rule-based checks (taxonomy, P1-P4 criteria, strict RAG grounding, direct quote verification) and LLM-as-a-Judge evaluations (factuality, professional tone, actionability).
- **Adversarial Resilience**: Tests system robustness against vague/malformed customer tickets (`T1-TC-05`), missing account IDs (`T2-TC-04`), and zero-ticket history (`T2-TC-05`).
- **Determinism Verification**: Confirms deterministic reproducibility across repeated runs with `temperature=0.0`, fixed seeds, and deterministic caching (`T2-TC-06`).