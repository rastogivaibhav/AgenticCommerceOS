# North-Star Persistence and Auth Hardening

## Runtime persistence

The north-star runtime now persists pilot state through `acosplatform/northstar/repository.py`.

Default local database:

```bash
var/acos_northstar.db
```

Override path:

```bash
ACOS_NORTHSTAR_SQLITE_PATH=/secure/path/acos_northstar.db
```

Persisted objects:

- conversation sessions
- channel identity index
- journeys
- messages
- evidence events

The SQLite repository is the default pilot implementation. For Postgres-backed deployments, use `db/northstar_schema.sql` as the migration baseline and replace the repository adapter behind the same interface.

## North-star endpoint auth

Local demos are open by default. To enforce API-key auth:

```bash
ACOS_NORTHSTAR_REQUIRE_AUTH=1
ACOS_NORTHSTAR_API_KEYS=key1,key2
```

Protected endpoints:

- `POST /api/northstar/messages`
- `GET /api/northstar/tools`

Header:

```http
X-API-Key: key1
```

## Hosted MCP auth

Local MCP tests are open by default. To enforce API-key auth:

```bash
ACOS_MCP_REQUIRE_AUTH=1
ACOS_MCP_API_KEYS=key1,key2
```

Protected endpoint:

- `POST /mcp`

Header:

```http
X-API-Key: key1
```

## Production posture still required

Before full GA:

1. Make auth required by default when `OPS_ENVIRONMENT` is not local/dev/test.
2. Replace local SQLite with Postgres-backed repository implementation.
3. Apply tenant isolation through `app.tenant_id` and Postgres RLS.
4. Add signed MCP client credentials per tenant/tool server.
5. Add audit-backed key rotation and revocation.
