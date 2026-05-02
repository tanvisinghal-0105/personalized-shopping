import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from google.cloud import firestore
import os
import sys
import json
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()

logger.info("Initializing Firestore client")
db = firestore.Client()

# Define the path to the static directory
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route to serve index.html from the root
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Optional: return a 404 or a simple message if index.html is missing
        return fastapi.Response(content="index.html not found", status_code=404)


@app.put("/api/v1/approvals/{customer_id}")
async def update_approval(customer_id: str):
    logger.info(f"Received PUT request for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({
                "approval_status": "approved"
            })
            logger.info(f"Successfully updated approval status for customer ID: {customer_id}")
            return {"customer_id": customer_id}
        except Exception as e:
            logger.error(f"Error updating Firestore for customer ID {customer_id}: {e}")
            raise fastapi.HTTPException(status_code=500, detail="Internal server error during update")
    else:
        logger.warning(f"Customer ID not found during PUT request: {customer_id}")
        # Return a proper FastAPI HTTP exception for not found
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")

@app.get("/api/v1/approvals/{customer_id}")
async def get_approval(customer_id: str):
    logger.info(f"Received GET request for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        logger.info(f"Found customer ID: {customer_id}")
        return document.to_dict()
    else:
        logger.warning(f"Customer ID not found during GET request: {customer_id}")
        # Return a proper FastAPI HTTP exception for not found
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")


# 
# Add a route to reset the cart info with the DEFAULT CART INFO
@app.post("/api/v1/reset_cart/{customer_id}")
async def reset_cart(customer_id: str):
    CUSTOMER_CART_INFO = {
            'cart_id': 'CART-112233', # Use example ID for consistency
            'items': {
                'GENERIC-PIXEL-CASE': {'sku': '1122334', 'name': 'Generic Google Pixel Case', 'quantity': 1, 'price': 19} },
            'subtotal': 19,
            'last_updated': '2025-04-23 11:05:00' # Use example timestamp
    }

    logger.info(f"Setting up mock cart info for customer ID: {customer_id}...")
    db.collection('carts').document(customer_id).set(CUSTOMER_CART_INFO)
    logger.info(f"Mock cart info set up for customer ID: {customer_id}")
    return {"status": "success", "customer_id": customer_id, "cart_reset": True}


# Add a route to reset approval status back to pending
@app.post("/api/v1/reset_approval/{customer_id}")
async def reset_approval_status(customer_id: str):
    logger.info(f"Received POST request to reset approval status for customer ID: {customer_id}")
    document = db.collection('customers').document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({
                "approval_status": "pending"
            })
            logger.info(f"Successfully reset approval status to pending for customer ID: {customer_id}")
            return {"status": "success", "customer_id": customer_id, "approval_status": "pending"}
        except Exception as e:
            logger.error(f"Error resetting approval status for customer ID {customer_id}: {e}")
            raise fastapi.HTTPException(status_code=500, detail="Internal server error during approval status reset")
    else:
        logger.warning(f"Customer ID not found during reset approval request: {customer_id}")
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")


# ================================================================== #
#  Evaluation API endpoints
# ================================================================== #

EVAL_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "server", "evaluation", "logs")

# Add server dir to path so we can import the evaluation module
_server_dir = os.path.join(os.path.dirname(__file__), "..", "..", "server")
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)


@app.get("/api/v1/eval/sessions")
async def list_eval_sessions():
    """List all recorded evaluation sessions."""
    files = sorted(glob.glob(os.path.join(EVAL_LOG_DIR, "session_*.json")), reverse=True)
    files = [f for f in files if "_eval_results" not in f]
    sessions = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            results_file = f.replace(".json", "_eval_results.json")
            has_results = os.path.exists(results_file)
            sessions.append({
                "file": os.path.basename(f),
                "session_id": data.get("session_id"),
                "customer_id": data.get("customer_id"),
                "start_time": data.get("start_time"),
                "duration_seconds": data.get("duration_seconds"),
                "turn_count": data.get("turn_count"),
                "tool_call_count": data.get("tool_call_count"),
                "has_eval_results": has_results,
            })
        except Exception:
            pass
    return {"sessions": sessions}


@app.post("/api/v1/eval/run/{filename}")
async def run_evaluation(filename: str, use_vertex: bool = True):
    """Run evaluation on a specific session log."""
    filepath = os.path.join(EVAL_LOG_DIR, filename)
    if not os.path.exists(filepath):
        raise fastapi.HTTPException(status_code=404, detail="Session file not found")

    try:
        from evaluation.run_eval import evaluate_session
        results = evaluate_session(filepath, use_vertex=use_vertex)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/eval/results/{filename}")
