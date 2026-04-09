# ACOS Control Plane
### Agentic commerce runtime + governed operations plane

[![GitHub Repo](https://img.shields.io/badge/GitHub-AgenticCommerceOS-181717?logo=github)](https://github.com/rastogivaibhav/AgenticCommerceOS)
[![Stars](https://img.shields.io/github/stars/rastogivaibhav/AgenticCommerceOS?style=social)](https://github.com/rastogivaibhav/AgenticCommerceOS/stargazers)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](./LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.0-blue)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)](https://www.python.org/)
[![Docker Compose](https://img.shields.io/badge/docker%20compose-ready-2496ED)](./docker-compose.yml)

ACOS is for teams running **AI-powered commerce journeys** in production, where approvals, rollback, tenant controls, and incident response are non-negotiable.

## Why This Exists
If this looked like n8n, that is on us.

ACOS is **not** a generic automation canvas.
It is an **agentic commerce system** with:
- a dedicated shopper runtime (`shopper-api`) for journey execution,
- and a dedicated ops plane (`ops-api`) for governance and release control.

What ACOS solves:
- Commerce journeys need domain contracts (`/v1/journey`), not generic node chaining.
- Promotions need approval + audit + rollback, not ad-hoc scripts.
- Operators need run-level investigation tied to workflow versions.
- Multi-tenant traffic needs hard limits to prevent noisy-neighbor failure.

## What You Can Do With It
- Execute customer journeys on `shopper-api` via `/v1/journey` with API-key auth.
- Manage workflow lifecycle in `ops-api`: draft, approve, promote, rollback, archive.
- Enforce role-based governance for high-risk operations.
- Track runs, inspect timelines, replay, and investigate incidents.
- Capture immutable audit records for control-plane mutations.
- Apply tenant rate limits, quotas, and in-flight caps.
- Generate production gate evidence artifacts for go/no-go decisions.

## Architecture (High-Level)
ACOS separates runtime execution from operations governance.

```text
                 +-----------------------------+
                 |       Ops UI (React)        |
                 | served by ops-api (/ui)     |
                 +--------------+--------------+
                                |
                                v
+-------------------+   +-------------------+   +-------------------+
| shopper-api :8080 |   |   ops-api :8081   |   |   chat-api :8001  |
| /v1/journey       |   | workflow governance|   | channel bridge    |
| X-API-Key auth    |   | approvals + audit  |   | slack/chat        |
+---------+---------+   +---------+---------+   +---------+---------+
          \____________________|___________________________/
                               v
                    +------------------------+
                    | PostgreSQL (db:5432)   |
                    | workflows/runs/audit   |
                    +------------------------+
```

Core packages in `acosplatform/`: `journey`, `workflows`, `governance`, `audit`, `observability`, `tenancy`, `replay`, `db`.

## Quick Start (CRITICAL)
Run ACOS locally and hit both runtime and ops endpoints.

```bash
git clone https://github.com/rastogivaibhav/AgenticCommerceOS.git
cd AgenticCommerceOS
cp .env.example .env
# Windows PowerShell: copy .env.example .env

docker compose up --build -d
```

Verify services:

```bash
curl http://localhost:8080/health   # shopper runtime
curl http://localhost:8081/health   # ops control plane
```

Open ops UI:
- http://localhost:8081/ui/

Mint an ops token for examples:

```bash
python scripts/mint_dev_jwt.py --role admin --secret "$OPS_JWT_SECRET"
```

## Example Usage
Run a shopper journey (runtime plane):

```bash
curl -X POST http://localhost:8080/v1/journey \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <SHOPPER_API_KEY>" \
  -d '{
    "tenant_id": "default",
    "workflow_family": "discovery",
    "message": "I need running shoes under 120",
    "customer_id": "cust_123"
  }'
```

List workflows (ops plane):

```bash
curl -X GET http://localhost:8081/api/v1/workflows \
  -H "Authorization: Bearer <OPS_TOKEN>"
```

Promote a workflow version:

```bash
curl -X POST http://localhost:8081/api/v1/workflows/wf_discovery_primary/versions/v3/promote \
  -H "Authorization: Bearer <OPS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_environment": "prod",
    "source_environment": "stage",
    "approval_note": "Approved for bounded pilot cutover"
  }'
```

Fetch audit verification:

```bash
curl -X GET "http://localhost:8081/api/audit?workflow_id=wf_discovery_primary" \
  -H "Authorization: Bearer <OPS_TOKEN>"
```

## Core Concepts
| Concept | Meaning | Why it matters |
|---|---|---|
| Workflow | Versioned definition of behavior | Safe change management |
| Version | Immutable revision | Predictable promotion + rollback |
| Run | Execution instance tied to workflow version | Fast root-cause analysis |
| Promotion | Controlled environment transition | Release governance |
| Approval | Role-gated authorization | Risk control |
| Audit Event | Immutable operation record | Compliance and traceability |
| Tenant Controls | Per-tenant throughput boundaries | Noisy-neighbor isolation |
| Evidence Pack | Artifact + runbook + sign-off record | Defensible go-live decisions |

## Integrations / Extensibility
- MCP-compatible product and capability connectors.
- Slack/chat channel bridging through `chat-api`.
- Stripe-compatible payment workflows in shopper flows.
- Optional AgentFabric hooks via environment configuration.
- Pluggable domain components under `acosplatform/plugins/`.

## Real Use Cases
- Retail operations control plane with approval-backed promotions and rollback.
- Post-purchase service automation with policy-aware escalation.
- Incident-ready AI operations with run timeline investigation and replay.
- Pilot go-live governance with objective evidence artifacts and sign-off records.
- Tenant-safe scale-up with hard quota and concurrency boundaries.

## Configuration
Use `.env.example` as the source of truth.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | - | Postgres connection string |
| `DB_PASSWORD` | Yes | - | DB credential for local compose |
| `SHOPPER_API_KEYS` | Yes | - | Shopper API auth keys |
| `OPS_JWT_SECRET` | Yes | - | Ops JWT signing secret |
| `ALLOWED_ORIGINS` | Yes | - | CORS allowlist |
| `ALLOW_INSECURE_DEV_AUTH` | No | `0` | Dev-only auth fallback |
| `TENANT_RATE_LIMIT_PER_MINUTE` | No | `120` | Per-tenant minute limit |
| `TENANT_DAILY_QUOTA` | No | `5000` | Per-tenant daily quota |
| `TENANT_MAX_IN_FLIGHT` | No | `8` | Per-tenant concurrency cap |
| `GOOGLE_API_KEY` | No | empty | Optional model provider key |
| `AGENTFABRIC_URL` | No | empty | Optional external agent fabric |
| `AGENTFABRIC_API_KEY` | No | empty | Optional external auth key |
| `SLACK_BOT_TOKEN` | No | empty | Chat API Slack integration |
| `SLACK_SIGNING_SECRET` | No | empty | Slack request validation |
| `SLACK_WORKSPACE_ID` | No | `default` | Workspace routing key |

## Security / Governance (if relevant)
ACOS is designed for controlled AI operations:
- RBAC enforcement on operational endpoints.
- Audit coverage for workflow and tenant mutations.
- Tenant-level traffic controls to reduce blast radius.
- Operational runbooks for go-live, promotions, rollback, and incidents.
- Evidence-driven release gates with machine-readable artifacts.

Operational guidance:
1. Keep `ALLOW_INSECURE_DEV_AUTH=0` outside local development.
2. Rotate `OPS_JWT_SECRET` and API keys regularly.
3. Keep `ALLOWED_ORIGINS` restricted to known domains.
4. Treat production gate artifacts as release records.

## Roadmap
Near-term:
- Canonical index for production evidence artifacts.
- Sign-off workflow in the ops UI.
- Expanded cross-tenant incident diagnostics.
- Automated first-week KPI post-cutover reporting.

Long-term:
- Deeper multi-tenant policy isolation.
- Progressive rollout strategies by workflow family.
- Broader connector ecosystem for enterprise systems of record.
- Extensibility model for third-party workflow capabilities.

## Contributing
Contributions are welcome from operators, backend engineers, frontend engineers, and platform teams.

1. Fork and create a branch.
2. Make focused changes with tests.
3. Run checks:
   - `python scripts/week12_production_gate_checker.py`
   - `python -m pytest tests/test_week12_production_gate_checker.py -q`
4. Open a PR with problem statement, implementation summary, and evidence.

See also:
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- [SECURITY.md](./SECURITY.md)

## License
Apache License 2.0. See [LICENSE](./LICENSE).
