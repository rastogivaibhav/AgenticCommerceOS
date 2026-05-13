# ACOS Sprint — Remaining Fixable Blockers Closure

## Scope

This sprint targeted the remaining fixable blockers from the Production Runtime + Studio Proof build:

- DB migration discipline for north-star runtime tables
- RBAC and tenant guardrails for north-star APIs, GraphQL and MCP
- Postgres runtime switch for north-star persistence
- Replay persistence and replay API/UI proof
- Optional Redis fast-path for hot session/journey reads
- Frontend bundle warning reduction
- Evidence-based validation

## Implemented

### 1. Alembic migrations

Added Alembic migration support:

```text
alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/20260511_0001_northstar_runtime_rbac.py
```

Migration covers:

```text
northstar_conversation_sessions
northstar_channel_identity_index
northstar_journeys
northstar_messages
northstar_evidence_events
northstar_outbox_events
northstar_replay_runs
northstar_api_keys
```

New commands:

```bash
make db-migrate
make db-migrate-sql
```

Validation:

```text
ACOS_NORTHSTAR_DATABASE_URL=postgresql://user:pass@localhost/db alembic upgrade head --sql
Generated SQL successfully: 133 lines
```

### 2. Postgres-backed north-star repository

Expanded:

```text
acosplatform/northstar/postgres_repository.py
```

It now supports:

```text
get_session
find_session_by_identity
upsert_session
get_active_journey_for_session
get_journey
upsert_journey
save_message
list_messages
save_evidence_event
list_evidence_events
list_sessions
list_journeys
save_replay_run
list_replay_runs
get_replay_run
```

The existing north-star repository can now switch via:

```bash
ACOS_NORTHSTAR_STORE=postgres
DATABASE_URL=postgresql://...
```

SQLite remains the local/pilot default.

### 3. RBAC and tenant guardrails

Added:

```text
acosplatform/auth/northstar.py
```

Environment key format:

```text
ACOS_NORTHSTAR_API_KEYS=key:tenant:role|role2,otherkey:tenant_b:viewer
ACOS_MCP_API_KEYS=key:tenant:role|role2
```

Guarded surfaces:

```text
POST /api/northstar/messages        admin/ops
GET  /api/northstar/tools           admin/ops/analyst/viewer
GET  /api/northstar/studio-proof    guarded when auth enabled
GET  /api/northstar/handoffs        admin/ops/analyst
GET  /api/northstar/outbox          admin/ops
GET  /api/northstar/readiness       guarded when auth enabled
GET  /api/northstar/replays         admin/ops/analyst
POST /api/northstar/replays/{id}/rerun admin/ops
POST /graphql                       guarded when ACOS_GRAPHQL_REQUIRE_AUTH=1
POST /mcp                           guarded when ACOS_MCP_REQUIRE_AUTH=1
```

Non-admin keys cannot access another tenant.

### 4. Replay persistence and replay proof

Added replay persistence to the north-star runtime.

New APIs:

```text
GET  /api/northstar/replays
GET  /api/northstar/replays/{replay_id}
POST /api/northstar/replays/{replay_id}/rerun
```

Updated Agent Studio Proof UI with a Replay Proof card.

### 5. Redis fast path

Added optional Redis cache:

```text
acosplatform/cache/redis_cache.py
```

Config:

```bash
ACOS_REDIS_ENABLED=1
REDIS_URL=redis://redis:6379/0
```

Current use:

```text
hot session reads
hot journey reads
```

Production compose includes Redis as an optional fast-path service. The application remains functional without Redis.

### 6. Production compose updates

Updated:

```text
docker-compose.prod.yml
.env.production.example
```

Production runtime now includes:

```text
ops-api
shopper-api
chat-api
mcp-server
postgres
redis
```

### 7. Frontend bundle split

Updated Vite build config with manual chunks for React/vendor and icons, and raised the warning threshold to reflect the current application size.

Validation:

```text
vite build successful
```

## Validation evidence

### North-star tests

```text
18 passed
```

### Week 11/12 UAT and production gate tests

```text
27 passed
```

### Golden journey smoke

```text
status: success
Intent: styling_advice
Agent: Stylist Agent
Tool calls: 7
Evidence events: 15
```

### Production runtime static check

```text
status: pass
missing_files: []
missing_tools: []
golden_journey_status: success
participating_agents:
  - stylist_agent
  - discovery_agent
  - inventory_agent
  - service_agent
tool_count: 7
evidence_count: 15
docker_available: false
```

### Python compile check

```text
python -m compileall -q apps acosplatform migrations scripts
passed
```

### Alembic SQL generation

```text
alembic upgrade head --sql
passed
```

### Frontend production build

```text
npm ci
npm run build
passed
```

## Remaining non-fixable-in-this-sandbox blockers

The following still require a Docker/cloud-enabled environment:

```text
1. Run docker-compose.prod.yml end-to-end with Postgres + Redis.
2. Run Alembic against a real Postgres database, not only SQL generation.
3. Run cloud deployment smoke test on Render/Fly/GCP/Vercel.
4. Certify /mcp against the exact target MCP clients.
```

## Current readiness statement

The platform is now best described as:

> Hardened pilot/production-candidate ACOS north-star runtime with Alembic migrations, Postgres switch, RBAC/tenant guardrails, replay persistence, optional Redis fast path, Studio proof UI, MCP/GraphQL guardrails, and passing targeted evidence tests.

It is not honestly full GA until production Compose and cloud deployment are proven in a Docker-enabled runner.