async def get_eval_results(filename: str):
    """Get evaluation results for a session."""
    results_file = os.path.join(EVAL_LOG_DIR, filename.replace(".json", "_eval_results.json"))
    if not os.path.exists(results_file):
        raise fastapi.HTTPException(status_code=404, detail="Evaluation results not found. Run evaluation first.")
    with open(results_file) as f:
        return json.load(f)


@app.get("/eval", response_class=HTMLResponse)
async def eval_dashboard():
    """Serve the evaluation dashboard UI."""
    return HTMLResponse(content=EVAL_DASHBOARD_HTML)


EVAL_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OTTO Agent Evaluation Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', -apple-system, sans-serif; background: #0a0b14; color: #e4e4f0; min-height: 100vh; padding: 24px; }
  h1 { font-size: 24px; margin-bottom: 8px; }
  .subtitle { color: #8888a8; font-size: 14px; margin-bottom: 24px; }
  .sessions-grid { display: grid; gap: 16px; }
  .session-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px; }
  .session-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .session-id { font-weight: 600; font-size: 14px; color: #00f0ff; }
  .session-meta { display: flex; gap: 16px; font-size: 13px; color: #8888a8; margin-bottom: 16px; }
  .btn { padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
  .btn-primary { background: linear-gradient(135deg, #a855f7, #00f0ff); color: #0a0b14; }
  .btn-primary:hover { opacity: 0.9; }
  .btn-secondary { background: rgba(255,255,255,0.08); color: #e4e4f0; border: 1px solid rgba(255,255,255,0.15); }
  .btn-secondary:hover { background: rgba(255,255,255,0.12); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .results-panel { margin-top: 16px; display: none; }
  .results-panel.open { display: block; }
  .score-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 12px; }
  .score-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px; }
  .score-label { font-size: 12px; color: #8888a8; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
  .score-value { font-size: 28px; font-weight: 700; }
  .score-good { color: #22c55e; }
  .score-ok { color: #f59e0b; }
  .score-bad { color: #ef4444; }
  .grade-badge { font-size: 32px; font-weight: 800; padding: 4px 16px; border-radius: 8px; }
  .grade-A { background: rgba(34,197,94,0.15); color: #22c55e; }
  .grade-B { background: rgba(34,197,94,0.1); color: #86efac; }
  .grade-C { background: rgba(245,158,11,0.15); color: #f59e0b; }
  .grade-D { background: rgba(239,68,68,0.1); color: #fca5a5; }
  .grade-F { background: rgba(239,68,68,0.15); color: #ef4444; }
  .detail-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 13px; }
  .detail-key { color: #8888a8; }
  .skipped { color: #ef4444; font-size: 12px; margin-top: 4px; }
  .empty-state { text-align: center; padding: 60px 20px; color: #555570; }
  .loading { color: #00f0ff; font-size: 13px; }
  .actions { display: flex; gap: 8px; }
</style>
</head>
<body>
<h1>OTTO Agent Evaluation</h1>
<p class="subtitle">Voice Shopping Assistant - Session Quality Analysis</p>

<div id="content">
  <div class="empty-state">Loading sessions...</div>
</div>

<script>
const API = '';

async function loadSessions() {
  const res = await fetch(`${API}/api/v1/eval/sessions`);
  const data = await res.json();
  const container = document.getElementById('content');

  if (!data.sessions || data.sessions.length === 0) {
    container.innerHTML = '<div class="empty-state"><h2>No sessions recorded yet</h2><p>Run the demo to generate session logs for evaluation.</p></div>';
    return;
  }

  container.innerHTML = '<div class="sessions-grid" id="sessionsGrid"></div>';
  const grid = document.getElementById('sessionsGrid');

  data.sessions.forEach(s => {
    const card = document.createElement('div');
    card.className = 'session-card';
    card.id = `card-${s.file}`;
    card.innerHTML = `
      <div class="session-header">
        <span class="session-id">${s.session_id || 'Unknown'}</span>
        <span style="font-size:12px;color:#555570;">${s.start_time || ''}</span>
      </div>
      <div class="session-meta">
        <span>Customer: ${s.customer_id || 'N/A'}</span>
        <span>Duration: ${s.duration_seconds || 0}s</span>
        <span>Turns: ${s.turn_count || 0}</span>
        <span>Tool Calls: ${s.tool_call_count || 0}</span>
      </div>
      <div class="actions">
        <button class="btn btn-primary" onclick="runEval('${s.file}', true)">Evaluate (Vertex AI + Custom)</button>
        <button class="btn btn-secondary" onclick="runEval('${s.file}', false)">Evaluate (Custom Metrics Only)</button>
        ${s.has_eval_results ? '<button class="btn btn-secondary" onclick="viewResults(\\'' + s.file + '\\')">View Results</button>' : ''}
      </div>
      <div class="results-panel" id="results-${s.file}"></div>
    `;
    grid.appendChild(card);
  });
}

async function runEval(filename, useVertex) {
  const panel = document.getElementById(`results-${filename}`);
  panel.className = 'results-panel open';
  panel.innerHTML = '<p class="loading">Running evaluation... This may take a minute.</p>';

  try {
    const res = await fetch(`${API}/api/v1/eval/run/${filename}?use_vertex=${useVertex}`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      renderResults(panel, data.results);
    } else {
      panel.innerHTML = `<p style="color:#ef4444;">Error: ${data.detail || 'Unknown error'}</p>`;
    }
  } catch (e) {
    panel.innerHTML = `<p style="color:#ef4444;">Error: ${e.message}</p>`;
  }
}

async function viewResults(filename) {
  const panel = document.getElementById(`results-${filename}`);
  panel.className = 'results-panel open';
  panel.innerHTML = '<p class="loading">Loading results...</p>';

  try {
    const res = await fetch(`${API}/api/v1/eval/results/${filename}`);
    const data = await res.json();
    renderResults(panel, data);
  } catch (e) {
    panel.innerHTML = `<p style="color:#ef4444;">Error: ${e.message}</p>`;
  }
}

function renderResults(panel, results) {
  const overall = results.overall || {};
  const grade = overall.grade || '?';
  const score = overall.score || 0;
  const scoreClass = score >= 0.8 ? 'score-good' : score >= 0.6 ? 'score-ok' : 'score-bad';

  let html = `
    <div style="display:flex;align-items:center;gap:16px;margin:16px 0;">
      <span class="grade-badge grade-${grade}">${grade}</span>
      <div>
        <div class="score-value ${scoreClass}">${(score * 100).toFixed(1)}%</div>
        <div style="font-size:12px;color:#8888a8;">Overall Score</div>
      </div>
    </div>
    <div class="score-grid">
  `;

  const layers = [
    { key: 'trajectory_order', label: 'Trajectory Order', scoreKey: 'trajectory_order_score' },
    { key: 'trajectory_args', label: 'Trajectory Args', scoreKey: 'trajectory_args_score' },
    { key: 'step_skip', label: 'Step Completion', scoreKey: 'step_skip_score' },
    { key: 'moodboard_quality', label: 'Moodboard Quality', scoreKey: 'moodboard_quality_score' },
    { key: 'session_completion', label: 'Task Completion', scoreKey: 'session_completion_score' },
    { key: 'speech_latency', label: 'Speech Latency', scoreKey: 'speech_latency_score' },
    { key: 'speech_wer', label: 'Transcription (WER)', scoreKey: 'speech_wer_score' },
  ];

  layers.forEach(l => {
    const layer = results[l.key] || {};
    const val = layer[l.scoreKey];
    if (val === undefined) return;
    const cls = val >= 0.8 ? 'score-good' : val >= 0.6 ? 'score-ok' : 'score-bad';
    html += `<div class="score-card"><div class="score-label">${l.label}</div><div class="score-value ${cls}">${(val * 100).toFixed(0)}%</div>`;

    // Show extra details
    Object.entries(layer).forEach(([k, v]) => {
      if (k !== l.scoreKey && !Array.isArray(v)) {
        html += `<div class="detail-row"><span class="detail-key">${k}</span><span>${typeof v === 'number' ? v.toFixed ? v.toFixed(2) : v : v}</span></div>`;
      }
    });

    // Show skipped stages if any
    if (layer.skipped_stages && layer.skipped_stages.length > 0) {
      html += `<div class="skipped">Skipped: ${layer.skipped_stages.join(', ')}</div>`;
    }
    html += '</div>';
  });

  // Vertex AI conversation results
  if (results.vertex_conversation && !results.vertex_conversation.error) {
    html += '<div class="score-card" style="grid-column:1/-1;"><div class="score-label">Vertex AI Conversation Quality</div>';
    Object.entries(results.vertex_conversation).forEach(([k, v]) => {
      if (typeof v === 'number') {
        const cls = v >= 4 ? 'score-good' : v >= 3 ? 'score-ok' : 'score-bad';
        html += `<div class="detail-row"><span class="detail-key">${k}</span><span class="${cls}">${v.toFixed(2)}</span></div>`;
      }
    });
    html += '</div>';
  }

  html += '</div>';
  panel.innerHTML = html;
}

loadSessions();
</script>
</body>
</html>
"""
