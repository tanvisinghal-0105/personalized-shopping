---
name: test-suite
description: "Run comprehensive testing for the personalized shopping project -- unit tests, Terraform validation, syntax checks, GCS connectivity, evaluation framework, and server import verification. Use this skill whenever the user asks to test the project, run tests, validate infrastructure, check code quality, verify the build, or wants a health check before deploying. Also use when the user says things like 'run tests', 'check everything works', 'validate', 'CI check', or 'is everything passing?'"
---

# Personalized Shopping - Test Suite

This skill runs a comprehensive, multi-layer test suite for the OTTO personalized shopping assistant project. The project lives at the working directory root and has this structure:

```
server/          - Python WebSocket backend (Gemini Live API, ADK agent)
client/          - Static frontend (HTML/JS/CSS)
crm/             - FastAPI CRM dashboard
terraform/       - GCP infrastructure as code
server/evaluation/ - Custom eval framework + Vertex AI integration
server/tests/    - pytest unit tests
```

## How to run

Execute each test layer in sequence. Report results as a checklist with pass/fail status. Stop on critical failures (syntax errors, import failures) but continue through test failures to give a full picture.

### Layer 1: Python Syntax Validation

Check all Python files compile without syntax errors. This catches typos and malformed code before anything else runs.

```bash
cd <project_root>/server
find . -name "*.py" -exec python -c "import ast; ast.parse(open('{}').read()); print('OK: {}')" \; 2>&1 | grep -v OK | head -20
```

Also check the CRM:
```bash
cd <project_root>/crm
find . -name "*.py" -exec python -c "import ast; ast.parse(open('{}').read()); print('OK: {}')" \; 2>&1 | grep -v OK | head -20
```

If any files fail, report them and stop -- nothing else will work until syntax is fixed.

### Layer 2: Server Import Verification

Verify the server can import its core modules without crashing. This catches missing dependencies, circular imports, and config issues.

```bash
cd <project_root>/server
python -c "from core.agents.retail.intent_detector import IntentDetector; print('intent_detector OK')"
python -c "from core.agents.retail.session_state import HomeDecorSessionState; print('session_state OK')"
python -c "from evaluation.session_recorder import get_recorder; print('session_recorder OK')"
python -c "from evaluation.run_eval import trajectory_order_metric; print('eval_metrics OK')"
python -c "from config.config import GCS_BUCKET_NAME, get_asset_url; print('config OK')"
```

Each import should print OK. If any fail, report the error -- it usually means a missing package or broken import chain.

### Layer 3: Unit Tests (pytest)

Run the pytest test suite. These test the core business logic without needing external services.

```bash
cd <project_root>/server
python -m pytest tests/ -v --tb=short 2>&1
```

Report the summary line (X passed, Y failed). If tests fail, show the failure details.

Key test files:
- `tests/test_intent_detector.py` - Intent detection for home decor requests
- `tests/test_session_state.py` - Session state management (create, update, get)
- `tests/test_eval_metrics.py` - Evaluation metric calculations (WER, trajectory, moodboard quality)

### Layer 4: Terraform Validation

Validate the Terraform configuration syntax and structure. This does NOT apply changes -- it only checks if the config is valid.

```bash
cd <project_root>/terraform
terraform init -backend=false 2>&1 | tail -5
terraform validate 2>&1
```

Use `-backend=false` on init to skip the GCS state backend (which may not exist locally). The validate command checks HCL syntax and resource references.

If terraform is not installed, report it as skipped (not failed) and suggest: `brew install terraform`

### Layer 5: GCS Bucket Connectivity

Verify the GCS bucket exists and is accessible. Read the bucket name from the server config.

```bash
cd <project_root>/server
python -c "
from config.config import GCS_BUCKET_NAME
from google.cloud import storage
client = storage.Client()
bucket = client.bucket(GCS_BUCKET_NAME)
if bucket.exists():
    print(f'GCS bucket OK: {GCS_BUCKET_NAME}')
    blobs = list(client.list_blobs(GCS_BUCKET_NAME, max_results=5))
    print(f'  Objects: {len(blobs)} (showing first 5)')
    for b in blobs:
        print(f'    {b.name}')
else:
    print(f'GCS bucket NOT FOUND: {GCS_BUCKET_NAME}')
"
```

If the bucket doesn't exist, report it as a warning (not failure) -- local dev works without GCS. Suggest running `terraform apply` or creating it manually.

### Layer 6: Evaluation Framework

Check if any recorded sessions exist and optionally run evaluation on them.

```bash
cd <project_root>/server
python -c "
import glob, os
logs = glob.glob('evaluation/logs/session_*.json')
logs = [f for f in logs if '_eval_results' not in f]
print(f'Recorded sessions: {len(logs)}')
for f in sorted(logs)[-3:]:
    print(f'  {os.path.basename(f)}')
"
```

If sessions exist, run the custom metrics evaluation (skip Vertex AI to keep it fast):

```bash
cd <project_root>/server
python -m evaluation.run_eval --no-vertex 2>&1
```

### Layer 7: Frontend Asset Check

Verify product images and style assets exist and are not broken references.

```bash
cd <project_root>
echo "Client assets: $(find client/assets -type f | wc -l) files"
echo "Product images: $(find client/assets/products -type f 2>/dev/null | wc -l) files"
```

## Output Format

Present results as a clear checklist:

```
Test Suite Results
==================
[PASS] Layer 1: Python Syntax          - All 45 files OK
[PASS] Layer 2: Server Imports          - All 5 modules OK
[FAIL] Layer 3: Unit Tests              - 12 passed, 2 failed
       - test_intent_detector::test_rejects_greeting FAILED
       - test_session_state::test_none_does_not_overwrite FAILED
[PASS] Layer 4: Terraform Validation    - Config valid
[SKIP] Layer 5: GCS Connectivity        - Bucket not found (expected in local dev)
[PASS] Layer 6: Evaluation Framework    - 2 sessions, latest score: 78% (C)
[PASS] Layer 7: Frontend Assets         - 203 files present

Overall: 5/7 passed, 1 failed, 1 skipped
```

Focus the user's attention on failures -- they need to know what broke and ideally why.
