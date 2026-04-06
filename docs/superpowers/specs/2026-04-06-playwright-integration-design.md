# Playwright Integration Test Suite Design
**Date:** 2026-04-06
**Status:** Approved

## Context

The ACOS platform has 34 passing Playwright E2E tests that verify UI rendering only. Three gaps remain before Week 11 UAT sign-off:
- No full-stack verification (UI → API → DB)
- Week 10 noisy-neighbor/quota evidence not yet captured
- No agent journey validation

This spec defines an integration test suite that closes all three gaps using Playwright + direct Postgres assertions, running against the live Docker stack at `http://localhost:8081`.

## Constraints

- Docker Compose stack must be running before tests execute (no `webServer` block)
- `ALLOW_INSECURE_DEV_AUTH` is not set — tests must generate real JWTs
- JWT secret: `OPS_JWT_SECRET=dev-secret-key-for-testing-only` (HS256)
- Shopper API key: `X-API-Key: test-key-1`
- Postgres: `postgresql://acos:acos_dev_password@localhost:5432/acos`

## File Layout

```
apps/ops_ui_v2/
├── playwright.config.integration.js        ← new config, baseURL :8081, no webServer
├── tests-e2e-integration/
│   ├── fixtures/
│   │   ├── auth.js                         ← JWT generation (jsonwebtoken, HS256)
│   │   ├── db.js                           ← pg.Pool helper
│   │   └── index.js                        ← composes both into extended test object
│   ├── workflow-lifecycle.spec.js
│   ├── tenant-quota.spec.js
│   └── agents.spec.js
```

## Shared Fixtures

### `fixtures/auth.js`
Generates a signed JWT on each test run using `jsonwebtoken` with payload `{ sub: "e2e-test-user", role: "admin" }` signed against `OPS_JWT_SECRET`. Exposes `authHeaders` (for Ops API) and `shopperHeaders` (for Shopper API). Composed into the `test` fixture so every spec has access without extra imports.

### `fixtures/db.js`
Opens a `pg.Pool` connected to the local Postgres instance. Exposes `db.query(sql, params)` for `SELECT` assertions after UI/API actions. Pool is torn down after each test file. Tests never write to the DB directly — only read to assert state created by the application under test.

### `fixtures/index.js`
Merges auth and db fixtures into a single extended `test` export. Each spec imports only from here:
```js
import { test, expect } from '../fixtures/index.js';
```

## Test Suite 1: `workflow-lifecycle.spec.js`

**Purpose:** Prove the full draft → approve → promote lifecycle writes correctly to the DB with an audit trail.

**Steps:**
1. `POST /workflows` with `authHeaders` — capture `workflow_id`
2. Assert response `state === "draft"`
3. `POST /workflows/{id}/approve` — assert `state === "approved"`
4. `POST /workflows/{id}/promote` — assert `state === "promoted"`
5. DB: `SELECT state FROM workflows WHERE id = $1` → `"promoted"`
6. DB: `SELECT COUNT(*) FROM workflow_audit WHERE workflow_id = $1` ≥ 3
7. Cleanup: `POST /workflows/{id}/archive`

## Test Suite 2: `tenant-quota.spec.js`

**Purpose:** Close the Week 10 evidence gap — prove rate-limiting blocks a hot tenant and does not affect neighbors.

**Steps:**
1. Read `TENANT_RATE_LIMIT_PER_MINUTE` from env (default 120); use a small override for test speed via env var `TENANT_RATE_LIMIT_PER_MINUTE=3` set in the test config
2. Fire `limit + 1` `POST /journey` requests as `tenant-a` using `shopperHeaders`
3. Assert the final response status is `429` with body containing `retry_after_seconds`
4. Fire 1 `POST /journey` as `tenant-b` → assert `200`
5. Capture `GET /metrics` response and write to `deploy/k8s/observability/evidence/week10-quota-{timestamp}.json`

**Note:** This suite targets the traffic guard middleware directly via API — no UI navigation needed. Still runs under Playwright for unified HTML reporting.

## Test Suite 3: `agents.spec.js`

**Purpose:** Verify the agents UI loads real data from the API and new agents persist to the DB.

**Steps:**
1. Navigate to `http://localhost:8081/ui/agents`
2. Assert page renders without console errors
3. Assert agents list element is visible (non-crashing empty state or populated rows)
4. `page.request.post('/api/v1/agents', { data: { name: 'e2e-test-agent', type: 'test' } })` with `authHeaders`
5. Reload page → assert agent name `'e2e-test-agent'` appears in the rendered list
6. DB: `SELECT id FROM agents WHERE name = 'e2e-test-agent'` → returns a row
7. Cleanup: `DELETE /api/v1/agents/{id}`

## Playwright Config

`playwright.config.integration.js`:
- `testDir: './tests-e2e-integration'`
- `baseURL: 'http://localhost:8081'`
- No `webServer` block
- Single project: `chromium`
- `timeout: 30000`, `expect.timeout: 10000`

Run command:
```bash
cd apps/ops_ui_v2
npx playwright test --config playwright.config.integration.js
```

## Dependencies

`jsonwebtoken` must be available in `apps/ops_ui_v2/node_modules`. Check with:
```bash
cd apps/ops_ui_v2 && node -e "require('jsonwebtoken')"
```
If missing: `npm install --save-dev jsonwebtoken pg`

## Evidence Artifacts

- Week 10 quota evidence: `deploy/k8s/observability/evidence/week10-quota-{timestamp}.json`
- Playwright HTML report: `apps/ops_ui_v2/playwright-report/` (existing)

## Success Criteria

- All three suites pass against the live stack
- DB assertions confirm state, not just API responses
- `week10-quota-*.json` evidence file written and committed
- Week 11 UAT pilot scripts can extend `workflow-lifecycle.spec.js` with tenant-specific scenarios
