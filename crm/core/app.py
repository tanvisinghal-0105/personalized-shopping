import fastapi
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from google.cloud import firestore
import os
import sys
import json
import glob
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = fastapi.FastAPI()

# --- Authentication for CRM API endpoints ---
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "true").lower() == "true"
ALLOWED_DOMAINS = ["google.com"]


def _verify_id_token(token: str) -> dict:
    """Verify a Google ID token and return user info."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(token, request)
        email = id_info.get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""
        if domain not in ALLOWED_DOMAINS:
            return None
        return {"email": email, "name": id_info.get("name", "")}
    except Exception:
        return None


async def require_auth(request: fastapi.Request):
    """FastAPI dependency that requires a valid Google ID token."""
    if not AUTH_ENABLED:
        return {"email": "dev@google.com", "name": "Dev User"}

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user = _verify_id_token(token)
        if user:
            return user

    raise fastapi.HTTPException(status_code=401, detail="Authentication required")


logger.info("Initializing Firestore client")
db = firestore.Client()

PROJECT_ID = os.environ.get("PROJECT_ID", "")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", f"{PROJECT_ID}-shopping-assets")
GCS_ASSETS_BASE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/assets"
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")

# Define the path to the static directories
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
client_dir = os.path.join(os.path.dirname(__file__), "..", "..", "client")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
# Serve the main shopping UI assets (JS/CSS)
if os.path.isdir(os.path.join(client_dir, "src")):
    app.mount(
        "/src",
        StaticFiles(directory=os.path.join(client_dir, "src")),
        name="client_src",
    )

_allowed_origins = [
    "http://localhost:8082",
    "http://localhost:8080",
]
# Add Cloud Run and API Gateway origins from env vars
if os.environ.get("_HASH"):
    _allowed_origins.append(
        f"https://cymbal-frontend-{os.environ['_HASH']}-uc.a.run.app"
    )
if os.environ.get("_GW_HASH"):
    _allowed_origins.append(
        f"https://cymbal-stylesync-gateway-{os.environ['_GW_HASH']}.uc.gateway.dev"
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Page-level auth middleware (cookie-based) ---
# Paths that don't require auth (sign-in page, static assets, health checks)
_PUBLIC_PREFIXES = ("/login", "/static/", "/src/", "/favicon")


@app.middleware("http")
async def page_auth_middleware(request: fastapi.Request, call_next):
    path = request.url.path

    # Allow public paths
    if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return await call_next(request)

    # API endpoints use Bearer token auth via Depends(require_auth) -- skip here
    if path.startswith("/api/"):
        return await call_next(request)

    # For all other routes (pages), check the id_token cookie
    if AUTH_ENABLED:
        token = request.cookies.get("id_token")
        if not token or not _verify_id_token(token):
            from fastapi.responses import RedirectResponse

            redirect_to = request.url.path
            return RedirectResponse(url=f"/login?next={redirect_to}", status_code=302)

    return await call_next(request)


# --- Sign-in page ---
@app.get("/login", include_in_schema=False)
async def login_page(next: str = "/"):
    return HTMLResponse(
        content=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign In - Cymbal StyleSync</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',-apple-system,sans-serif; background:#0a0b14; color:#e4e4f0; min-height:100vh; display:flex; align-items:center; justify-content:center; }}
  .container {{ text-align:center; max-width:400px; padding:40px; }}
  .title {{ font-size:32px; font-weight:700; margin-bottom:8px; }}
  .subtitle {{ color:#8888a8; font-size:14px; margin-bottom:32px; }}
  .error {{ color:#ef4444; font-size:12px; display:none; margin-top:16px; }}
</style>
</head>
<body>
<div class="container">
    <div class="title">Cymbal StyleSync</div>
    <p class="subtitle">Sign in with your Google account to access the platform.</p>
    <div id="g_id_onload"
        data-client_id="{OAUTH_CLIENT_ID}"
        data-callback="handleSignIn"
        data-auto_prompt="false">
    </div>
    <div class="g_id_signin"
        data-type="standard"
        data-size="large"
        data-theme="filled_black"
        data-text="sign_in_with"
        data-shape="pill"
        data-logo_alignment="left"
        data-width="300">
    </div>
    <p id="signInError" class="error"></p>
</div>
<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
var _nextUrl = '{next}';
function handleSignIn(response) {{
    try {{
        var payload = JSON.parse(atob(response.credential.split('.')[1]));
        var email = payload.email || '';
        var domain = email.split('@')[1] || '';
        if (domain !== 'google.com') {{
            document.getElementById('signInError').textContent = 'Access restricted to @google.com accounts.';
            document.getElementById('signInError').style.display = 'block';
            return;
        }}
        // Set cookie with the ID token (1 hour expiry matching Google token)
        document.cookie = 'id_token=' + response.credential + '; path=/; max-age=3600; SameSite=Lax; Secure';
        // Also store in localStorage for API calls and shopping iframe
        var user = {{
            firstName: payload.given_name || 'User',
            lastName: payload.family_name || '',
            email: email,
            customerId: 'CY-' + Math.floor(Math.random()*9000+1000) + '-' + Math.floor(Math.random()*9000+1000),
            signInTime: new Date().toISOString(),
            googleIdToken: response.credential,
            picture: payload.picture || ''
        }};
        localStorage.setItem('cymbalUser', JSON.stringify(user));
        window.location.href = _nextUrl;
    }} catch(e) {{
        document.getElementById('signInError').textContent = 'Sign-in failed: ' + e.message;
        document.getElementById('signInError').style.display = 'block';
    }}
}}
</script>
</body>
</html>"""
    )


