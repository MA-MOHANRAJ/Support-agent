import streamlit as st
import json
from pathlib import Path
from src.task1.triage import triage_ticket
from src.task2.summarizer import generate_tam_brief
from src.task2.data_loader import AccountDataLoader

st.set_page_config(
    page_title="Support AI & TAM Intelligence Platform",
    page_icon="⚡",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #64748B; margin-bottom: 1.5rem; }
    .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
    .badge-p1 { background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-p2 { background-color: #FFEDD5; color: #9A3412; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-p3 { background-color: #FEF3C7; color: #92400E; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-p4 { background-color: #E0E7FF; color: #3730A3; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ Support AI & TAM Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Production-grade AI Tooling for Technical Support Engineers & Technical Account Managers</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🎫 Task 1: Intelligent Ticket Triage", "📊 Task 2: TAM QBR Account Health Brief"])

# ==============================================================================
# TAB 1: TICKET TRIAGE
# ==============================================================================
with tab1:
    st.subheader("Autonomous Support Ticket Ingestion & Triage")
    st.caption("Classifies incoming raw support tickets without human labelling, retrieves relevant KB docs, and drafts first response.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Input Ticket")
        sample_choice = st.selectbox(
            "Select Sample Ticket or Enter Custom Text:",
            [
                "Custom Ticket Text",
                "Sample 1: P1 Outage (SecureVault Key Management Down)",
                "Sample 2: Integration Issue (CloudSync SSO Failure)",
                "Sample 3: Performance (DataBridge Pro Connection Pool)",
                "Sample 4: How-To (WorkflowEngine Automated Triggers)"
            ]
        )

        default_text = ""
        if sample_choice == "Sample 1: P1 Outage (SecureVault Key Management Down)":
            default_text = "URGENT: SecureVault Key Management is completely down in our production environment. None of our microservices can decrypt API tokens and our entire customer-facing checkout flow is failing with 500 errors. We need immediate P1 escalation!"
        elif sample_choice == "Sample 2: Integration Issue (CloudSync SSO Failure)":
            default_text = "SSO configuration not working for new users — CloudSync\n\nExisting users can log in fine via Okta SSO, but all newly added employees receive an error when attempting to authenticate in CloudSync. We need guidance on how to fix this for our team."
        elif sample_choice == "Sample 3: Performance (DataBridge Pro Connection Pool)":
            default_text = "Our batch ingestion pipelines in DataBridge Pro are experiencing severe latency spikes and database connection pool exhaustion under 200 concurrent user load."
        elif sample_choice == "Sample 4: How-To (WorkflowEngine Automated Triggers)":
            default_text = "How do I configure cron-based automated schedule triggers for data export workflows in WorkflowEngine?"

        ticket_input = st.text_area("Ticket Content (Subject & Body):", value=default_text, height=220)

        if st.button("🚀 Run Intelligent Triage", type="primary", use_container_width=True):
            if not ticket_input.strip():
                st.warning("Please enter ticket text to triage.")
            else:
                with st.spinner("Triaging ticket and retrieving knowledge base context..."):
                    try:
                        result = triage_ticket(ticket_input)
                        st.session_state["triage_result"] = result
                    except Exception as e:
                        st.error(f"Triage error: {e}")

    with col2:
        st.markdown("#### Triage Assessment Output")
        if "triage_result" in st.session_state:
            res = st.session_state["triage_result"]
            
            badge_class = f"badge-{res.urgency.lower()}"
            st.markdown(f"**Urgency Tier**: <span class='{badge_class}'>{res.urgency}</span> | **Category**: `{res.category}` | **Product**: `{res.product or 'Inferred'}` (`{res.product_area}`)", unsafe_allow_html=True)
            st.markdown(f"**Recommended Team**: `{res.recommended_team}`")
            
            st.info(f"**Triage Reasoning:**\n{res.reasoning}")

            if res.known_issue and res.knowledge_base_source:
                st.success(f"📚 **Known KB Match Found**: `{res.knowledge_base_source}`")
            else:
                st.warning("ℹ️ **Knowledge Base**: No exact known issue match found (fallback diagnostic mode).")

            st.markdown("#### Draft First-Response Message")
            st.text_area("Agent Response Draft:", value=res.draft_response, height=220)
        else:
            st.info("Run triage on the left to view the structured classification, RAG citation, and drafted response.")

# ==============================================================================
# TAB 2: TAM ACCOUNT HEALTH BRIEF
# ==============================================================================
with tab2:
    st.subheader("TAM QBR Account Health Brief Synthesizer")
    st.caption("Aggregates customer account metadata and last 90 days of tickets to produce a deterministic 3-section QBR brief with direct quote justifications.")

    loader = AccountDataLoader()
    account_ids = sorted(list(loader._accounts.keys()))

    col_acc1, col_acc2 = st.columns([1, 1])
    with col_acc1:
        selected_acc = st.selectbox("Option A: Choose from Preset Accounts:", account_ids, index=account_ids.index("ACC-3336") if "ACC-3336" in account_ids else 0)
    with col_acc2:
        manual_acc = st.text_input("Option B: Enter Custom Account ID:", value=selected_acc, placeholder="e.g. ACC-3336, ACC-4654, ACC-9999")

    target_acc = manual_acc.strip() if manual_acc.strip() else selected_acc
    gen_btn = st.button("📊 Generate Brief", type="primary", use_container_width=True)

    if gen_btn or "tam_brief" in st.session_state:
        with st.spinner(f"Synthesizing QBR Account Brief for {target_acc}..."):
            try:
                brief = generate_tam_brief(target_acc)
                st.session_state["tam_brief"] = brief

                # Top Metrics KPIs
                kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
                kpi1.metric("Company", brief.company)
                kpi2.metric("Health Status", brief.health_status)
                kpi3.metric("Annual Recurring Revenue", f"${brief.arr_usd:,.0f}")
                kpi4.metric("Seat Utilization", f"{brief.seat_utilization_pct}%")
                kpi5.metric("90d Support Tickets", brief.total_tickets_last_90d)

                st.markdown("---")

                # Section 1
                st.markdown("### 1. Executive Summary")
                st.info(brief.executive_summary)

                # Section 2
                st.markdown(f"### 2. Open Risks & Flagged Issues ({len(brief.open_risks)} Identified)")
                if not brief.open_risks:
                    st.write("No critical risk signals identified for this account.")
                for r in brief.open_risks:
                    t_str = f"Ticket: `{r.ticket_id}`" if r.ticket_id else "Account-Level"
                    severity_color = "🔴" if r.severity in ["Critical", "High"] else "🟡"
                    with st.expander(f"{severity_color} {r.risk_type} ({r.severity} Severity) — {t_str}", expanded=True):
                        st.markdown(f"**Reason:** {r.reason}")
                        st.markdown(f"**Direct Verbatim Evidence Quote:**")
                        st.code(r.evidence_quote, language="text")

                # Section 3
                st.markdown("### 3. Recommended Talking Points for TAM")
                for idx, pt in enumerate(brief.talking_points, start=1):
                    st.markdown(f"**{idx}.** {pt}")

            except Exception as e:
                st.error(f"Failed to generate TAM brief: {e}")
