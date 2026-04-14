# ACOS Investment Implementation Plan
## Investor diligence follow-through and production hardening sequence

**Date:** April 14, 2026
**Audience:** Technology diligence reviewers, platform leadership, investment committee
**Status:** Proposed implementation plan grounded in the current codebase

---

## 1. Executive Intent

The current ACOS repository already demonstrates a real product direction:
- governed workflow registry and promotion model
- shopper runtime, ops control plane, and chat gateway separation
- connector-backed commerce/service paths
- React operator UI with meaningful workflow, channel, and agent surfaces

The investment question is not whether there is a real product. There is.
The question is whether the platform can be made production-credible without a rewrite.

This plan assumes the right strategy is:
1. preserve the current architecture,
2. remove critical trust-boundary risks first,
3. harden tenant isolation and operational truthfulness,
4. then scale reliability, security, and deployment maturity.

---

## 2. Current Investment Position

### Strengths worth backing
- Clear product identity as an agentic commerce runtime plus governed operations plane.
- Working service topology across `shopper-api`, `ops-api`, `chat-api`, and `ops_ui_v2`.
- Real workflow/version/promotion concepts already implemented.
- Real connectors and live-vs-preview behavior already present for WhatsApp, Telegram, Shopify, and Salesforce.
- Strong implementation velocity with evidence of iterative improvement rather than static scaffolding.

### Risks that currently block production-grade confidence
1. Unauthenticated execution surface in `chat-api`.
2. Tenant isolation is declared in schema but not consistently enforced in code paths.
3. Workflow decision rules currently rely on Python `eval()`.
4. Persistence and analytics can silently fall back to in-memory or static demo data.
5. Channel delivery semantics still blur preview success and live failure.
6. Deployment and identity model are still local/dev-centric rather than enterprise-ready.

---

## 3. Implementation Principles

1. Do not rewrite the platform.
2. Keep the three-service topology intact.
3. Preserve the ops UI and workflow model as the control-plane core.
4. Make security and tenant correctness non-optional at runtime.
5. Separate demo continuity from production truth.
6. Add deployment maturity only after trust boundaries are fixed.

---

## 4. Workstreams

### Workstream A: Trust Boundaries and Authentication
**Goal:** remove externally reachable unauthenticated execution paths.

Scope:
- Add explicit auth for `chat-api` message and workflow execution routes.
- Verify Slack signature on Slack-originated events.
- Introduce service-to-service auth for internal calls.
- Add environment validation for `chat-api` equivalent to `shopper-api` and `ops-api`.

Code areas:
- `apps/chat_api/main.py`
- `apps/chat_api/routers/message.py`
- `apps/chat_api/routers/workflows.py`
- `apps/chat_api/config.py`

Exit criteria:
- No workflow execution endpoint is callable anonymously.
- Slack-originated traffic is signature-validated.
- Non-dev startup fails with unsafe auth configuration.

### Workstream B: Tenant Isolation Enforcement
**Goal:** make tenant boundaries real in runtime behavior, not only in schema intent.

Scope:
- Replace generic `transaction()` usage with `tenant_transaction()` where tenant-scoped data is read or written.
- Tighten RLS policies so missing `app.tenant_id` denies by default.
- Pass explicit tenant context through repository functions that currently operate globally.
- Add multi-tenant regression tests around runs, context, channels, CRM, and workflows.

Code areas:
- `acosplatform/db/connection.py`
- `acosplatform/db/repository.py`
- `acosplatform/context/store.py`
- workflow, channel, and CRM callers across `apps/ops_api` and `acosplatform/*`
- `db/schema.sql`

Exit criteria:
- Tenant-scoped data paths always set `app.tenant_id`.
- RLS cannot be bypassed by unset session context.
- Cross-tenant leakage tests fail before fix and pass after fix.

### Workstream C: Safe Workflow Rule Execution
**Goal:** remove unsafe dynamic evaluation from workflow graphs.

