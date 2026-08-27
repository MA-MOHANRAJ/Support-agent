import os
from typing import Dict, Any, Union, Optional
from fastapi import FastAPI, HTTPException, Body, Path
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.task1.schemas import TriageResult as Task1TriageResult
from src.task1.triage import triage_ticket
from src.task2.schemas import TAMBrief, TAMBriefRequest
from src.task2.summarizer import generate_tam_brief

app = FastAPI(
    title="Support Intelligence & TAM Platform API",
    description="Production-grade AI tooling for Technical Support Triage (Task 1) and TAM Account Health Synthesis (Task 2).",
    version="1.0.0"
)


class TicketTriageRequest(BaseModel):
    ticket_text: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    product: Optional[str] = None
    product_area: Optional[str] = None
    company: Optional[str] = None
    plan_tier: Optional[str] = None


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def web_ui():
    """
    Interactive Web Dashboard for Technical Support Engineers & TAMs.
    Allows testing Task 1 (Ticket Triage) and Task 2 (TAM QBR Briefs with dropdown & manual entry) directly in the browser.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Support AI & TAM Intelligence Platform</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --bg: #f8fafc;
      --surface: #ffffff;
      --text: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --radius: 10px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 32px 20px; line-height: 1.5; }
    .container { max-width: 1100px; margin: 0 auto; }
    .header { margin-bottom: 24px; }
    .header h1 { font-size: 28px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 10px; }
    .header p { color: var(--text-muted); font-size: 15px; margin-top: 4px; }
    .tabs { display: flex; gap: 8px; border-bottom: 2px solid var(--border); margin-bottom: 24px; }
    .tab-btn { padding: 12px 20px; background: none; border: none; font-size: 15px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
    .tab-btn.active { color: var(--primary); border-bottom-color: var(--primary); }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .card h3 { font-size: 17px; margin-bottom: 14px; font-weight: 600; }
    label { display: block; font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 6px; }
    select, textarea, input { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 14px; margin-bottom: 14px; outline: none; }
    select:focus, textarea:focus, input:focus { border-color: var(--primary); }
    textarea { height: 160px; resize: vertical; }
    button.btn { background: var(--primary); color: #fff; border: none; padding: 12px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; width: 100%; font-size: 14px; transition: background 0.2s; }
    button.btn:hover { background: var(--primary-dark); }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .badge-p1 { background: #fee2e2; color: #991b1b; }
    .badge-p2 { background: #ffedd5; color: #9a3412; }
    .badge-p3 { background: #fef3c7; color: #92400e; }
    .badge-p4 { background: #e0e7ff; color: #3730a3; }
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }
    .metric-box { background: #f1f5f9; padding: 12px; border-radius: 8px; text-align: center; }
    .metric-box .val { font-size: 18px; font-weight: 700; color: #0f172a; }
    .metric-box .lbl { font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }
    .risk-item { background: #fff1f2; border-left: 4px solid #e11d48; padding: 12px; border-radius: 4px; margin-bottom: 10px; font-size: 13px; }
    .risk-item .title { font-weight: 700; color: #9f1239; margin-bottom: 4px; }
    .risk-item .quote { background: #ffe4e6; padding: 6px 10px; border-radius: 4px; font-style: italic; margin-top: 6px; color: #881337; }
    .point-item { padding: 8px 12px; background: #f8fafc; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 8px; font-size: 13px; }
    .loader { display: none; text-align: center; padding: 20px; color: var(--primary); font-weight: 600; }
    .err-box { display: none; background: #fee2e2; border: 1px solid #f87171; color: #991b1b; padding: 12px; border-radius: 6px; margin-bottom: 14px; font-size: 13px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⚡ Support AI & TAM Intelligence Platform</h1>
      <p>Production-grade AI tooling for Technical Support Engineers & Technical Account Managers</p>
    </div>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('tab1')">🎫 Task 1: Ticket Triage</button>
      <button class="tab-btn" onclick="switchTab('tab2')">📊 Task 2: TAM QBR Account Brief</button>
    </div>

    <!-- TAB 1: TICKET TRIAGE -->
    <div id="tab1" class="tab-content active">
      <div class="grid-2">
        <div class="card">
          <h3>Input Support Ticket</h3>
          <label>Choose Preset Sample:</label>
          <select id="triagePreset" onchange="loadPreset()">
            <option value="custom">-- Custom Ticket Input --</option>
            <option value="p1">Sample 1: P1 Outage (SecureVault Key Mgmt Down)</option>
            <option value="sso">Sample 2: Integration / SSO Issue (CloudSync)</option>
            <option value="howto">Sample 3: Routine How-To (WorkflowEngine Cron)</option>
            <option value="perf">Sample 4: Performance Latency (DataBridge Pro)</option>
          </select>

          <label>Ticket Content (Free-Text or Subject + Body):</label>
          <textarea id="triageInput" placeholder="Paste incoming support ticket text here...">URGENT: SecureVault Key Management is completely down in our production environment. None of our microservices can decrypt API tokens and our entire customer-facing checkout flow is failing with 500 errors. We need immediate P1 escalation!</textarea>
          <button class="btn" onclick="runTriage()">🚀 Run Intelligent Triage</button>
        </div>

        <div class="card">
          <h3>Triage Assessment</h3>
          <div id="triageErr" class="err-box"></div>
          <div id="triageLoader" class="loader">Triaging ticket & retrieving knowledge base...</div>
          <div id="triageEmpty" style="color: var(--text-muted); font-size: 14px;">Click 'Run Intelligent Triage' to view structured classification, RAG citations, and draft response.</div>
          <div id="triageResult" style="display: none;">
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px;">
              <span id="resUrgency" class="badge badge-p1">P1</span>
              <span id="resCategory" style="font-weight: 600; font-size: 14px;">Category</span>
              <span id="resProduct" style="color: var(--text-muted); font-size: 13px;">Product</span>
            </div>
            <div style="font-size: 13px; margin-bottom: 10px;"><strong>Routing:</strong> <span id="resTeam">Tier 1</span></div>
            <div style="font-size: 13px; margin-bottom: 10px;"><strong>Reasoning:</strong> <span id="resReasoning">...</span></div>
            <div id="resKbBox" style="font-size: 12px; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px; border-radius: 6px; margin-bottom: 12px; color: #166534;"></div>
            <label>Draft First-Response Message:</label>
            <textarea id="resDraft" style="height: 140px; font-size: 13px;" readonly></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: TAM BRIEF -->
    <div id="tab2" class="tab-content">
      <div class="card" style="margin-bottom: 20px;">
        <h3>Generate TAM Account Health Brief</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px;">
          <div>
            <label>Option A: Choose from Preset Accounts</label>
            <select id="accSelect" onchange="document.getElementById('accManual').value = this.value">
              <option value="ACC-3336">ACC-3336 — Omni Consumer Products ($500k ARR, At Risk)</option>
              <option value="ACC-3033">ACC-3033 — Polaris Group ($120k ARR, Healthy)</option>
              <option value="ACC-4654">ACC-4654 — Initech ($96k ARR, Healthy)</option>
              <option value="ACC-7893">ACC-7893 — Solaris Data ($24k ARR, New)</option>
              <option value="ACC-4610">ACC-4610 — Zymurgy Systems ($250k ARR, Healthy)</option>
            </select>
          </div>
          <div>
            <label>Option B: Enter Any Account ID Manually</label>
            <input type="text" id="accManual" value="ACC-3336" placeholder="e.g. ACC-3336, ACC-4654, ACC-9999" />
          </div>
        </div>
        <button class="btn" style="max-width: 250px;" onclick="runTAMBrief()">📊 Generate QBR Brief</button>
      </div>

      <div id="tamErr" class="err-box"></div>
      <div id="tamLoader" class="loader">Synthesizing 90-day ticket history & account records...</div>
      
      <div id="tamResult" style="display: none;">
        <div class="metric-grid">
          <div class="metric-box"><div class="lbl">Company</div><div class="val" id="mCompany">-</div></div>
          <div class="metric-box"><div class="lbl">Health Status</div><div class="val" id="mHealth">-</div></div>
          <div class="metric-box"><div class="lbl">ARR</div><div class="val" id="mArr">-</div></div>
          <div class="metric-box"><div class="lbl">Seat Utilization</div><div class="val" id="mSeats">-</div></div>
        </div>

        <div class="card" style="margin-bottom: 16px;">
          <h3>1. Executive Summary</h3>
          <p id="bSummary" style="font-size: 14px; color: #1e293b;"></p>
        </div>

        <div class="card" style="margin-bottom: 16px;">
          <h3>2. Open Risks & Flagged Issues (<span id="bRiskCount">0</span> Detected)</h3>
          <div id="bRisksContainer"></div>
        </div>

        <div class="card">
          <h3>3. Recommended Talking Points for TAM</h3>
          <div id="bPointsContainer"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    function loadPreset() {
      const v = document.getElementById('triagePreset').value;
      const t = document.getElementById('triageInput');
      if (v === 'p1') {
        t.value = "URGENT: SecureVault Key Management is completely down in our production environment. None of our microservices can decrypt API tokens and our entire customer-facing checkout flow is failing with 500 errors. We need immediate P1 escalation!";
      } else if (v === 'sso') {
        t.value = "SSO configuration not working for new users — CloudSync\\n\\nExisting users can log in fine via Okta SSO, but all newly added employees receive an error when attempting to authenticate in CloudSync. We need guidance on how to fix this for our team.";
      } else if (v === 'howto') {
        t.value = "How do I configure cron-based automated schedule triggers for data export workflows in WorkflowEngine?";
      } else if (v === 'perf') {
        t.value = "Our batch ingestion pipelines in DataBridge Pro are experiencing severe latency spikes and database connection pool exhaustion under 200 concurrent user load.";
      }
    }

    async function runTriage() {
      const text = document.getElementById('triageInput').value;
      const errBox = document.getElementById('triageErr');
      errBox.style.display = 'none';
      document.getElementById('triageLoader').style.display = 'block';
      document.getElementById('triageEmpty').style.display = 'none';
      document.getElementById('triageResult').style.display = 'none';

      try {
        const res = await fetch('/api/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticket_text: text })
        });
        const data = await res.json();
        document.getElementById('triageLoader').style.display = 'none';

        if (!res.ok) {
          errBox.textContent = data.detail || 'Triage request failed.';
          errBox.style.display = 'block';
          return;
        }

        document.getElementById('triageResult').style.display = 'block';

        const urg = document.getElementById('resUrgency');
        urg.textContent = data.urgency;
        urg.className = 'badge badge-' + data.urgency.toLowerCase();

        document.getElementById('resCategory').textContent = data.category;
        document.getElementById('resProduct').textContent = (data.product || 'Inferred') + ' (' + data.product_area + ')';
        document.getElementById('resTeam').textContent = data.recommended_team;
        document.getElementById('resReasoning').textContent = data.reasoning;
        document.getElementById('resDraft').value = data.draft_response;

        const kb = document.getElementById('resKbBox');
        if (data.known_issue && data.knowledge_base_source) {
          kb.style.display = 'block';
          kb.innerHTML = '📚 <strong>Grounded KB Doc:</strong> ' + data.knowledge_base_source;
        } else {
          kb.style.display = 'none';
        }
      } catch (err) {
        document.getElementById('triageLoader').style.display = 'none';
        errBox.textContent = 'Network/Server Error: ' + err.message;
        errBox.style.display = 'block';
      }
    }

    async function runTAMBrief() {
      const accId = document.getElementById('accManual').value.trim() || document.getElementById('accSelect').value;
      const errBox = document.getElementById('tamErr');
      errBox.style.display = 'none';
      document.getElementById('tamLoader').style.display = 'block';
      document.getElementById('tamResult').style.display = 'none';

      try {
        const res = await fetch('/api/tam/brief/' + encodeURIComponent(accId));
        const data = await res.json();
        document.getElementById('tamLoader').style.display = 'none';

        if (!res.ok) {
          errBox.textContent = data.detail || `Account '${accId}' not found or error generating brief.`;
          errBox.style.display = 'block';
          return;
        }

        document.getElementById('tamResult').style.display = 'block';

        document.getElementById('mCompany').textContent = data.company;
        document.getElementById('mHealth').textContent = data.health_status;
        document.getElementById('mArr').textContent = '$' + Number(data.arr_usd).toLocaleString();
        document.getElementById('mSeats').textContent = data.seat_utilization_pct + '%';
        document.getElementById('bSummary').textContent = data.executive_summary;
        document.getElementById('bRiskCount').textContent = data.open_risks.length;

        const rCont = document.getElementById('bRisksContainer');
        rCont.innerHTML = '';
        if (data.open_risks.length === 0) {
          rCont.innerHTML = '<div style="color: var(--text-muted); font-size: 13px;">No critical risks detected for this account.</div>';
        } else {
          data.open_risks.forEach(r => {
            const div = document.createElement('div');
            div.className = 'risk-item';
            div.innerHTML = '<div class="title">' + r.risk_type + ' (' + r.severity + ' Severity)' + (r.ticket_id ? ' — Ticket: ' + r.ticket_id : ' — Account-Level') + '</div>' +
                            '<div>' + r.reason + '</div>' +
                            '<div class="quote">"' + r.evidence_quote + '"</div>';
            rCont.appendChild(div);
          });
        }

        const pCont = document.getElementById('bPointsContainer');
        pCont.innerHTML = '';
        data.talking_points.forEach((pt, idx) => {
          const div = document.createElement('div');
          div.className = 'point-item';
          div.innerHTML = '<strong>' + (idx + 1) + '.</strong> ' + pt;
          pCont.appendChild(div);
        });
      } catch (err) {
        document.getElementById('tamLoader').style.display = 'none';
        errBox.textContent = 'Network/Server Error: ' + err.message;
        errBox.style.display = 'block';
      }
    }
  </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


# ==============================================================================
# TASK 1: Intelligent Ticket Triage Endpoint
# ==============================================================================
@app.post("/api/triage", response_model=Task1TriageResult, tags=["Task 1 - Triage"])
def triage_endpoint(payload: Union[TicketTriageRequest, Dict[str, Any], str] = Body(...)):
    """
    Intelligent Ticket Triage Endpoint (Task 1).
    """
    try:
        if isinstance(payload, TicketTriageRequest):
            data = payload.model_dump(exclude_none=True)
        else:
            data = payload

        return triage_ticket(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage processing error: {str(e)}")


# ==============================================================================
# TASK 2: TAM Account Health Summariser Endpoints
# ==============================================================================
@app.post("/api/tam/brief", response_model=TAMBrief, tags=["Task 2 - TAM Brief"])
def generate_tam_brief_post(req: TAMBriefRequest):
    """
    Generate TAM Account Brief via POST (Task 2).
    """
    try:
        return generate_tam_brief(req.account_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TAM Brief generation error: {str(e)}")


@app.get("/api/tam/brief/{account_id}", response_model=TAMBrief, tags=["Task 2 - TAM Brief"])
def generate_tam_brief_get(account_id: str = Path(..., description="Target Account ID (e.g. ACC-3336)")):
    """
    Generate TAM Account Brief via GET (Task 2).
    """
    try:
        return generate_tam_brief(account_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TAM Brief generation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
