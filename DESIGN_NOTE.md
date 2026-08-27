# Technical Design Note: Production Support & TAM Intelligence Platform

## 1. Top 3 Production Failure Modes, Detection & Mitigation

### Failure Mode 1: Knowledge Base Semantic Drift & False Match Citations
* **Mechanism**: In production, continuous product updates and fast-growing documentation can cause vector embeddings of unrelated articles to drift into high similarity territory with novel ticket symptoms. This could lead to triaging an issue as a `known_issue=true` with an irrelevant troubleshooting guide.
* **Detection**: 
  - Track **Retrieval Confidence Discrepancy**: Alert when FAISS cosine similarity is below a dynamic confidence threshold ($\tau < 0.72$) or when customer CSAT / first-contact resolution rates drop on automated responses.
  - LLM Self-Verification step comparing the retrieved text against ticket symptoms before assigning `known_issue=true`.
* **Mitigation**:
  - Enforce a strict fallback rule: if candidate similarity is marginal or the doc fails factual verification, automatically downgrade to `known_issue=false` and request targeted diagnostic logs rather than offering ungrounded steps.
  - Automated weekly knowledge-base regression evals using synthetic benchmark tickets.

### Failure Mode 2: Multi-Turn Hallucination of Customer Data / Escalation Risks in TAM Briefs
* **Mechanism**: When synthesizing unstructured account notes, the model could hallucinate competitor names, pricing discounts, or exaggerated outage statistics not present in the dataset.
* **Detection**:
  - **Automated Verbatim Quotation Checking**: Programmatically verify that every `evidence_quote` in the generated brief is a strict character substring of either `accounts.json` or `tickets.json`. If a quote fails substring containment, reject the output.
* **Mitigation**:
  - Implement deterministic rule-based preprocessing (as built in Task 2) to extract candidate quotes and risk flags *before* LLM prompting.
  - Use deterministic sampling (`temperature=0.0`, fixed seed, structured JSON schema).

### Failure Mode 3: Provider API Rate Limits, Token Throttling & Outages
* **Mechanism**: Sudden ticket spikes or daily token allocation exhaustion (e.g. HTTP 429 RateLimitError) can cause pipeline failures.
* **Detection**:
  - Real-time latency & error tracking middleware measuring 429/5xx rates on outgoing LLM client calls.
* **Mitigation**:
  - Implement exponential backoff retry loops with jitter in `LLMClient`.
  - Maintain an asynchronous multi-provider failover routing layer (e.g., primary Groq/OpenAI $\rightarrow$ backup Anthropic/Local vLLM).
  - Deterministic input prompt hashing & caching for identical query deduplication.

---

## 2. Latency vs. Quality Trade-Offs

* **Trade-Off Made**: We chose a **hybrid deterministic RAG + two-stage validation pipeline** (FAISS embedding retrieval $\rightarrow$ deterministic rule extraction $\rightarrow$ LLM generation $\rightarrow$ Pydantic schema validation $\rightarrow$ LLM-as-a-judge quality gate). This guarantees 100% grounded facts and strict P1–P4 taxonomy adherence at the cost of ~2.5–3.5s latency per ticket.
* **If Latency Were the Hard Constraint (<200ms)**:
  1. **Fine-Tuned Small Language Model (SLM)**: Replace the general LLM with an 8B/7B distilled model (or quantized ONNX model) fine-tuned exclusively on ticket taxonomy classification and routing.
  2. **Hierarchical Routing**: Use fast TF-IDF / BM25 classifier for immediate P4/How-To categorization in <15ms, reserving LLM inference strictly for ambiguous or P1/P2 outage tickets.
  3. **Speculative / Streaming Generation**: Stream draft responses directly to the support agent console using Server-Sent Events (SSE).

---

## 3. Data Sensitivity & PII Protection

* **Vulnerabilities**: Customer support tickets and account records frequently contain PII (names, emails, phone numbers, employee titles), API keys, and environment variables.
* **Architecture Controls**:
  1. **Pre-Inference Sanitization Layer**: Integrated regex / Microsoft Presidio PII anonymizer masking emails, JWT tokens, IP addresses, and phone numbers before payloads reach external LLM endpoints.
  2. **Zero Data Retention Agreements**: Ensure enterprise API endpoints operate under strict Zero Data Retention (ZDR) policies preventing model fine-tuning on customer telemetry.
  3. **Credential Guard Prompting**: For critical outages, system prompts explicitly instruct drafts: *"Please do not share secret keys, passwords, or credentials."*

---

## 4. Scaling to 10× Ticket Volume

* **Bottlenecks at 10× Load (5,000+ tickets/day)**:
  - **Synchronous API Gateways**: Synchronous HTTP request-response bottlenecks under burst loads.
  - **In-Memory Embedding Computation**: Real-time SentenceTransformer encoding causing CPU contention.
* **Scaling Strategy**:
  1. **Asynchronous Event-Driven Architecture**: Decouple ingestion via a message queue (Apache Kafka or Redis Streams). Webhooks push raw tickets onto a queue; a pool of worker nodes processes triage asynchronously.
  2. **Distributed Vector Index**: Migrate FAISS from in-memory index to managed vector infrastructure (e.g. Qdrant / Milvus / pgvector) with read-replicas.
  3. **Batching & Tiered LLM Routing**: Batch non-urgent P3/P4 tickets for periodic bulk summarisation while reserving low-latency provisioned throughput for P1 alerts.
