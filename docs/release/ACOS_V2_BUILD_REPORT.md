# ACOS v2 Build Report

## Status

ACOS v2 foundation has been added on top of the north-star runtime.

## Added

- Agent Registry
- Capability Registry
- A2A invocation and traces
- Channel modes
- Tone profiles
- Evaluation framework proof
- Guardrails and FinOps proof
- Memory access proof
- Route-to-production proof
- ACOS v2 Alembic migration
- ACOS v2 UI screens
- ACOS v2 demo smoke script
- ACOS v2 targeted tests

## Validation evidence

- `pytest -q harness/python/tests/northstar` → 28 passed
- `pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py` → 27 passed
- `python scripts/northstar_smoke.py` → success
- `python scripts/production_runtime_check.py` → pass, Docker unavailable in sandbox
- `PYTHONPATH=. python scripts/ui_load_check.py` → pass
- `cd apps/ops_ui_v2 && npm run build` → Vite build successful

## Honest remaining external checks

- Run production Docker Compose on Docker-enabled machine.
- Run Alembic migrations against real Postgres.
- Certify A2A/MCP against chosen external vendor agent clients.
- Connect real John Lewis systems or sandbox equivalents for product/order/returns data.
