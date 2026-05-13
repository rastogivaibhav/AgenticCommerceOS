# ACOS v2 Demo Runbook

## Start locally

```bash
PYTHONPATH=. OPS_ENVIRONMENT=dev ALLOW_INSECURE_DEV_AUTH=1 uvicorn apps.ops_api.main:app --host 0.0.0.0 --port 8081
```

Open:

```text
http://localhost:8081/ui/estate
```

## Recommended demo flow

1. `/ui/estate` — explain ACOS v2 as the agentic retail estate control plane.
2. Click **Run nursery + mattress + returns A2A demo**.
3. `/ui/a2a-trace` — show orchestrator → specialist agents → tools → response merge.
4. `/ui/agent-registry` — show agents as governed production assets.
5. `/ui/capabilities` — show intent/capability/agent coverage.
6. `/ui/channel-modes` — show same agent, different channel presentation.
7. `/ui/evaluations` — show quality gates and split recommendation.
8. `/ui/governance` — show guardrails, FinOps, memory audit and route to production.

## CLI proof

```bash
PYTHONPATH=. python scripts/acos_v2_demo_smoke.py
pytest -q harness/python/tests/northstar/test_acos_v2_estate.py
```
