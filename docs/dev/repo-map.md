# Repository Map

This map is the source of truth for what is current, what is supporting evidence, and what is intentionally legacy. It exists to keep the developer experience clean while preserving useful demo and validation assets.

## Current Product Surface

- `apps/ops_api/` - canonical FastAPI control plane used by the operations UI and hardening tests.
- `apps/ops_ui_v2/` - canonical React/Vite operator experience.
- `apps/shopper_api/` - shopper-facing API surface for demo and journey flows.
- `apps/chat_api/` - chat workflow API surface and adapters.
- `apps/retail_mock_api/` - local mock retail backend for demos and integration checks.
- `apps/mcp_server/` - MCP entry point for tool-facing workflows.
- `acosplatform/` - shared platform modules: governance, tools, workflows, tenancy, auth, observability, hardening, replay, and integrations.
- `integrations/` - external connector clients and adapter runtimes.
- `harness/` - Python and Playwright tests for backend, UI, integration, and northstar hardening.
- `deploy/` - Kubernetes, observability, tenant-network, and evidence assets.
- `migrations/` and `db/` - database migrations and schemas.

## Documentation And Evidence

- `docs/architecture/` - reference architecture and operating-model docs.
- `docs/product/` - product plans, PRDs, and readiness journey.
- `docs/demo/` - runnable demo guides and runbooks.
- `docs/deployment/` - production runtime guidance.
- `docs/observability/`, `docs/release/`, and `deploy/**/evidence/` - retained release, readiness, and operational evidence.
- `docs/archive/` - historical planning artifacts that should not appear as active work areas.

## Developer Entry Points

- `README.md` - current project overview and quick start.
- `run_demo_suite.py` - root-level convenience launcher for the high-fidelity demo stack.
- `scripts/` - operational checks, readiness scripts, smoke tests, and helper utilities.
- `scripts/live_checks/` - optional live-provider checks that require external credentials or services.
- `scripts/legacy/` - retained one-off demo experiments and historical scripts.

## Legacy Or Transitional Areas

- `ops_api/` - older shopping-chat FastAPI implementation retained because tests still cover it. Treat `apps/ops_api/` as canonical for new control-plane work.
- `legacy/` - preserved demo assets that are useful for reference but are not part of the main runtime path.
- `docs/superpowers/` - historical plans and specs that are retained as documentation rather than active workspace state.

## Generated Files Not To Commit

Keep generated logs, coverage files, Playwright reports, Vite output, and local vendor drops out of Git. The root `.gitignore` covers the common outputs from local validation runs.
