# Testing Guide

## Quick Run

Use the Claude Code skill:
```
/test-suite
```

This runs all 7 test layers automatically.

## Manual Testing

### Unit Tests
```bash
cd server
python -m pytest tests/ -v
python -m pytest tests/test_intent_detector.py -v    # specific file
python -m pytest tests/ -v --tb=short                # short tracebacks
```

### Terraform Validation
```bash
cd terraform
terraform init -backend=false
terraform validate
```

### Evaluation Framework
```bash
cd server
python -m evaluation.run_eval --no-vertex    # custom metrics only
python -m evaluation.run_eval               # full eval with Vertex AI
python -m evaluation.run_eval --all          # all recorded sessions
```

### Server Import Check
```bash
cd server
python -c "from core.agents.retail.intent_detector import IntentDetector; print('OK')"
python -c "from core.agents.retail.session_state import HomeDecorSessionState; print('OK')"
python -c "from evaluation.run_eval import trajectory_order_metric; print('OK')"
```

## Test Files

| File | Tests |
|------|-------|
| `server/tests/test_intent_detector.py` | Home decor intent detection, room type extraction |
| `server/tests/test_session_state.py` | Session create, update, get, moodboard marking |
| `server/tests/test_eval_metrics.py` | WER, trajectory order, step skip, moodboard quality, latency |
| `server/tests/test_auth.py` | Token validation, IAP JWT verification, dev mode fallback |
| `server/tests/test_cost_tracker.py` | Token counting, USD cost calculation, session tracking |
| `server/tests/test_observability.py` | Metrics collection, error recording, health reporting |
| `server/tests/test_retry.py` | Retryable error classification, backoff logic, 429/503 handling |
| `server/tests/test_security.py` | Input sanitization, PII detection, injection guard, audit logging |

## GCS Upload (for deployment)
```bash
cd server
python scripts/upload_assets_to_gcs.py --dry-run    # preview
python scripts/upload_assets_to_gcs.py               # upload
```
