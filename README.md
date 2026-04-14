# ACOS Control Plane
### Agentic commerce runtime plus governed operations plane

[![GitHub Repo](https://img.shields.io/badge/GitHub-AgenticCommerceOS-181717?logo=github)](https://github.com/rastogivaibhav/AgenticCommerceOS)
[![Stars](https://img.shields.io/github/stars/rastogivaibhav/AgenticCommerceOS?style=social)](https://github.com/rastogivaibhav/AgenticCommerceOS/stargazers)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](./LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.0-blue)](./CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB)](https://www.python.org/)
[![Docker Compose](https://img.shields.io/badge/docker%20compose-ready-2496ED)](./docker-compose.yml)

ACOS is a Python and React platform for running AI-assisted commerce journeys with explicit workflow versions, operator controls, tenant-aware protections, and connector-backed service flows.

In plain English, ACOS is a **governed control plane for AI-assisted retail and customer-service operations**. It gives an operations team one place to design, test, approve, promote, and monitor customer-facing workflows that run across APIs, messaging channels, agents, and external systems.

Today the repository ships a working split between:
- `shopper-api` for customer-facing journey execution
- `ops-api` for workflow governance, replay, approvals, channels, agents, skills, and analytics
- `chat-api` for Slack and message-driven workflow execution
- `ops_ui_v2` for the control-plane UI served by `ops-api`
- PostgreSQL persistence for runs, workflow versions, audit, context, CRM, channels, agents, and skills

## What This Software Actually Does

ACOS is built to help a retail or service operations team answer questions like:
- Which workflow is live for customer support, order status, returns, loyalty, or escalation?
- Which agent, tools, and channels are attached to that workflow?
- How do we test and approve a change before it reaches customers?
- When something fails, can an operator see what happened and roll back safely?

The software is not just a chatbot and not just a workflow builder. Its real job is to sit between:
- customer-facing channels such as WhatsApp, Telegram, and APIs
- AI runtimes and tool-connected agents
- operator governance for approvals, promotions, audit, and rollback

## Who It Is For

The most credible early user is:
- a retail or commerce operations team
- a digital customer-support organization
- an enterprise innovation or automation team piloting AI-led service flows

ACOS is most useful when customer interactions are spread across channels and teams want more control than ad hoc prompt wiring or single-channel bots can provide.

## What It Is Not

ACOS is not:
- a generic no-code workflow SaaS
- a mass-market chatbot product
- a replacement for Shopify, Salesforce, WhatsApp, Telegram, or the underlying LLM providers

It is the governed operations layer that coordinates those systems.

## What Ships Today

- Versioned workflow registry with seeded workflow families for `discovery`, `purchase`, `post_purchase`, `service`, and `engagement`
- Graph-based workflow execution for saved workflows with node types for triggers, connectors, agents, decisions, human handoff, and end states
- Shopper runtime execution on `POST /v1/journey` with API-key auth, tenant traffic guards, metrics, and workflow resolution
- Ops-plane controls for create, approve, promote, rollback, archive, test-run, and execute workflow versions
- Agent and skill inventory with test endpoints and runtime-provider visibility
- Channel binding, sender approval, pairing, QR/start-link onboarding, and workflow validation routes for WhatsApp and Telegram
- Connector probes and action execution for Shopify, Salesforce, WhatsApp Cloud API, Telegram Bot API, plus runtime provider selection across Google GenAI, LM Studio, and local fallback
- Persisted runs, events, audit events, context sessions/memory, governance decisions, CRM customers/cases, products, orders, tenants, agents, skills, and demo routes
- A React ops UI with pages for Workflows, Agents, Skills, Analytics, Channels, Demo Routes, and Tenants

## Architecture At A Glance

```text
                          +-----------------------------------+
                          | Ops UI (React + Vite build)       |
                          | served by ops-api at /ui          |
                          +----------------+------------------+
                                           |
                                           v
+---------------------+     +------------------------------+     +----------------------+
| shopper-api :8080   |     | ops-api :8081                |     | chat-api :8001       |
| /v1/journey         |     | workflows, channels, agents, |     | Slack + message/job  |
| API key auth        |     | skills, replay, analytics    |     | workflow execution   |
+----------+----------+     +---------------+--------------+     +-----------+----------+
           |                                |                                  |
           +--------------------+-----------+----------------------------------+
                                |
                                v
                  +------------------------------------------+
                  | PostgreSQL                               |
                  | runs, workflow versions, promotions,     |
                  | audit, context, CRM, channels, agents    |
                  +------------------------------------------+
                                |
                                v
          +-----------------------------------------------------------+
          | External systems and runtime providers                    |
          | Shopify | Salesforce | WhatsApp | Telegram | Google GenAI |
          | LM Studio | local fallback                                 |
          +-----------------------------------------------------------+
```

## Repository Layout

```text
apps/
  shopper_api/   customer-facing runtime API
  ops_api/       control-plane API and embedded UI serving
  chat_api/      Slack/message gateway
  ops_ui_v2/     React control-plane frontend

acosplatform/
  journey/       shopper runtime orchestration
  workflows/     workflow registry and graph executor
  retail_ops/    channel intake and demo route dispatch
  db/            repository layer and schema helpers
  governance/    authorization and policy helpers
  observability/ metrics, traces, SLO helpers
  tenancy/       tenant-aware traffic controls
  replay/        replay services

integrations/
  adk/           runtime provider abstraction
  shopify/       Shopify Admin API probe/actions
  salesforce/    Salesforce REST actions
  whatsapp/      WhatsApp Cloud API helpers
  telegram/      Telegram Bot API helpers

db/schema.sql    bootstrap schema for local Postgres
docs/            architecture, runbooks, readiness docs
```

## Quick Start

```bash
git clone https://github.com/rastogivaibhav/AgenticCommerceOS.git
cd AgenticCommerceOS
cp .env.example .env
docker compose up --build -d
```

Verify services:

```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
curl http://localhost:8001/health
```

Open the control plane:
- [http://localhost:8081/ui/](http://localhost:8081/ui/)

Default runtime posture:
- `ACOS_PLATFORM_MODE=normal` keeps the product in its normal operator posture even if some dependencies fall back locally.
- `ACOS_PLATFORM_MODE=demo` forces the UI to present a demo-safe posture for local walkthroughs and connector-light setups.
- `ACOS_RUNTIME_PREFERENCE=auto` lets the runtime choose between Google GenAI, host-local OpenAI-compatible LLMs, Docker-routed local LLMs, and final local fallback.

Bootstrap a local ops token when dev auth is enabled:

```bash
python scripts/mint_dev_jwt.py --role admin --secret "$OPS_JWT_SECRET"
```

Optional frontend-only development:

```bash
cd apps/ops_ui_v2
npm install
npm run dev
```

## Core APIs

### Shopper Runtime

Execute a shopper journey:

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

The response includes:
- `run_id`
- resolved `journey`
- selected `workflow` and version
- `trace` id
- contextual result payload with cost, score, policy, and runtime metadata

### Ops Control Plane

List workflows:

```bash
curl http://localhost:8081/api/v1/workflows \
  -H "Authorization: Bearer <OPS_TOKEN>"
```

Promote a workflow version:

```bash
curl -X POST http://localhost:8081/api/v1/workflows/wf-order-support-demo/versions/v1/promote \
  -H "Authorization: Bearer <OPS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_environment": "prod",
    "source_environment": "stage",
    "approval_note": "Approved for controlled cutover"
  }'
```

Execute a saved workflow through the graph executor:

```bash
curl -X POST http://localhost:8081/api/v1/workflows/wf-order-support-demo/execute \
  -H "Authorization: Bearer <OPS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "default",
    "customer_id": "cust_1001",
    "environment": "dev",
    "message": "Where is my order ORD-1001?"
  }'
```

List channels and demo routes:

```bash
curl http://localhost:8081/api/v1/channels \
  -H "Authorization: Bearer <OPS_TOKEN>"

curl http://localhost:8081/api/v1/demo/routes \
  -H "Authorization: Bearer <OPS_TOKEN>"
```

### Chat API

The chat gateway exposes Slack and message-driven workflow endpoints, including:
- `/api/chat/message`
- `/api/messages/send`
- `/api/workflows/execute-message`
- `/api/jobs/{job_id}/status`

Security posture for chat-api:
- Slack-originated message intake on `/api/chat/message` validates `X-Slack-Signature` and `X-Slack-Request-Timestamp` whenever `SLACK_SIGNING_SECRET` is configured.
- Direct workflow execution routes under `/api/workflows/*` require `Authorization: Bearer <token>`.
- In non-dev environments, startup validation now requires chat bearer auth secret configuration (`CHAT_JWT_SECRET` or `OPS_JWT_SECRET`) plus `SLACK_SIGNING_SECRET`.

## Data Model Snapshot

`db/schema.sql` currently defines and initializes:
- `runs`, `events`, `experiments`
- `workflows`, `workflow_versions`, `workflow_promotions`
- `audit_events`, `governance_decisions`
- `context_sessions`, `context_events`, `context_memory`
- `tenants`, `orders`, `products`, `loyalty_points`
- `agents`, `skills`
- `channel_bindings`, `channel_senders`, `channel_pairings`
- `demo_routes`
- `crm_customers`, `crm_cases`

Row-level security is enabled for context and governance tables, with tenant isolation policies applied through `app.tenant_id`.

## Configuration

Use `.env.example` as the starter file, but note that the current codebase also supports additional optional connector and runtime-provider variables through `docker-compose.yml` and the integration modules.

Required for local compose:
- `DB_PASSWORD`
- `SHOPPER_API_KEYS`
- `OPS_JWT_SECRET`
- `ALLOWED_ORIGINS`

Common optional variables:
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- `ACOS_PLATFORM_MODE` with `normal` or `demo`
- `ACOS_RUNTIME_PREFERENCE` with `auto`, `google_genai`, `local_openai_host`, `local_openai_docker`, or `local_fallback`
- `LOCAL_OPENAI_BASE_URL`
- `LOCAL_OPENAI_MODEL`
- `DOCKER_OPENAI_BASE_URL`
- `DOCKER_OPENAI_MODEL`
- `LMSTUDIO_BASE_URL` and `LMSTUDIO_MODEL` as legacy aliases for the host-local OpenAI-compatible path
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_ADMIN_ACCESS_TOKEN`
- `SHOPIFY_API_VERSION`
- `SALESFORCE_INSTANCE_URL`
- `SALESFORCE_ACCESS_TOKEN`
- `SALESFORCE_API_VERSION`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_API_VERSION`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_DEFAULT_CHAT_ID`
- `TELEGRAM_BOT_USERNAME`
- `TELEGRAM_WEBHOOK_URL`
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SLACK_WORKSPACE_ID`
- `CHAT_JWT_SECRET` (optional if `OPS_JWT_SECRET` is already provided)
- `TENANT_RATE_LIMIT_PER_MINUTE`
- `TENANT_DAILY_QUOTA`
- `TENANT_MAX_IN_FLIGHT`
- `OPS_ENVIRONMENT`
- `ALLOW_MOCK_ROUTES`
- `ALLOW_NON_DEV_MOCK_ROUTES`

WhatsApp binding notes:
- Environment variables enable the connector globally, but the control plane still expects a WhatsApp channel binding to be saved through the Channels page.
- The binding metadata should include `verify_token`, `access_token`, `phone_number_id`, and optionally `start_chat_number` plus `default_recipient`.
- Webhook verification uses the saved binding metadata, so multiple WhatsApp bindings can coexist as long as each binding carries its own verify token and phone number ID.
- Inbound webhook routing now resolves tenant and environment from the matched binding instead of assuming `default` and `whatsapp-support`.
- Outbound channel tests use the saved `default_recipient` when no explicit recipient is provided, which keeps local validation predictable before a customer sender is paired.
- You can check whether a real Meta validation is runnable locally with `python scripts/check_whatsapp_live_readiness.py`.

Runtime routing notes:
- The header in `ops_ui_v2` now exposes runtime controls so operators can switch between `normal` and `demo` posture and choose a preferred LLM path without editing code.
- `local_openai_host` is intended for host-local runtimes such as LM Studio or another OpenAI-compatible server bound on the machine.
- `local_openai_docker` is intended for Docker-routed runtimes such as a compose service exposed at `http://llm:1234/v1` or a host service reachable from containers through `host.docker.internal`.

## Current Operational Shape

ACOS is no longer just a prototype with implicit Python-only workflows. The current code already has:
- persisted workflow identities and versions
- active promotion state by environment
- a visual graph model in the UI
- a graph executor in the backend
- demo retail routes that bridge channel intake to workflow execution
- approval and incident surfaces in the ops API
- sandbox-to-live connector behavior with explicit probe and preview modes

The strongest way to think about the product today is:
- `shopper-api` runs customer-facing journeys
- `ops-api` and `ops_ui_v2` act as the governed control plane
- `chat-api` and channel bindings extend those workflows into message-driven operations

The main product value is governance and visibility around AI-assisted service flows, not generic automation for its own sake.

The main gaps are still around full production hardening:
- more complete connector coverage
- stronger separation of mock/demo data from live operator paths
- deeper policy enforcement inside every workflow step
- broader automated test coverage across end-to-end channel flows

## Contributing

1. Create a focused branch.
2. Make small, verifiable changes.
3. Run the relevant checks for the area you touched.
4. Update docs when service topology, API behavior, or operational workflows change.

Useful references:
- [docs/README.md](./docs/README.md)
- [docs/architecture/02-reference-architecture.md](./docs/architecture/02-reference-architecture.md)
- [docs/RUNBOOK_GO_LIVE.md](./docs/RUNBOOK_GO_LIVE.md)
- [docs/RUNBOOK_WORKFLOW_PROMOTION.md](./docs/RUNBOOK_WORKFLOW_PROMOTION.md)

## License

Apache License 2.0. See [LICENSE](./LICENSE).
