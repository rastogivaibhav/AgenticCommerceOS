# ACOS v2 Production Backbone Fix Report

## Scope fixed

This sprint addressed the ten priority blockers from the ACOS v2 code review.

### 1. Replace v2 in-memory registries with repository-backed runtime

Added `acosplatform/v2_store/repository.py` and wired the v2 agent, capability, A2A trace/task, tool, MCP, memory, evaluation, route-to-production and vendor-agent foundations through a persistent repository abstraction.

Local/pilot mode uses SQLite at `var/acos_v2.db`. Production schema is represented by Alembic migrations and CI is configured to run migrations against Postgres.

### 2. Expand Alembic schema

Added migration:

```text
migrations/versions/20260513_0003_acos_v2_production_backbone.py
```

It adds production backbone tables for:

- agent versions
- A2A tasks
- tools
- MCP servers
- memory records
- memory access events
- evaluation sets/runs
- approval requests
- vendor agents / kill switch

Alembic SQL generation passed using a Postgres URL.

### 3. A2A task lifecycle and vendor mock adapter

Added package files:

```text
acosplatform/a2a/contracts.py
acosplatform/a2a/task_state.py
acosplatform/a2a/vendor_adapter.py
acosplatform/a2a/response_merge.py
acosplatform/a2a/evidence.py
acosplatform/a2a/router.py
acosplatform/a2a/planner.py
acosplatform/a2a/auth.py
acosplatform/a2a/errors.py
acosplatform/a2a/invocation.py
```

A2A runs now create persisted task records and can invoke a mock vendor agent. Vendor agents support a kill switch.

### 4. Missing v2 APIs added

Added or completed:

```text
POST /api/v2/agents/{agent_id}/versions
POST /api/v2/agents/{agent_id}/promote
POST /api/v2/agents/{agent_id}/retire
GET  /api/v2/capabilities/coverage
POST /api/v2/a2a/tasks
GET  /api/v2/a2a/tasks
GET  /api/v2/a2a/tasks/{task_id}
GET  /api/v2/tools
POST /api/v2/tools
GET  /api/v2/mcp/servers
POST /api/v2/mcp/servers
GET  /api/v2/memory/session/{session_id}
GET  /api/v2/memory/journey/{journey_id}
POST /api/v2/evaluations/run
GET  /api/v2/evaluations/{run_id}
GET  /api/v2/vendor-agents
POST /api/v2/vendor-agents
POST /api/v2/vendor-agents/{vendor_agent_id}/kill-switch
```

### 5. Dedicated screens added

Added first-class UI pages:

```text
/ui/tool-registry
/ui/memory
/ui/tone
/ui/finops
/ui/route-to-production
```

### 6. A2A traces integrated into Runs

The Runs screen now also displays recent ACOS v2 A2A traces with agents, policy decisions, memory reads and cost.

### 7. Production promotion gates enforced

Agent promotion now checks owner, capabilities, supported channels, tools, risk rating, fallback and evaluation score. Incomplete agents return `409` instead of silently promoting.

### 8. Vendor-agent registration and kill switch

Added vendor-agent registry APIs and a mock vendor adapter. Disabled/killed vendor agents cannot be invoked.

### 9. Policy/cost controls inside orchestration

The A2A orchestrator now records policy decisions, cost estimates, memory access and tool trace evidence as part of each trace. High-risk returns operations require human approval style verdicts.

### 10. Docker Compose and Alembic in CI

Added:

```text
.github/workflows/acos-v2-production-ci.yml
```

The workflow provisions Postgres and Redis, runs Alembic migrations, backend tests, demo smokes, frontend build, Docker Compose config and Docker Compose runtime smoke.

## Validation run in this sandbox

```text
pytest -q harness/python/tests/northstar
32 passed
```

```text
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
27 passed
```

```text
python scripts/acos_v2_demo_smoke.py
success
```

```text
python scripts/northstar_smoke.py
success
```

```text
python scripts/production_runtime_check.py
status: pass
```

```text
DATABASE_URL=postgresql://acos:acos@localhost:5432/acos python -m alembic upgrade head --sql
passed / generated SQL through revision 20260513_0003
```

```text
cd apps/ops_ui_v2 && npm run build
Vite build successful
```

```text
python scripts/ui_load_check.py
status: pass
```

## Remaining external validation

Docker is still not available inside this sandbox, so actual `docker compose up` runtime proof must be completed in GitHub Actions or a Docker-enabled machine. The CI workflow has been added to perform that check.
