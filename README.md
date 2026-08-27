# Production-Grade AI Platform for Technical Support & TAM Teams

[![CI Evaluation](https://github.com/your-org/zycus-assessment/actions/workflows/eval.yml/badge.svg)](https://github.com)
[![Pass Rate](https://img.shields.io/badge/Evaluation%20Pass%20Rate-100%25%20(12%2F12)-brightgreen)](./evaluation/eval_report.md)
[![Quality Score](https://img.shields.io/badge/Mean%20Quality%20Score-0.97%20%2F%201.00-blue)](./evaluation/eval_report.json)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)](https://fastapi.tiangolo.com/)

An enterprise-ready AI platform powering **Technical Support Engineers** (Task 1) and **Technical Account Managers** (Task 2), backed by an automated **Hybrid Evaluation Harness** (Task 3), production-grade **Design Note** (Task 4), and interactive **Streamlit UI**.

---

## 📋 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Quickstart & Setup](#-quickstart--setup)
3. [Task 1: Intelligent Ticket Triage Agent](#-task-1-intelligent-ticket-triage-agent)
4. [Task 2: TAM Account Health Summariser](#-task-2-tam-account-health-summariser)
5. [Task 3: AI Quality Evaluation Harness](#-task-3-ai-quality-evaluation-harness)
6. [Task 4: Technical Design Note](#-task-4-technical-design-note)
7. [Bonus Features & Capabilities](#-bonus-features--capabilities)
8. [Project Structure](#-project-structure)

---

## 🏗️ Architecture Overview

```
                      ┌──────────────────────────────────────────┐
                      │        Incoming Support Ticket           │
                      │   (Raw Free-Text or Structured JSON)     │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │    RAG Engine (FAISS + MiniLM-L6-v2)     │
                      │    Retrieves Grounded Knowledge Chunks   │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
┌────────────────────────┐    ┌─────────────────────────┐    ┌────────────────────────┐
│  Taxonomy & P1-P4 Gate │───▶│  LLM Structured Engine  │───▶│ Pydantic Validation &  │
│  SSO/IdP Routing Rules │    │   (openai/gpt-oss-120b) │    │ Draft Response Safety  │
└────────────────────────┘    └─────────────────────────┘    └───────────┬────────────┘
                                                                         │
                                                                         ▼
                                                             ┌────────────────────────┐
                                                             │ TriageResult (Task 1)  │
                                                             └────────────────────────┘

                      ┌──────────────────────────────────────────┐
                      │               Account ID                 │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
                      ┌──────────────────────────────────────────┐
                      │  Deterministic DataLoader & Risk Engine  │
                      │  • 90-Day Ticket Filter & Sorter         │
                      │  • Renewal Timeline Status (Past/Future) │
                      │  • Verbatim Quote Extraction (Substrings)│
                      │  • Backlog vs 90d Ticket Disambiguation  │
                      └────────────────────┬─────────────────────┘
                                           │
                                           ▼
┌────────────────────────┐    ┌─────────────────────────┐    ┌────────────────────────┐
│ Multi-Layer Determinism│───▶│   TAM Summary Engine    │───▶│  TAMBrief (Task 2)     │
│ (Temp 0.0 + Seed 42 +  │    │  (Self-Healing Parser + │    │  • 3-5 Sent Summary    │
│  Hash Prompt Cache)    │    │   Deterministic Fallback)│   │  • Quoted Open Risks   │
└────────────────────────┘    └─────────────────────────┘    │  • Grounded TAM Points │
                                                             └────────────────────────┘
```

---

## ⚡ Quickstart & Setup

### 1. Prerequisites & Environment Setup
Clone the repository and install all dependencies:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your LLM API credentials:
```bash
cp .env.example .env
```
Edit `.env`:
```env
LLM_API_KEY=your_groq_or_openai_api_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
```

### 3. Build Vector Embeddings (RAG Index)
Ingest the Markdown knowledge base into the local FAISS vector store:
```bash
python -m src.rag.ingest
```

---

## 🎫 Task 1: Intelligent Ticket Triage Agent

Ingests raw incoming tickets without any human labelling and produces structured classification, urgency prioritisations (P1–P4), knowledge base citations, responder team routing, and safe first-response drafts.

### Python Function Call:
```python
from src.task1.triage import triage_ticket

result = triage_ticket("URGENT: SecureVault Key Management is down in production. None of our microservices can decrypt tokens.")
print(result.model_dump_json(indent=2))
```

### CLI Sample Execution:
```bash
python -m src.task1.test_triage
```

### REST API Server & Endpoint:
```bash
# Start FastAPI backend
uvicorn app.main:app --reload --port 8000
```
**Endpoint**: `POST http://127.0.0.1:8000/api/triage`  
**Request Body**:
```json
{
  "ticket_text": "SSO configuration not working for new users in CloudSync. Existing users log in fine via Okta, but new joiners receive errors."
}
```

---

## 📊 Task 2: TAM Account Health Summariser

Auto-generates a 3-section QBR account brief from structured customer records and 90-day ticket history. Features rule-assisted risk detection, direct verbatim quote justifications, and strict multi-layer determinism.

### Python Function Call:
```python
from src.task2.summarizer import generate_tam_brief

brief = generate_tam_brief("ACC-3336")
print(brief.model_dump_json(indent=2))
```

### CLI Sample Execution:
```bash
python -m src.task2.test_tam
```

### REST API Endpoints:
- `POST /api/tam/brief` with body `{"account_id": "ACC-3336"}`
- `GET /api/tam/brief/ACC-3336`

---

## 🧪 Task 3: AI Quality Evaluation Harness

A comprehensive evaluation framework testing both Task 1 and Task 2 across 12 test cases (standard + adversarial) using a **Hybrid Evaluation Judge** (50% rule-based deterministic assertions + 50% LLM-as-a-judge).

### Running Evaluation Harness:
```bash
python -m evaluation.evaluate
```

### Running Pytest Suite:
```bash
pytest -v
```

### Evaluation Benchmark Summary (100% Pass Rate):
| Task | Tests | Passed | Pass Rate | Mean Score | Status |
|---|---|---|---|---|---|
| **Task 1: Intelligent Ticket Triage** | 6 | 6 | **100.0%** | **0.97 / 1.00** | ✅ PASS |
| **Task 2: TAM Health Summariser** | 6 | 6 | **100.0%** | **0.98 / 1.00** | ✅ PASS |
| **Total Evaluation** | **12** | **12** | **100.0%** | **0.97 / 1.00** | ✅ PASS |

📄 Full Reports:
- [evaluation/eval_report.md](./evaluation/eval_report.md)
- [evaluation/eval_report.json](./evaluation/eval_report.json)

---

## 📝 Task 4: Technical Design Note

Read the complete 600-word engineering design document: **[DESIGN_NOTE.md](./DESIGN_NOTE.md)**.

Covers:
1. **Top 3 Production Failure Modes, Detection & Mitigations** (RAG semantic drift, LLM hallucination of customer facts, API rate-limit/token exhaustion).
2. **Latency vs. Quality Trade-Offs** (Hybrid RAG + 2-stage validation vs. sub-200ms SLM/speculative streaming).
3. **Data Sensitivity & PII Handling** (Pre-inference sanitization, credential guard prompts, Zero Data Retention).
4. **Scaling to 10× Ticket Volume** (Asynchronous message queues, distributed vector storage, tiered LLM routing).

---

## 🌟 Bonus Features & Capabilities

1. **Interactive Streamlit UI Demo (+5 Marks)**:
   ```bash
   streamlit run app/ui.py
   ```
   Interactive web console for Technical Support Engineers & TAMs with live KPI cards, risk drawers, and editable response drafts.

2. **Automated CI/CD Pipeline (+2 Marks)**:
   - Configured in [`.github/workflows/eval.yml`](./.github/workflows/eval.yml) running regression testing on every push.

3. **Prompt Versioning & Changelog Registry (+2 Marks)**:
   - Detailed in [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md) tracking evolution from `v1.0` through `v1.3`.

---

## 📂 Project Structure

```
zycus-assessment/
├── app/
│   ├── main.py                  # FastAPI server exposing /api/triage and /api/tam/brief
│   └── ui.py                    # Streamlit Interactive Web Application (Bonus)
├── data/
│   ├── accounts.json            # 50 synthetic customer accounts
│   └── tickets.json             # 500 synthetic support tickets
├── evaluation/
│   ├── eval_dataset.json        # 12 benchmark test cases (standard + adversarial)
│   ├── evaluator.py             # Hybrid scoring engine (Rules + LLM-as-a-judge)
│   ├── evaluate.py              # Main evaluation harness CLI runner
│   ├── eval_report.json         # Automated JSON evaluation report
│   ├── eval_report.md           # Automated Markdown evaluation report
│   └── test_eval_harness.py     # Pytest test suite
├── knowledge-base/              # Markdown product & troubleshooting documentation
├── src/
│   ├── rag/
│   │   ├── ingest.py            # FAISS vector indexing & document chunking
│   │   └── retrieve.py          # Semantic similarity search & KB retrieval
│   ├── task1/
│   │   ├── schemas.py           # Pydantic schemas (TriageResult, TicketInput)
│   │   ├── prompts.py           # Taxonomy, P1-P4 rules, anti-hallucination prompts
│   │   ├── llm.py               # OpenAI client with rate-limit exponential backoff
│   │   ├── triage.py            # Core TicketTriage engine
│   │   └── test_triage.py       # Task 1 standalone verification tests
│   └── task2/
│       ├── schemas.py           # Pydantic schemas (TAMBrief, OpenRiskItem)
│       ├── data_loader.py       # Deterministic account & 90-day ticket query engine
│       ├── prompts.py           # 3-section brief synthesis prompts
│       ├── summarizer.py        # TAMSummarizer engine with self-healing JSON retry
│       └── test_tam.py          # Task 2 standalone verification tests
├── .env.example                 # Template for required environment variables
├── .github/workflows/eval.yml   # GitHub Actions CI workflow (Bonus)
├── DESIGN_NOTE.md               # Task 4 Design Note (~600 words)
├── PROMPT_CHANGELOG.md          # Prompt versioning and changelog (Bonus)
├── README.md                    # Main documentation
└── requirements.txt             # Project dependencies
```