# Route to serve CRM dashboard from root
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            html = f.read()
        html = html.replace("{{GCS_ASSETS_BASE}}", GCS_ASSETS_BASE)
        return HTMLResponse(content=html)
    else:
        return fastapi.Response(content="index.html not found", status_code=404)


# Route to serve the shopping assistant UI
@app.get("/shop", include_in_schema=False)
async def read_shop():
    shop_path = os.path.join(client_dir, "index.html")
    if os.path.exists(shop_path):
        with open(shop_path) as f:
            html = f.read()
        html = html.replace("{{GCS_ASSETS_BASE}}", GCS_ASSETS_BASE)
        html = html.replace("{{OAUTH_CLIENT_ID}}", OAUTH_CLIENT_ID)
        html = html.replace("{{BUILD_TS}}", str(int(os.path.getmtime(shop_path))))
        return HTMLResponse(content=html)
    else:
        return fastapi.Response(content="Shopping UI not found", status_code=404)


@app.put("/api/v1/approvals/{customer_id}")
async def update_approval(customer_id: str, _user=Depends(require_auth)):
    logger.info(f"Received PUT request for customer ID: {customer_id}")
    document = db.collection("customers").document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({"approval_status": "approved"})
            logger.info(
                f"Successfully updated approval status for customer ID: {customer_id}"
            )
            return {"customer_id": customer_id}
        except Exception as e:
            logger.error(f"Error updating Firestore for customer ID {customer_id}: {e}")
            raise fastapi.HTTPException(
                status_code=500, detail="Internal server error during update"
            )
    else:
        logger.warning(f"Customer ID not found during PUT request: {customer_id}")
        # Return a proper FastAPI HTTP exception for not found
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")


@app.get("/api/v1/approvals/{customer_id}")
async def get_approval(customer_id: str, _user=Depends(require_auth)):
    logger.info(f"Received GET request for customer ID: {customer_id}")
    document = db.collection("customers").document(customer_id).get()
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
async def reset_cart(customer_id: str, _user=Depends(require_auth)):
    CUSTOMER_CART_INFO = {
        "cart_id": "CART-112233",  # Use example ID for consistency
        "items": {
            "GENERIC-PIXEL-CASE": {
                "sku": "1122334",
                "name": "Generic Google Pixel Case",
                "quantity": 1,
                "price": 19,
            }
        },
        "subtotal": 19,
        "last_updated": "2025-04-23 11:05:00",  # Use example timestamp
    }

    logger.info(f"Setting up mock cart info for customer ID: {customer_id}...")
    db.collection("carts").document(customer_id).set(CUSTOMER_CART_INFO)
    logger.info(f"Mock cart info set up for customer ID: {customer_id}")
    return {"status": "success", "customer_id": customer_id, "cart_reset": True}


# Add a route to reset approval status back to pending
@app.post("/api/v1/reset_approval/{customer_id}")
async def reset_approval_status(customer_id: str, _user=Depends(require_auth)):
    logger.info(
        f"Received POST request to reset approval status for customer ID: {customer_id}"
    )
    document = db.collection("customers").document(customer_id).get()
    if document.exists:
        try:
            document.reference.update({"approval_status": "pending"})
            logger.info(
                f"Successfully reset approval status to pending for customer ID: {customer_id}"
            )
            return {
                "status": "success",
                "customer_id": customer_id,
                "approval_status": "pending",
            }
        except Exception as e:
            logger.error(
                f"Error resetting approval status for customer ID {customer_id}: {e}"
            )
            raise fastapi.HTTPException(
                status_code=500,
                detail="Internal server error during approval status reset",
            )
    else:
        logger.warning(
            f"Customer ID not found during reset approval request: {customer_id}"
        )
        raise fastapi.HTTPException(status_code=404, detail="Customer not found")


