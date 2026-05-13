# Sprint Report — Production Runtime + Studio Proof

## Scope

This sprint reviewed the pending north-star scope and focused on the next critical sprint: **Production Runtime + Studio Proof**.

## Implemented

### Production runtime proof

- Added `docker-compose.prod.yml` with production-posture services:
  - `ops-api`
  - `shopper-api`
  - `chat-api`
  - `mcp-server`
  - `postgres`
- Added `.env.production.example`.
- Added `docs/deployment/PRODUCTION_RUNTIME_GUIDE.md`.
- Added `scripts/production_runtime_check.py`.
- Added `make compose-prod-up` and `make runtime-check`.
- Updated `.github/workflows/northstar-ci.yml` to run production compose smoke on Docker-enabled GitHub runners.

### Studio proof APIs

Added read-only north-star proof endpoints:

- `GET /api/northstar/studio-proof`
- `GET /api/northstar/handoffs`
- `GET /api/northstar/outbox`
- `GET /api/northstar/readiness`

The Studio proof endpoint aggregates:

- golden journey result
- participating agents
- tool calls
- evidence events
- human handoffs
- MCP tool list
- session/journey snapshots
- outbox events
- production readiness checks

### Agent Studio v2 proof screen

Added:

- `apps/ops_ui_v2/src/pages/StudioProof.jsx`
- `apps/ops_ui_v2/src/pages/StudioProof.css`
- `apps/ops_ui_v2/src/api/northstarAPI.js`
- Sidebar route: `/ui/studio-proof`

The Studio Proof screen includes:

- Retail Simulation Console
- Agent Registry proof
- MCP Tool Browser
- Human Handoff Queue
- Tabbed Inspector: Node, Prompts, Connectors, Evidence, Tests, Deployment
- Deployment readiness panel

### Repository/runtime support

Added repository helpers:

- `list_sessions()`
- `list_journeys()`

Updated CORS to allow `X-API-Key` so north-star/MCP protected APIs can work from browser-based Studio clients.

## Validation evidence

### North-star test suite

```text
15 passed
```

### UAT + production gate tests

```text
27 passed
```

### Production runtime static check

```text
status: pass
missing_files: []
missing_tools: []
golden_journey_status: success
tool_count: 7
evidence_count: 15
docker_available: false
```

### Golden journey smoke

```text
ACOS north-star smoke status: success
Intent: styling_advice
Agent: Stylist Agent
Tool calls: 7
Evidence events: 15
```

### Frontend build

```text
vite build successful
```

Known warning remains: generated JS chunk is larger than 500 KB.

## Still not certified in this sandbox

Docker is not installed in this environment. Production Docker Compose smoke is now defined in CI, but not sandbox-certified here.

## Remaining GA blockers

- Run production compose proof in Docker-enabled CI or local machine.
- Complete Postgres-backed north-star repository switch at runtime.
- Add production RBAC/tenant isolation to GraphQL resolvers and Studio proof APIs beyond API-key gating.
- Implement full replay UI and replay persistence for golden journey.
- Harden DLP, cost enforcement, prompt immutability and policy decisions.
- Certify external MCP clients against `/mcp`.
- Address Vite bundle warning with code splitting.

## Current verdict

The app is now stronger than pilot foundation:

> ACOS now has a working north-star runtime, golden multi-agent retail journey, durable local state, event outbox foundation, MCP server/client foundation, GraphQL Studio mutations, Studio Proof screen, production compose assets, and CI-defined production runtime proof.

It is still not full enterprise GA until Docker/cloud/runtime/RBAC/governance certification is completed.
