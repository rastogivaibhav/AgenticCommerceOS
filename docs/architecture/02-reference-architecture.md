# ACOS Reference Architecture

## Purpose

This document describes the architecture that is actually present in the repository today, plus the most important near-term gaps.

## Current Service Topology

### Experience Layer

Interfaces already implemented:
- shopper API clients calling `shopper-api`
- operators using the React ops UI served at `/ui` by `ops-api`
- Slack and message-based clients calling `chat-api`
- WhatsApp and Telegram channel participants entering flows through `ops-api` channel endpoints

### API And Control Layer

Current services:
- `apps/shopper_api/main.py`
  - `POST /journey`
  - `POST /v1/journey`
  - `GET /metrics`
  - `GET /health`
- `apps/ops_api/main.py`
  - workflow, run, replay, analytics, billing, agent, skill, tenant, channel, demo-route, connector, sandbox, incident, and UI routes
  - embedded static UI serving at `/ui`
- `apps/chat_api/main.py`
  - Slack/message intake
  - workflow execution from messages
  - async job creation and status retrieval

### Workflow And Runtime Layer

There are two execution modes in the current codebase:

1. Shopper journey runtime
- implemented in `acosplatform/journey/engine.py`
- resolves a journey family
- resolves an active workflow version for that family and environment
- executes modular commerce capabilities
- applies ADK runtime support, policy checks, scoring, billing, metrics, traces, and context persistence

2. Saved workflow graph execution
- implemented in `acosplatform/workflows/executor.py`
- loads a saved workflow version and graph
- executes graph nodes in dependency order
- supports node types:
  - `triggerNode`
  - `connectorNode`
  - `agentNode`
  - `decisionNode`
  - `humanNode`
  - `endNode`
- persists the execution as a run with `tool_trace` and `node_trace`

### Channel And Retail Ops Layer

`acosplatform/retail_ops/service.py` adds a channel-oriented orchestration layer on top of saved workflows:
- sender discovery and approval
- pairing/start-link onboarding for channel identities
- route inference from inbound text
- dispatch into demo routes
- notification fan-out to configured target channels

This is the main bridge between channel intake and workflow execution in the current repository.

### Connector And Runtime Provider Layer

Current connector/provider modules:
- `integrations/shopify/client.py`
- `integrations/salesforce/client.py`
- `integrations/whatsapp/client.py`
- `integrations/telegram/client.py`
- `integrations/adk/provider.py`

Supported runtime providers today:
- `google_genai`
- `lmstudio_local`
- `local_fallback`

The connector model is intentionally honest about execution mode:
- `live` when credentials and upstream systems are available
- `configured_preview` when a connector is configured but live send is disabled or degraded
- `sandbox` when the system falls back to local behavior

## Current Container Topology

The local compose topology is:
- `shopper-api`
- `ops-api`
- `chat-api`
- `postgres`

`ops-ui` is built separately from `apps/ops_ui_v2` and served by `ops-api` from either:
- `apps/ops_api/ui`
- or `apps/ops_ui_v2/dist`

## Current Request Flows

### Shopper Journey Flow

1. Request enters `shopper-api` with `X-API-Key`.
2. Pydantic validation and tenant traffic controls are applied.
3. `journey.engine.run_journey` resolves journey family and active workflow.
4. Commerce services and ADK runtime logic run.
5. Context, run, events, traces, metrics, and score are persisted.
6. A structured result is returned with workflow and trace metadata.

### Saved Workflow Execution Flow

1. Operator or API client calls an `ops-api` workflow execute or test-run endpoint.
2. `workflows.executor.execute_saved_workflow` loads the active version for the environment.
3. Graph nodes execute across connectors, agent runtime, decision logic, and human escalation.
4. Tool and node traces are collected.
5. A run is persisted in Postgres.
6. The response includes workflow resolution, traces, and channel response artifacts.

### Channel Demo Route Flow

1. Inbound WhatsApp or Telegram message is received through `ops-api`.
2. Channel binding and sender approval state are resolved.
3. Pairing flow runs if a pair/start code is present.
4. A demo route is inferred or selected.
5. The route dispatches to a saved workflow execution.
6. Customer reply and operator notifications are sent through the channel adapters.

## Current Bounded Contexts In Code

### Journey Runtime
- `acosplatform/journey`
- `acosplatform/plugins`
- `acosplatform/personalization`
- `acosplatform/evaluation`
- `acosplatform/billing`

### Workflow Registry And Execution
- `acosplatform/workflows`
- `apps/ops_api` workflow endpoints
- `apps/ops_ui_v2` workflow registry and editor UI

### Channel And Retail Operations
- `acosplatform/retail_ops`
- channel, pairing, sender, and demo route endpoints in `apps/ops_api/main.py`

### Platform And Governance
- `acosplatform/auth`
- `acosplatform/governance`
- `acosplatform/tenancy`
- `acosplatform/audit`
- `acosplatform/observability`
- `acosplatform/context`

### Persistence
- `acosplatform/db`
- `db/schema.sql`

## Persistence Foundations

The current schema already includes first-class storage for:
- workflows and versions
- promotions
- runs and events
- audit events
- context sessions, events, and memory
- governance decisions
- agents and skills
- tenants
- channels, senders, and pairings
- demo routes
- CRM customers and cases
- products, orders, loyalty points
- experiments

This means ACOS has already moved beyond a purely in-code architecture for workflow and operational state.

## Current UI Surface

The React UI currently exposes pages for:
- Workflows
- Workflow Editor
- Agents
- Skills
- Analytics
- Channels
- Demo Routes
- Tenants

The UI is routed under `/ui` and uses `BrowserRouter` with `/ui/` as its basename.

## Reliability And Security Foundations Present Today

- API-key auth on `shopper-api`
- JWT role enforcement on ops routes
- CORS allowlists
- tenant rate limits, daily quotas, and in-flight caps
- row-level security for context and governance tables
- workflow promotion and rollback state
- audit persistence for operational mutations
- health and metrics endpoints on the main services
- global exception handling with sanitized error responses
- startup validation for auth and schema availability

## Important Gaps

The biggest remaining gaps are:
- stronger separation between demo/mock data paths and live operator paths
- deeper policy enforcement inside every saved workflow node execution path
- broader automated test coverage for end-to-end channel and connector flows
- fuller externalization of agent, skill, and connector version promotion
- more complete asynchronous backbone for long-running workflow steps

## Near-Term Architectural Direction

The current codebase already has the right seams to continue evolving by:
- strengthening the workflow graph model rather than replacing it
- hardening live connector operations behind the existing sandbox/live contract
- expanding the ops UI around the existing workflow, channel, and incident APIs
- treating agents, skills, and connectors as increasingly versioned and promotable resources