Scope:
- Replace `eval()` in decision nodes with a constrained expression interpreter.
- Support only an allowlisted rule grammar such as:
  - `order_found`
  - `customer_found`
  - `confidence > 0.7`
  - boolean `and` / `or` / `not`
- Validate rules at save-time in the workflow designer and at execute-time in the backend.

Code areas:
- `acosplatform/workflows/executor.py`
- `apps/ops_api/main.py`
- `apps/ops_ui_v2/src/components/*` workflow config surfaces

Exit criteria:
- No execution path uses Python `eval()` on workflow-authored content.
- Invalid rules are rejected with actionable operator feedback.

### Workstream D: Truthful Persistence, Analytics, and Fallback Handling
**Goal:** ensure operator-visible state is trustworthy during partial outages.

Scope:
- Distinguish clearly between:
  - live persisted state
  - degraded read-only state
  - demo/static fallback state
- Prevent write-like behavior from silently succeeding in memory when DB is unavailable for production-facing flows.
- Keep demo mode, but force it to be explicit and operator-visible.
- Add provenance headers and persistence health markers to key endpoints beyond analytics.

Code areas:
- `acosplatform/db/repository.py`
- `apps/ops_api/routers/analytics.py`
- `apps/ops_api/main.py`
- `apps/ops_ui_v2/src/store/*`

Exit criteria:
- Operators can always tell whether data is live, degraded, or demo-backed.
- Production-mode writes fail explicitly if persistence is unavailable.
- Demo continuity remains usable only when selected or clearly labeled.

### Workstream E: Channel Reliability and Live Connector Semantics
**Goal:** make messaging channels operationally trustworthy.

Scope:
- Make live send failures first-class failures, not `status=ok` previews.
- Add retry policy, timeout classification, and audit outcomes for WhatsApp and Telegram sends.
- Improve run correlation between inbound webhooks, workflow runs, and outbound responses.
- Add connector health dashboards and troubleshooting surfaces.

Code areas:
- `integrations/whatsapp/client.py`
- `integrations/telegram/client.py`
- `acosplatform/retail_ops/service.py`
- `apps/ops_api/main.py`
- `apps/ops_ui_v2/src/pages/Channels.jsx`

Exit criteria:
- Failed live sends are visible as failures.
- Inbound-to-run-to-reply correlation is audit-traceable.
- Channel readiness has an operator runbook and testable checks.

### Workstream F: Deployment and Production Platform Maturity
**Goal:** move from local-compose posture to investable production posture.

Scope:
- Introduce environment-specific deployment manifests.
- Externalize secrets and service config from `.env`-centric local assumptions.
- Add Postgres migration discipline instead of schema-on-start as the main production mechanism.
- Add centralized observability, alerting, and deployment verification.
- Define production identity model for ops users, service principals, and channel webhooks.

Code areas:
- `docker-compose.yml`
- deployment manifests and scripts to be added under `deploy/`
- startup validation modules
- CI/CD pipeline definitions to be added

Exit criteria:
- Production deploy path does not depend on dev flags or bootstrap shortcuts.
- Schema changes are migration-driven.
- Secrets are managed outside repo-local env files.

---

## 5. Recommended Delivery Sequence

### Phase 1: Investment Protection Sprint
**Duration:** 2-3 weeks
**Objective:** eliminate issues that would materially weaken technical diligence.

Includes:
1. Workstream A: trust boundaries and authentication
2. Workstream B: tenant isolation enforcement
3. Workstream C: safe workflow rule execution

Decision gate:
- Do not position the platform as enterprise-ready before this phase is complete.

### Phase 2: Operational Truth and Channel Hardening
**Duration:** 2-4 weeks
**Objective:** make the control plane trustworthy during real operations.

Includes:
1. Workstream D: truthful persistence and analytics
2. Workstream E: channel reliability and connector semantics

Decision gate:
- At the end of this phase, the product can credibly support a controlled pilot with real operators and bounded tenants.

