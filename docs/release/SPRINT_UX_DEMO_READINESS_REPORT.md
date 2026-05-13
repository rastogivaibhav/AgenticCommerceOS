# Sprint UX + Demo Readiness Report

## Scope

This sprint closes the review feedback that the product had missing UX screens and unclear demo/testing guidance.

## Added UX screens

### `/ui/demo-guide`

A buyer/CTO-facing guided demo script that explains:

- product narrative
- target persona
- demo message
- six-step storyboard
- success criteria
- commands to prove the build
- RBAC notes for protected demos

### `/ui/test-center`

A QA/operator proof hub that explains:

- backend test commands
- UI build command
- Alembic migration proof
- Docker production runtime check
- MCP and GraphQL checks
- a runnable golden journey smoke action from the UI

## Added API support

### `GET /api/northstar/demo-script`

Returns the demo storyboard, talk track, success criteria and proof commands.

### `GET /api/northstar/test-plan`

Returns the concrete test matrix for functional, backend, UAT, runtime, frontend, database, deployment, MCP and GraphQL proof.

## Documentation added

- `docs/demo/ACOS_DEMO_RUNBOOK.md`
- `docs/qa/ACOS_TEST_PLAN.md`

## Bug fixed

`NorthstarMessageRequest` now includes a `metadata` field. The endpoint was previously using `request.metadata` without declaring it in the Pydantic request model.

## Validation evidence

```text
pytest -q harness/python/tests/northstar
20 passed
```

```text
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
27 passed
```

```text
python scripts/northstar_smoke.py
success; intent=styling_advice; tool_calls=7; evidence_events=15
```

```text
python scripts/production_runtime_check.py
status=pass; docker_available=false
```

```text
cd apps/ops_ui_v2 && npm ci && npm run build
Vite build successful
```

```text
python -m compileall -q apps acosplatform migrations scripts
passed
```

## Remaining external proof

Docker runtime and cloud deployment still require a Docker-enabled machine or target cloud runner.