# ================================================================== #
#  Evaluation API endpoints (reads from GCS)
# ================================================================== #

EVAL_LOG_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "server", "evaluation", "logs"
)
GCS_EVAL_PREFIX = "evaluation/logs"

# Add server dir to path so we can import the evaluation module
_server_dir = os.path.join(os.path.dirname(__file__), "..", "..", "server")
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)


def _list_gcs_eval_sessions():
    """List eval sessions from GCS bucket."""
    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blobs = list(
            bucket.list_blobs(prefix=f"{GCS_EVAL_PREFIX}/session_", delimiter="/")
        )
        sessions = []
        for blob in sorted(blobs, key=lambda b: b.name, reverse=True):
            if "_eval_results" in blob.name:
                continue
            try:
                data = json.loads(blob.download_as_text())
                results_blob = bucket.blob(
                    blob.name.replace(".json", "_eval_results.json")
                )
                has_results = results_blob.exists()
                sessions.append(
                    {
                        "file": os.path.basename(blob.name),
                        "session_id": data.get("session_id"),
                        "customer_id": data.get("customer_id"),
                        "start_time": data.get("start_time"),
                        "duration_seconds": data.get("duration_seconds"),
                        "turn_count": data.get("turn_count"),
                        "tool_call_count": data.get("tool_call_count"),
                        "cost_usd": data.get("cost_usd", 0),
                        "token_usage": data.get("token_usage", {}),
                        "has_eval_results": has_results,
                    }
                )
            except Exception:
                pass
        return sessions
    except Exception as e:
        logger.warning(f"Failed to read eval sessions from GCS: {e}")
        return []


def _list_local_eval_sessions():
    """Fallback: list eval sessions from local filesystem."""
    files = sorted(
        glob.glob(os.path.join(EVAL_LOG_DIR, "session_*.json")), reverse=True
    )
    files = [f for f in files if "_eval_results" not in f]
    sessions = []
    for f in files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            results_file = f.replace(".json", "_eval_results.json")
            has_results = os.path.exists(results_file)
            sessions.append(
                {
                    "file": os.path.basename(f),
                    "session_id": data.get("session_id"),
                    "customer_id": data.get("customer_id"),
                    "start_time": data.get("start_time"),
                    "duration_seconds": data.get("duration_seconds"),
                    "turn_count": data.get("turn_count"),
                    "tool_call_count": data.get("tool_call_count"),
                    "cost_usd": data.get("cost_usd", 0),
                    "token_usage": data.get("token_usage", {}),
                    "has_eval_results": has_results,
                }
            )
        except Exception:
            pass
    return sessions


@app.get("/api/v1/eval/sessions")
async def list_eval_sessions(_user=Depends(require_auth)):
    """List all recorded evaluation sessions from GCS or local fallback.

    Filters out empty sessions (0 turns) which result from dropped
    connections and contain no meaningful data.
    """
    sessions = _list_gcs_eval_sessions()
    if not sessions:
        sessions = _list_local_eval_sessions()
    sessions = [s for s in sessions if (s.get("turn_count") or 0) > 0]
    return {"sessions": sessions}


