# Agentic Commerce OS (ACOS)

ACOS is a governed control plane for agentic retail and service operations. It
coordinates customer-facing channels, agent runtimes, deterministic tools,
operator workflows, evidence capture, and production-readiness reporting.

This repository's `main` branch is the canonical codebase. Older local snapshots
may contain additional demos and experimental routers; those are being ported
back as focused review branches instead of being copied wholesale over `main`.

## Current Status

As of June 27, 2026:

- Phase 1-7 hardening gates are merged into `main` through PR #9.
- The production runtime check passes locally and writes
  `docs/release/production-runtime-check.json`.
- The north-star Python test suite passed before merge: `40 passed`.
- Ops UI production build passed before merge.
- Spree ecommerce demo assets are staged separately in draft PR #10.
- Ops approval/workflow/run/promotion/incident assets are staged separately in
  draft PR #11.

The platform is locally verified with external blockers. It is not yet
procurement-certified for a specific buyer environment until live connector,
identity-provider, compliance, operator-UAT, deployment, and paid-pilot evidence
is supplied.

## What Is In `main`

- Shopper, Ops, Chat, MCP, and north-star API surfaces.
- A modular Ops API with north-star and v2 control-plane routers.
- Deterministic golden retail journey execution for local validation.
- Evidence, replay, tenant, RBAC, GraphQL, MCP, and runtime-readiness surfaces.
- Phase 1-7 hardening gate reporting.
- Tool policy evaluation for high-risk tool calls.
- Connector certification and business outcome KPI contracts.
- Docker Compose assets for local and production-like runtime checks.

## What Is Not Yet In `main`

The following local-only assets are intentionally staged as separate draft PRs:

- PR #10: Spree ecommerce demo, enhanced Spree Store API client, webhook ingress,
  demo compose/env/scripts/docs, Playwright demo, and Spree tests.
- PR #11: Ops approval, workflow, run, promotion, and incident-response routers
  plus their UAT fixture package.

Those PRs are additive and deliberately do not overwrite the newer modular Ops
API structure in `main`.

## Architecture

ACOS is organized around a governed runtime loop:

1. Customer channels send requests to the Shopper API.
2. The ACOS orchestration runtime routes the journey across specialist agents.
3. Agents call deterministic tools through the tool registry, MCP, or existing
   commerce/service APIs.
4. Evidence, replay records, policy verdicts, and tenant context are captured
   for audit and incident response.
5. The Ops API and Ops UI expose governance, readiness, replay, GraphQL, and
   control-plane views.
6. Hardening reports summarize what is locally verified and what still requires
   external buyer-environment evidence.

## Core Components

- `apps/ops_api`: governed control-plane API, north-star APIs, GraphQL, RBAC,
  readiness, replay, and v2 surfaces.
- `apps/ops_ui_v2`: React-based Ops UI.
- `apps/shopper_api`: shopper-facing runtime entrypoint.
- `apps/chat_api`: chat/channel API.
- `apps/mcp_server`: MCP tool surface.
- `acosplatform/orchestration`: deterministic multi-agent journey runtime.
- `acosplatform/tools`: tool registry, execution, and policy enforcement.
- `acosplatform/hardening`: Phase 1-7 readiness gate reporting.
- `acosplatform/connectors`: connector certification contracts.
- `acosplatform/outcomes`: pilot KPI and business outcome contracts.
- `db`, `migrations`: schema and Alembic migration support.
- `harness`: Python and Playwright validation assets.

## Quick Start

```bash
git clone https://github.com/rastogivaibhav/AgenticCommerceOS.git
cd AgenticCommerceOS
cp .env.example .env
docker compose up --build
```

Default local endpoints from `docker-compose.yml`:

- Shopper API: `http://localhost:8080`
- Ops API: `http://localhost:8081`
- Chat API: `http://localhost:8001`
- Postgres: `127.0.0.1:5432`

The production-like compose file uses different ports:

- Ops API: `http://localhost:8000`
- Ops UI: `http://localhost:3001`
- Shopper API: `http://localhost:9005`
- Retail mock API: `http://localhost:9006`

## Local Verification

Useful verification commands:

```bash
python -m pytest harness/python/tests/northstar -q
python scripts/production_runtime_check.py
alembic upgrade head --sql
npm --prefix apps/ops_ui_v2 ci
npm --prefix apps/ops_ui_v2 run build
```

The runtime checker reports:

- Golden journey status.
- Participating agents.
- Tool and evidence counts.
- Alembic migration availability.
- Redis/runtime configuration posture.
- Phase 1-7 hardening gate status.

## Hardening Reality

Locally verified phases in the merged hardening report:

- Phase 1: Enterprise identity, RBAC, and secure defaults.
- Phase 2: Tenant isolation and data boundaries.
- Phase 5: Workflow Studio and operator UX API surface.
- Phase 6: Production runtime and deployment certification assets.
- Phase 7: Business outcome proof contract.

Partial phases requiring external evidence:

- Phase 3: Connector certification. A live commerce connector must be certified
  with credentials, webhooks, idempotency, and failure drills.
- Phase 4: Policy, risk, and compliance. Buyer-specific PII, PCI, DLP, retention,
  legal-hold, and model-risk controls must be mapped and tested.

External blockers still required for procurement-grade certification:

- Buyer SSO/OIDC/SAML integration.
- Negative tenant-isolation tests against real Postgres/RLS.
- Live connector certification.
- Compliance-control mapping.
- Operator UAT for promotion, pause, rollback, and incident handling.
- Target-infrastructure deployment, backup/restore, load, and DR testing.
- Paid-pilot KPI measurement.

## Known Residuals

- `npm --prefix apps/ops_ui_v2 test -- --run` has test drift against current UI
  copy and API assumptions.
- `npm --prefix apps/ops_ui_v2 audit --audit-level=moderate` still reports
  Monaco -> DOMPurify moderate advisories that `npm audit fix` cannot resolve
  under the current dependency range.
- Spree demo and Ops workflow assets are not mounted in `main` yet; they are in
  draft PRs for focused review.

## Development Notes

- Keep `main` canonical.
- Port local-only work in focused branches.
- Avoid copying the local monolithic `apps/ops_api/main.py` over the remote
  modular API.
- Distinguish local verification from live buyer certification.
- Prefer deterministic tool execution for money, inventory, and customer
  commitments.

## License

Licensed under Apache 2.0. See [LICENSE](./LICENSE).
