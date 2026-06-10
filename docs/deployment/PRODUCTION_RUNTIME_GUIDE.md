# ACOS Production Runtime Guide

This guide describes the production runtime proof added in the Production Runtime + Studio Proof Sprint.

## Services

The production compose profile starts:

- `ops-api` on port `8081`
- `shopper-api` on port `8080`
- `chat-api` on port `8001`
- `mcp-server` on port `8090`
- `postgres` with base schema and north-star schema

## Required environment

Copy `.env.production.example` to `.env.production` and set strong secrets:

```bash
cp .env.production.example .env.production
```

Required secrets:

- `DB_PASSWORD`
- `OPS_JWT_SECRET`
- `CHAT_JWT_SECRET`
- `SHOPPER_API_KEYS`
- `ACOS_NORTHSTAR_API_KEYS`
- `ACOS_MCP_API_KEYS`
- `ALLOWED_ORIGINS`

## Static runtime check

```bash
python scripts/production_runtime_check.py
```

This verifies production files, key retail tools, and the golden journey without needing Docker.

## Docker runtime proof

Run this on a Docker-enabled machine or CI runner:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
curl -f http://localhost:8081/health
curl -f http://localhost:8090/health
python scripts/northstar_smoke.py
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

## Current limitation

The ChatGPT sandbox used for this sprint does not provide Docker, so compose runtime remains CI/machine-certified rather than sandbox-certified.

## North-Star DB migrations

This build includes Alembic migrations for the north-star runtime tables.

```bash
export DATABASE_URL=postgresql://acos:<password>@<host>:5432/acos
make db-migrate
```

To review SQL without applying it:

```bash
make db-migrate-sql
```

The first migration creates the north-star session, journey, message, evidence,
outbox, replay, and API-key metadata tables.

## North-Star RBAC and tenant isolation

Enable guardrails in production:

```bash
ACOS_NORTHSTAR_REQUIRE_AUTH=1
ACOS_GRAPHQL_REQUIRE_AUTH=1
ACOS_MCP_REQUIRE_AUTH=1
ACOS_NORTHSTAR_API_KEYS=admin-key:default:admin|ops|analyst|viewer,viewer-key:default:viewer
ACOS_MCP_API_KEYS=mcp-key:default:admin|ops
```

Key format:

```text
key:tenant:role|role2
```

Non-admin keys are restricted to their configured tenant. Write operations require
`admin` or `ops`.

## Postgres north-star store

Use Postgres instead of SQLite:

```bash
ACOS_NORTHSTAR_STORE=postgres
DATABASE_URL=postgresql://acos:<password>@db:5432/acos
```

SQLite remains the default for local development and test runs.

## Optional Redis fast path

Redis is optional and used for hot session/journey lookups. The app works without it.

```bash
ACOS_REDIS_ENABLED=1
REDIS_URL=redis://redis:6379/0
```

The production compose file includes a Redis service, but `ACOS_REDIS_ENABLED` controls whether the app uses it.

## Replay proof

North-star runs now capture replay snapshots. APIs:

```text
GET  /api/northstar/replays
GET  /api/northstar/replays/{replay_id}
POST /api/northstar/replays/{replay_id}/rerun
```

The Studio Proof screen includes a Replay Proof card.