@app.post("/api/v1/eval/run/{filename}")
async def run_evaluation(
    filename: str, use_vertex: bool = True, _user=Depends(require_auth)
):
    """Run evaluation on a specific session log (GCS or local)."""
    # Try local first
    filepath = os.path.realpath(os.path.join(EVAL_LOG_DIR, filename))
    if not filepath.startswith(os.path.realpath(EVAL_LOG_DIR) + os.sep):
        raise fastapi.HTTPException(status_code=400, detail="Invalid filename")

    # If not local, download from GCS
    if not os.path.exists(filepath):
        try:
            from google.cloud import storage

            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(f"{GCS_EVAL_PREFIX}/{filename}")
            if blob.exists():
                os.makedirs(EVAL_LOG_DIR, exist_ok=True)
                blob.download_to_filename(filepath)
                logger.info(f"Downloaded eval session from GCS: {filename}")
            else:
                raise fastapi.HTTPException(
                    status_code=404, detail="Session file not found"
                )
        except fastapi.HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to download from GCS: {e}")
            raise fastapi.HTTPException(
                status_code=404, detail="Session file not found"
            )

    try:
        from evaluation.run_eval import evaluate_session

        results = evaluate_session(filepath, use_vertex=use_vertex)

        # Save results to GCS
        try:
            from google.cloud import storage as _storage

            results_filename = filename.replace(".json", "_eval_results.json")
            _client = _storage.Client()
            _bucket = _client.bucket(GCS_BUCKET_NAME)
            _blob = _bucket.blob(f"{GCS_EVAL_PREFIX}/{results_filename}")
            if _blob.exists():
                _blob.delete()
            _blob.upload_from_string(
                json.dumps(results, indent=2, default=str),
                content_type="application/json",
            )
            logger.info(f"Eval results saved to GCS: {results_filename}")
        except Exception as gcs_err:
            logger.warning(f"Failed to save eval results to GCS: {gcs_err}")

        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/eval/results/{filename}")
async def get_eval_results(filename: str, _user=Depends(require_auth)):
    """Get evaluation results from GCS."""
    results_name = filename.replace(".json", "_eval_results.json")

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(f"{GCS_EVAL_PREFIX}/{results_name}")
        if blob.exists():
            data = json.loads(blob.download_as_text())
            logger.info(
                f"Eval results loaded from GCS: {results_name} "
                f"(score={data.get('overall', {}).get('score')})"
            )
            return data
    except Exception as e:
        logger.warning(f"GCS eval results lookup failed: {e}")

    raise fastapi.HTTPException(
        status_code=404,
        detail="Evaluation results not found. Run evaluation first.",
    )


@app.put("/api/v1/eval/results/{filename}")
async def put_eval_results(
    filename: str, request: fastapi.Request, _user=Depends(require_auth)
):
    """Upload eval results directly to GCS."""
    results_name = filename.replace(".json", "_eval_results.json")
    body = await request.json()
    try:
        from google.cloud import storage

        content = json.dumps(body, indent=2, default=str)
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(f"{GCS_EVAL_PREFIX}/{results_name}")
        if blob.exists():
            blob.delete()
        blob.upload_from_string(content, content_type="application/json")

        logger.info(
            f"Eval results written via PUT: {results_name} "
            f"(score={body.get('overall', {}).get('score')})"
        )
        return {"status": "success", "file": results_name}
    except Exception as e:
        logger.error(f"Failed to write eval results: {e}")
        raise fastapi.HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/eval/analytics")
async def eval_analytics(_user=Depends(require_auth)):
    """Return aggregate analytics across all evaluated sessions."""
    sessions = _list_gcs_eval_sessions()
    if not sessions:
        sessions = _list_local_eval_sessions()
    sessions = [s for s in sessions if (s.get("turn_count") or 0) > 0]

    total_sessions = len(sessions)
    total_cost = sum(s.get("cost_usd", 0) for s in sessions)
    total_tokens = sum(
        (s.get("token_usage", {}).get("input_tokens", 0) or 0)
        + (s.get("token_usage", {}).get("output_tokens", 0) or 0)
        for s in sessions
    )
    total_duration = sum(s.get("duration_seconds", 0) or 0 for s in sessions)

    # Collect scores from evaluated sessions
    scores = []
    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        for s in sessions:
            if not s.get("has_eval_results"):
                continue
            try:
                results_name = s["file"].replace(".json", "_eval_results.json")
                blob = bucket.blob(f"{GCS_EVAL_PREFIX}/{results_name}")
                if blob.exists():
                    result = json.loads(blob.download_as_text())
                    overall = result.get("overall", {})
                    score = overall.get("score")
                    if score is not None:
                        latency_data = result.get("speech_latency", {})
                        scores.append(
                            {
                                "session_id": s.get("session_id"),
                                "score": score,
                                "grade": overall.get("grade", "?"),
                                "latency": latency_data.get("p95_latency_seconds"),
                            }
                        )
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Failed to collect eval scores: {e}")

    avg_score = sum(sc["score"] for sc in scores) / len(scores) if scores else None
    latencies = [sc["latency"] for sc in scores if sc.get("latency") is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None

    return {
        "total_sessions": total_sessions,
        "evaluated_sessions": len(scores),
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "total_duration": total_duration,
        "avg_score": avg_score,
        "avg_latency": avg_latency,
        "scores": scores,
    }


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
