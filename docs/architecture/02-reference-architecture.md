# ACOS Reference Architecture

## Purpose

This document defines the target enterprise architecture for ACOS while staying grounded in the current repository.

## Baseline To Build From

Current baseline:
- `shopper-api` for customer-facing requests
- `ops-api` for operational access
- Postgres for runs, events, and experiments
- modular Python packages for journeys, commerce capabilities, billing, replay, and tenancy
- Docker and Compose already present

Target state should evolve this baseline instead of replacing it wholesale.

## Architectural Layers

### 1. Experience Layer
Interfaces that initiate work or consume operational insight.

Channels:
- shopper web and mobile
- contact center and support tooling
- operator control plane
- partner or marketplace APIs

### 2. API Gateway Layer
The ingress layer that enforces:
- authentication and authorization
- tenant routing
- rate limits
- request validation
- versioning
- request tracing

### 3. Orchestration Runtime Layer
The brain of ACOS.

Responsibilities:
- intent classification
- workflow selection
- step execution
- policy evaluation
- retries and compensations
- human handoff
- run state persistence

### 4. Agent And Skill Layer
Reusable execution assets.

Core constructs:
- agents
- skills
- prompts
- tools and connectors
- policies
- model profiles
- execution budgets

### 5. Commerce Domain Services Layer
Business capabilities that should become durable services over time.

Primary bounded contexts:
- Catalog
- Pricing
- Promotions
- Checkout
- Orders
- Returns
- Loyalty
- Personalization
- Billing and Usage
- Evaluation

### 6. Platform And Governance Layer
Cross-cutting enterprise concerns:
- identity and access management
- tenancy
- audit
- observability
- secrets and config
- release management
- compliance controls

## Bounded Context Map

### Channel Intake
Normalizes requests from shopper or operator channels into typed commands and events.

### Journey Orchestration
Owns workflow state, execution policy, step sequencing, replay, and run history.

### Agent Management
Owns agent definitions, allowed skills, model profiles, and execution guardrails.

### Skill Registry
Owns tools, schemas, connector bindings, test fixtures, and version history.

### Commerce Core
Owns deterministic business services such as catalog lookup, pricing, promotions, loyalty, checkout, orders, and returns.

### Governance And Risk
Owns policy evaluation, approval gates, audit, tenant isolation, and exception handling.

### Analytics And Evaluation
Owns cost, quality, usage, experimentation, and operational analytics.

## Runtime Topology

## Current Suggested Container Topology

- `shopper-api`
- `ops-api`
- `postgres`
- `ops-ui` as a built static artifact served either by `ops-api` or a dedicated container

## Near-Term Enterprise Topology

- `edge-gateway`
- `shopper-api`
- `ops-api`
- `workflow-runtime`
- `agent-registry-service`
- `skill-registry-service`
- `policy-service`
- `evaluation-service`
- `postgres`
- `redis`
- `object-store`
- `message-bus`
- `ops-ui`

## Data Model Foundations

The following objects should become first-class persisted resources:

- Tenant
- User
- Agent
- Skill
- Workflow
- WorkflowVersion
- Policy
- Connector
- Run
- RunStep
- Event
- EvaluationResult
- Experiment
- DeploymentPromotion

## Integration Strategy

### Deterministic Before Generative
Use deterministic business services for pricing, checkout, loyalty, and returns.
Use LLMs for explanation, summarization, intent help, and decision support where governed.

### Adapter Pattern For External Systems
All external commerce and enterprise systems should be integrated through typed adapters.

### Async Event Backbone
Longer-running workflows should publish events rather than rely on synchronous chaining only.

## Security Architecture

Enterprise minimums:
- strong tenant isolation
- environment-specific secrets
- role-based access control
- policy-based action authorization
- audit logs for sensitive actions
- immutable run history
- model and tool allowlists
- PII classification and redaction
- approval gates for high-risk actions

## Observability Architecture

Required pillars:
- logs with correlation ids
- metrics by tenant, workflow, skill, and environment
- traces across end-to-end runs
- run timelines in the control plane
- business KPIs such as resolution rate, conversion, cost per run, and escalation rate

## Reliability And Operational Requirements

- stateless service containers where possible
- idempotent workflow steps
- retries with backoff for transient failures
- dead-letter handling for failed asynchronous events
- health endpoints for all services
- startup checks for schema and dependency readiness

## Quality Requirements

Every slice should meet:
- typed interfaces
- migration-safe persistence
- automated tests
- container build success
- documented operational behavior
- backward-compatible API versioning where relevant

## Current-To-Target Gaps

The main gaps between current state and target architecture are:
- mock data instead of durable domain systems
- orchestration logic embedded in code rather than workflow resources
- incomplete control-plane UX
- weak separation between runtime and control-plane concerns
- limited policy, audit, and metrics enforcement in the execution path
- no durable registry for agents, skills, or workflow versions

## Architectural Direction

The next development phases should not try to solve everything at once.
They should progressively convert the current prototype into:

1. a trusted control-plane foundation
2. a workflow-centric runtime
3. a governed registry for agents and skills
4. a production-grade operational platform
