# ACOS Fresh Build Load Verification Report

Date: 2026-05-11
Build: `AgenticCommerceOS-fresh-load-verified.zip`

## Purpose

The previous package was reported as not loading correctly. This fresh build was rebuilt from the latest API-plane-connected code and patched to improve UI shell serving and load verification.

## Fixes Applied

- Rebuilt the React production bundle from `apps/ops_ui_v2`.
- Added FastAPI `HEAD /ui`, `HEAD /ui/`, and `HEAD /ui/{path:path}` handlers so load balancers, proxies, and browser/preflight probes do not receive `405 Method Not Allowed` for the UI shell.
- Added `scripts/ui_load_check.py` to verify the embedded UI shell, deep links, and built assets from the FastAPI app.
- Added `make ui-load-check`.
- Regenerated `apps/ops_ui_v2/dist`.

## Load Verification

`python scripts/ui_load_check.py` passed.

Verified:

- `GET /ui/` returns 200.
- `HEAD /ui/` returns 200.
- React shell includes `<div id="root"></div>`.
- Built JS/CSS assets referenced by `index.html` are served from `/ui/assets/...`.
- Deep link `GET /ui/runs` serves the React shell.
- All discovered assets returned 200.

## Build/Test Evidence

Passed:

```text
pytest -q harness/python/tests/northstar
23 passed
```

Passed:

```text
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
27 passed
```

Passed:

```text
python scripts/northstar_smoke.py
status: success
intent: styling_advice
tool calls: 7
evidence events: 15
```

Passed:

```text
python scripts/production_runtime_check.py
status: pass
docker_available: false
```

Passed:

```text
cd apps/ops_ui_v2 && npm run build
vite build successful
```

## How to Load Locally

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cd apps/ops_ui_v2 && npm ci && npm run build && cd ../..
PYTHONPATH=. OPS_ENVIRONMENT=dev ALLOW_INSECURE_DEV_AUTH=1 uvicorn apps.ops_api.main:app --host 0.0.0.0 --port 8081
```

Open:

```text
http://localhost:8081/ui/
http://localhost:8081/ui/runs
http://localhost:8081/ui/demo-guide
http://localhost:8081/ui/api-plane
```

## Notes

Docker runtime remains unverified in this sandbox because Docker is not installed here. The package includes production compose assets for verification in a Docker-enabled environment.
