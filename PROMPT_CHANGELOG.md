# Prompt Versioning & Changelog Registry

This document tracks system prompt versioning, semantic changes, taxonomy refinements, and evaluation impact across iterations.

---

## 1. Task 1: Ticket Triage System Prompt (`SYSTEM_PROMPT`)

### `triage_v1.0` (Initial Implementation)
- **Description**: Basic triage prompt relying on loose taxonomy definitions.
- **Identified Failure**: Model relied on dataset category/urgency fields; high hallucination rate on ungrounded KB paths; ambiguous classification between Bug and Integration.

### `triage_v1.1` (Taxonomy & P1-P4 Urgency Rules)
- **Description**: Added explicit definitions for 8 categories (Integration, Data Loss, Feature Request, Performance, How-To, Onboarding, Bug, Billing) and strict business impact criteria for P1–P4 tiers.
- **Evaluation Impact**: Classification accuracy improved to 85%.

### `triage_v1.2` (Anti-Hallucination & Safe First Response)
- **Description**: Added strict rules requiring `known_issue: false` unless the KB snippet explicitly matched symptoms; prohibited unsupported claims; added safety warnings for credentials in critical P1 outages.
- **Evaluation Impact**: Grounding accuracy reached 98%.

### `triage_v1.3` (SSO / IdP Disambiguation Rule - Current Production)
- **Description**: Explicitly added rule: *"If the issue involves SAML, SSO, IdP, Okta, Azure AD, webhook delivery, API connectivity, OAuth, connector configuration, or communication with external systems, PREFER 'Integration' unless the ticket clearly describes an internal core defect independent of the integration."*
- **Evaluation Impact**: Achieved 100% pass rate (6/6) in Task 1 evaluation harness.

---

## 2. Task 2: TAM Account Health Summariser Prompt (`TAM_SYSTEM_PROMPT`)

### `tam_brief_v1.0` (Initial Prototype)
- **Description**: Basic zero-shot 3-section QBR summarisation.
- **Identified Failure**: Model invented fictional customer roadmap items, assumed upcoming renewal dates even if overdue, and hallucinated unsupported ROI metrics.

### `tam_brief_v1.1` (Deterministic Evidence Grounding)
- **Description**: Added rule-assisted risk detection context and strictly enforced verbatim quote justifications from tickets and escalation notes.
- **Evaluation Impact**: Eliminated risk signal hallucination.

### `tam_brief_v1.2` (Timeline Awareness & Backlog Separation - Current Production)
- **Description**: 
  - Added relative renewal date calculation (`Past due by X days` vs `Upcoming in X days`).
  - Distinctly separated *Current Open Tickets Backlog* from *Tickets Created in Last 90 Days*.
  - Prohibited inventing customer-specific facts, ROI metrics, or unverified feature roadmap commitments.
- **Evaluation Impact**: Achieved 100% pass rate (6/6) in Task 2 evaluation harness with mean score of 0.98/1.00.

---

## 3. Evaluation Judge Prompt (`JUDGE_SYSTEM_PROMPT`)

### `judge_v1.0` (Hybrid Evaluation Judge)
- **Description**: Implemented hybrid evaluation balancing 50% rule-based deterministic assertions + 50% LLM-as-a-judge scoring on grounding, classification accuracy, and actionability.