### Phase 3: Production Platform Readiness
**Duration:** 4-6 weeks
**Objective:** move from credible pilot platform to production-ready deployment baseline.

Includes:
1. Workstream F: deployment and identity maturity
2. security reviews and penetration-style validation
3. resilience and DR drills

Decision gate:
- At the end of this phase, ACOS can support serious enterprise pilot expansion and formal procurement review.

---

## 6. Road To Production

### Stage 0: Now
Current state:
- strong prototype / early platform
- investable for team and direction
- not yet safe to present as hardened multitenant enterprise infrastructure

### Stage 1: Secure The Edges
Ship before any broad external exposure:
1. Authenticate `chat-api`.
2. Validate Slack signatures.
3. remove `eval()` from workflow execution.
4. disable permissive tenant access defaults.

Production gate:
- no unauthenticated execution
- no unsafe dynamic rule execution
- no cross-tenant read/write leakage in tests

### Stage 2: Make Operator Data Truthful
Ship before live operator rollout:
1. explicit live/degraded/demo states across ops endpoints
2. hard failure for persistence loss in normal mode
3. reliable connector failure reporting
4. audit correlation across workflow and channel paths

Production gate:
- dashboards and UI reflect real persistence and delivery state
- connector incidents are diagnosable without reading code

### Stage 3: Production Deployment Baseline
Ship before enterprise go-live:
1. managed secrets and identity provider integration
2. DB migrations
3. deployment environments and rollback flows
4. centralized logs, metrics, traces, and alerting
5. SLOs for shopper, ops, chat, and messaging paths

Production gate:
- repeatable staging and production deploy process
- rollback tested
- failover and incident runbooks exercised

### Stage 4: Enterprise Expansion
Ship before scaling to multiple real customers:
1. stronger RBAC and audit completeness
2. tenant-level feature controls and policy packs
3. connector credential isolation by tenant/environment
4. load, chaos, and abuse testing

Production gate:
- procurement-ready controls narrative
- production evidence pack for architecture, security, tenancy, and operations

---

## 7. Suggested Milestone Acceptance Metrics

### Security and Platform
- `0` anonymous workflow execution endpoints
- `0` use of `eval()` on workflow-authored data
- `100%` tenant-scoped repository paths covered by tests where applicable

### Reliability and Operations
- `100%` operator-visible analytics responses carry provenance
- `100%` live connector send failures recorded as failures
- recovery runbooks exercised for DB loss, channel failure, and bad promotion

### Product Readiness
- workflow authoring remains usable after safe rule engine introduction
- channels page can distinguish configured preview vs healthy live path
- operators can tell if they are acting on demo, degraded, or live data

---

## 8. Investment Recommendation Framing

### If investing now
Invest on the basis of:
- strong product thesis
- credible architectural center of gravity
- evidence of shipping velocity
- clear hardening path without platform rewrite

### Do not invest on the basis of
- current enterprise security maturity
- proven multitenant enforcement
- production-ready operational controls

### What would materially improve confidence fast
1. close Phase 1 completely
2. demonstrate a tenant isolation test suite
3. show authenticated `chat-api` flows in staging
4. remove silent production-mode in-memory fallbacks

---

## 9. Immediate Next Implementation Slices

1. `PR-1` Secure `chat-api`
   - add auth dependencies, Slack signature verification, startup validation
2. `PR-2` Enforce tenant context
   - switch high-risk repository/context paths to `tenant_transaction`
   - tighten RLS deny-by-default behavior
3. `PR-3` Replace workflow `eval()`
   - add safe rules engine plus validation
4. `PR-4` Truthful persistence mode
   - disable silent in-memory write fallback in normal mode
5. `PR-5` Connector failure semantics
   - upgrade WhatsApp and Telegram delivery outcomes to explicit live failure states

This sequence preserves current momentum while addressing the specific issues that matter most to technical investment diligence.
