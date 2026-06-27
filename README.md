# Agentic Commerce OS

Agentic Commerce OS (ACOS) is a governed control plane for agentic retail and service operations. It is designed to let commerce teams orchestrate AI-assisted journeys while keeping money movement, inventory changes, customer commitments, approvals, audit, and rollback deterministic.

The current repository is organized around the production-shaped platform under `apps/`, `acosplatform/`, `integrations/`, `harness/`, `deploy/`, and `docs/`. Historical demos and optional live-provider checks are retained, but they are now marked separately so contributors can tell what is current.

## Current System

- `apps/ops_api/` - canonical FastAPI control plane for operators.
- `apps/ops_ui_v2/` - canonical React/Vite operator UI.
- `apps/shopper_api/` - shopper-facing journey API.
- `apps/chat_api/` - chat workflow API and adapters.
- `apps/retail_mock_api/` - local mock retail backend for demos and integration checks.
- `apps/mcp_server/` - MCP entry point for tool-facing workflows.
- `acosplatform/` - shared platform modules for workflows, tools, governance, tenancy, auth, observability, hardening, replay, and integrations.
- `integrations/` - connector clients and adapter runtimes.
- `harness/` - Python and Playwright tests.
- `deploy/` - Kubernetes, observability, multi-tenant, and evidence assets.

For a fuller folder-by-folder guide, see [docs/dev/repo-map.md](docs/dev/repo-map.md).

## Architecture

ACOS uses a hub-and-spoke operating model:

1. Customer channels such as web, WhatsApp, Slack, or partner apps call shopper and chat APIs.
2. ACOS routes journeys through governed workflow and orchestration services.
3. Tool execution is policy-checked, auditable, and deterministic for high-risk actions.
4. Operators use the control plane to inspect runs, approve workflows, replay traces, and monitor outcomes.
5. External commerce systems such as OMS, ERP, CRM, payment, and catalog providers are reached through connectors or MCP-style tools.

## Why It Matters

- Deterministic execution around orders, payments, inventory, refunds, and customer promises.
- Human approval and policy gates for high-risk workflow promotion.
- Replayable audit traces for incidents, compliance, and enterprise review.
- Extensible connector/runtime model for existing APIs, MCP tools, and agent providers.
- Operator-first UI for governance, evaluation, routing, FinOps, and production readiness.

## Quick Start

```bash
git clone https://github.com/rastogivaibhav/AgenticCommerceOS.git
cd AgenticCommerceOS
cp .env.example .env
docker compose up --build -d
python bootstrap.py
```

The main local operator entry point is `http://localhost:8000/ui/`.

For the high-fidelity local demo stack:

```bash
python run_demo_suite.py
```

## Development Checks

```bash
python -m pytest harness/python/tests/northstar -q
python -m pytest harness/python/tests -q
npm --prefix apps/ops_ui_v2 install
npm --prefix apps/ops_ui_v2 run build
```

Some live checks under `scripts/live_checks/` require external credentials or running provider services and are not part of the default local path.

## Repository Hygiene

Generated coverage files, Playwright reports, Vite logs, local vendor drops, and ad hoc output files should not be committed. Legacy or exploratory assets belong under `legacy/`, `scripts/legacy/`, or `docs/archive/`.

## Documentation

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - documentation map.
- [API.md](API.md) - API contracts and examples.
- [TESTING.md](TESTING.md) - test strategy and commands.
- [SECURITY.md](SECURITY.md) - security posture and vulnerability reporting.
- [CONTRIBUTING.md](CONTRIBUTING.md) - contribution guidance.

## License

Apache 2.0. See [LICENSE](LICENSE).
