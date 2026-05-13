# Sprint Report — API Plane to Screen Connectivity

## Objective
Verify and close gaps where product screens were not clearly connected to the API plane.

## Result
The operator UI now includes an explicit API Plane screen and every primary screen is either connected to live REST/North-star/GraphQL APIs or documented as server-side MCP surfaced through the API proof layer.

## Fixes made

### 1. Added API Plane screen

New route:

```text
/ui/api-plane
```

New file:

```text
apps/ops_ui_v2/src/pages/APIPlane.jsx
```

The screen shows:

- screen-to-endpoint matrix
- REST plane coverage
- North-star REST coverage
- GraphQL probe
- MCP server-side exposure note
- RBAC/API-key header reminder

### 2. Added API Plane backend endpoint

New endpoint:

```text
GET /api/northstar/api-plane
```

It returns the screen/API mapping used by the UI.

### 3. Fixed Analytics API wiring

Frontend analytics calls now use the actual backend router prefix:

```text
GET /api/analytics/metrics
GET /api/analytics/timeseries
GET /api/analytics/workflows
GET /api/analytics/export
```

Previously, the UI called `/analytics/...`, which did not match the mounted router prefix.

### 4. Exposed existing Experiments and Simulation screens

Added routes and navigation entries:

```text
/ui/experiments
/ui/simulation
```

### 5. Connected Simulation to north-star API

Simulation now calls:

```text
GET /api/northstar/runs
POST /api/northstar/messages
```

This means the simulation screen is no longer purely static; it can run/load the golden journey.

### 6. Added GraphQL browser probe

The API Plane screen calls:

```text
POST /graphql
```

Default query:

```graphql
{ tools { name protocol } }
```

## Screen-to-API coverage

| Screen | Route | API plane | Status |
|---|---|---|---|
| Workflows | `/ui/workflows` | REST | Connected |
| Workflow Editor | `/ui/workflows/:id/editor` | REST | Connected |
| Studio Proof | `/ui/studio-proof` | North-star REST | Connected |
| Runs | `/ui/runs` | North-star REST | Connected |
| Demo Guide | `/ui/demo-guide` | North-star REST | Connected |
| Test Center | `/ui/test-center` | North-star REST | Connected |
| API Plane | `/ui/api-plane` | North-star REST + GraphQL | Connected |
| Channels | `/ui/channels` | REST | Connected |
| Routes | `/ui/demo-routes` | REST | Connected |
| Agents | `/ui/agents` | REST | Connected |
| Skills | `/ui/skills` | REST | Connected |
| Analytics | `/ui/analytics` | REST | Connected |
| Tenants | `/ui/tenants` | REST | Connected |
| Experiments | `/ui/experiments` | REST | Connected |
| Simulation | `/ui/simulation` | North-star REST | Connected |

## Validation

```text
pytest -q harness/python/tests/northstar
23 passed
```

```text
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
27 passed
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
cd apps/ops_ui_v2 && npm ci && npm run build
Vite build successful
```

## Remaining external checks

- Docker compose runtime still requires a Docker-enabled runner.
- MCP certification still requires the exact target MCP client(s).
- Shopper API journey simulation requires shopper-api service deployment or `VITE_SHOPPER_API_URL`.
