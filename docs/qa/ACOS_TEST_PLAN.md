# ACOS Test Plan

## Fast local proof

```bash
make test-northstar
make smoke-northstar
make runtime-check
make ui-build
```

## Backend tests

```bash
pytest -q harness/python/tests/northstar
pytest -q harness/python/tests/test_week11_uat_and_production_gate.py
```

## Database migration proof

```bash
alembic upgrade head --sql
```

Then run against Postgres in a Docker-enabled environment:

```bash
DATABASE_URL=postgresql://acos:acos@localhost:5432/acos alembic upgrade head
```

## UI proof

```bash
cd apps/ops_ui_v2
npm ci
npm run build
```

Manual UI checks:

- `/ui/demo-guide` renders demo storyboard and commands.
- `/ui/studio-proof` runs the retail journey and shows agents/tools/evidence.
- `/ui/test-center` lists all checks and runs a smoke journey.

## API proof

```bash
curl http://localhost:8000/api/northstar/demo-script
curl http://localhost:8000/api/northstar/test-plan
curl -X POST http://localhost:8000/api/northstar/messages \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id":"default","channel":"web","channel_user_id":"demo","text":"I need an outfit for a winter wedding under £200, available for pickup near Reading"}'
```

## Production runtime proof

```bash
docker compose -f docker-compose.prod.yml up --build
```

Expected services:

- ops-api
- shopper-api
- chat-api
- mcp-server
- postgres
- redis

## Acceptance criteria

- North-star tests pass.
- Golden journey smoke succeeds.
- UI builds.
- Alembic SQL renders.
- Production runtime static check passes.
- Docker Compose runs successfully in an external Docker-enabled runtime.
