# ACOS Sprint Next Hardening Report

## Sprint Goal
Move the north-star ACOS build from an in-memory pilot foundation toward a more credible GA track by hardening persistence, auth guardrails, MCP/GraphQL confidence, and release evidence.

## Completed Scope

### 1. Durable North-Star Runtime State
Added a local durable repository at `acosplatform/northstar/repository.py`.

It persists:
- conversation sessions
- channel identity index
- journeys
- messages
- evidence events

Default local store:

```text
var/acos_northstar.db
```

Override with:

```bash
ACOS_NORTHSTAR_SQLITE_PATH=/path/to/northstar.db
```

This removes the previous hard blocker where the new north-star state existed only in process memory.

### 2. Session Spine Persistence
Updated `acosplatform/sessions/spine.py` so `resolve_or_create_session()` now:
- resolves sessions from durable identity index
- upserts sessions
- upserts active journeys
- stores message envelopes
- still preserves in-memory fallback for fast local tests

### 3. Evidence Persistence
Updated `acosplatform/evidence/store.py` so `record_evidence()` now persists evidence events durably while preserving the in-process fallback.

### 4. Optional Production API Guardrails
Added optional API-key protection for north-star pilot endpoints.

Set:

```bash
ACOS_NORTHSTAR_REQUIRE_AUTH=1
ACOS_NORTHSTAR_API_KEYS=key1,key2
```

Protected endpoints:
- `POST /api/northstar/messages`
- `GET /api/northstar/tools`

Local demos remain open unless the flag is enabled.

### 5. Optional MCP Server Guardrails
Added optional API-key protection for hosted MCP access.

Set:

```bash
ACOS_MCP_REQUIRE_AUTH=1
ACOS_MCP_API_KEYS=key1,key2
```

Protected endpoint:
- `POST /mcp`

### 6. Additional Hardening Tests
Added:

```text
harness/python/tests/northstar/test_sprint_hardening.py
```

Coverage added:
- durable session/message/evidence persistence
- north-star endpoint auth blocking
- MCP endpoint auth blocking

## Validation Evidence

### North-Star Tests

```text
8 passed
```

Command:

```bash
pytest -q harness/python/tests/northstar
```

### Golden Journey Smoke

```text
ACOS north-star smoke status: success
Intent: stock_availability
Agent: Inventory Agent
Tool calls: 4
Evidence events: 8
Response: For a winter wedding under £200, I recommend: Navy Satin Midi Dress (£89, 4 in Reading); Silver Wrap Shawl (£35, 8 in Reading); Black Block-Heel Court Shoes (£59, 3 in Reading).
```

Command:

```bash
python scripts/northstar_smoke.py
```

### Week 11/12 UAT and Gate Tests

```text
27 passed
```

Command:

```bash
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
```

### React Production Build

```text
vite build successful
```

Output:

```text
dist/index.html                   0.75 kB
dist/assets/index-BeuIl1Ek.css   51.38 kB
dist/assets/index-DANSAEsq.js   891.67 kB
✓ built
```

Known warning:

```text
Some chunks are larger than 500 kB after minification.
```

This is not a release blocker for pilot readiness but remains a frontend optimisation item.

### Full Legacy Harness

The full harness progressed but timed out in this sandbox before completion.

Observed progress before timeout:

```text
........................................................................ [15%]
................
```

This is still not a full GA certification.

### Docker Runtime

Docker is not installed in this sandbox:

```text
docker: command not found
```

Docker Compose runtime remains unproven in this environment.

## GA Readiness Movement

Previous state:
- north-star state was in-memory only
- endpoint guardrails were not present for north-star/MCP pilot surfaces
- limited hardening tests

Current state:
- durable SQLite-backed pilot state exists
- sessions, journeys, messages, and evidence persist
- auth can be enforced for north-star and MCP endpoints
- north-star/UAT/gate/UI validations pass

## Current Verdict

ACOS is now stronger as a **pilot-ready north-star platform foundation**.

It is still **not full enterprise GA** until these are completed:

1. Docker Compose runtime proof in a Docker-enabled environment.
2. Postgres migrations for north-star tables.
3. Tenant-scoped RBAC wired into GraphQL, MCP, and north-star APIs by default in production.
4. Full legacy harness completion without timeout.
5. Frontend bundle splitting.
6. MCP validation against target clients.
7. Cloud deployment smoke test.

## Recommended Next Sprint

**Sprint: Production Runtime Proof**

Focus:
- Postgres migration for north-star tables
- Docker-enabled Compose validation
- CI workflow for tests/build/smoke
- GraphQL RBAC enforcement
- MCP tenant-scoped auth
- Vercel/Render deployment proof
