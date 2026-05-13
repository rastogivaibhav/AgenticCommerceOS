# ACOS North-Star Gap Closure Sprint Report

## Sprint objective
Close the highest-priority gaps found in the phase verification review: stronger multi-agent proof, human handoff, GraphQL Studio mutations, event outbox foundation, extended retail tools, and production persistence direction.

## Completed changes

### 1. Golden journey upgraded from single-primary-agent to multi-agent orchestration
The north-star runtime now coordinates the following agents for the winter wedding journey:

- Discovery Agent
- Stylist Agent
- Inventory Agent
- Service Agent / handoff

The smoke path now calls:

- `catalog.search`
- `pricing.calculate`
- `promotions.find_offers`
- `inventory.check_stock`
- `case.create`

Evidence now includes `human.handoff.created` when pickup/store context is present.

### 2. Intent routing improved
The intent router now prioritises styling/product-discovery signals over narrow stock availability when a message contains rich retail intent such as outfit, wedding, budget, and pickup constraints.

### 3. Retail tool layer extended
Added support for:

- `catalog.get_product`
- `pricing.calculate`
- `promotions.find_offers`
- `returns.create_return`

The mock retail store now includes product detail, pricing calculation, offer discovery, and return creation helpers.

### 4. Workflow runtime gap closure
Workflow executor now supports:

- `intentNode`
- `humanHandoffNode` alias alongside existing `humanNode`
- evidence creation for workflow human handoff
- downstream state exposure of classified intent and recommended agent

### 5. GraphQL Studio mutations added
GraphQL schema now includes mutations for:

- `createWorkflowDraft`
- `runDryTest`
- `approveWorkflow`
- `promoteWorkflow`
- `generateAgent`

This moves GraphQL beyond read-only UI composition and toward Agent Studio operational control.

### 6. Event backbone foundation added
Added a lightweight SQLite-backed outbox module:

- `acosplatform/events/outbox.py`

It supports:

- event publishing
- pending-event listing
- processed marker
- retry/dead-letter marker
- idempotency key

`message.received` now publishes to the outbox.

### 7. Postgres north-star production direction added
Added optional Postgres repository:

- `acosplatform/northstar/postgres_repository.py`

Updated `db/northstar_schema.sql` with outbox table baseline.

This does not yet replace SQLite in the runtime by default, but it gives the production migration path for the north-star spine.

## Validation evidence

### North-star tests

```text
12 passed
```

### Week 11/12 UAT and production gate tests

```text
27 passed
```

### Golden journey smoke

```text
ACOS north-star smoke status: success
Intent: styling_advice
Agent: Stylist Agent
Tool calls: 7
Evidence events: 15
Response: For a winter wedding under £200, I recommend: Navy Satin Midi Dress (£89, 4 in Reading); Silver Wrap Shawl (£35, 8 in Reading); Black Block-Heel Court Shoes (£59, 3 in Reading). Basket is within the £200 budget. Eligible offer: £10 off occasionwear bundles over £150.
```

### Frontend build

```text
vite build successful
```

Known warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

### Docker runtime

```text
Docker unavailable in this sandbox: docker: command not found
```

Docker Compose runtime remains unverified here and must be certified in a Docker-enabled runner.

## Updated phase status

| Phase | Status after this sprint | Notes |
|---|---:|---|
| Phase 0 — Stabilise codebase | Partial | Tests and UI build pass after install. Docker still unverified. |
| Phase 1 — Omnichannel session spine | Mostly implemented | SQLite durable pilot state + message outbox. Full channel coverage still not complete. |
| Phase 2 — Intent + agent router | Mostly implemented | Rule-based router and multi-agent selection evidence now stronger. Planner/memory still light. |
| Phase 3 — Workflow runtime upgrade | Improved partial | `intentNode`, `mcpToolNode`, `humanHandoffNode` now exist. Replay remains incomplete. |
| Phase 4 — Retail tool layer | Mostly implemented as mock | More complete mock retail capability. Real Shopify/Salesforce parity still needed. |
| Phase 5 — MCP foundation | Partial-to-good | Foundation remains; external MCP client certification still needed. |
| Phase 6 — GraphQL Studio API | Improved partial | Read queries + key mutations now exist. Auth/RBAC integration still needs production hardening. |
| Phase 7 — Agent Studio v2 | Partial | Backend supports more; UI still needs full tabbed inspector/MCP browser/deployment readiness. |
| Phase 8 — Golden retail journey | Mostly implemented for pilot | Now proves 4 agents, 5+ tools, handoff, evidence. Replay/Ops Console visual proof remains. |
| Phase 9 — Governance, FinOps, Safety | Partial | Evidence exists. DLP, cost controls, approval policies and unsafe-action blocking still incomplete. |
| Phase 10 — Production deployment | Partial/unverified | CI assets exist. Docker/cloud deployment proof still pending. |

## Remaining GA blockers

1. Docker Compose runtime proof in Docker-enabled CI.
2. Full Postgres runtime switch for north-star repository, not only optional adapter/schema.
3. Production RBAC and tenant isolation for GraphQL, MCP, and north-star endpoints.
4. UI Agent Studio v2 completion: tabbed inspector, MCP browser, deployment readiness panel.
5. Replay UI and replay backend proof for golden journey.
6. Governance/FinOps/DLP hardening.
7. Frontend code splitting to remove large bundle warning.
8. External MCP client compatibility validation.

## Next recommended sprint

**Production Runtime + Studio Proof Sprint**

Target outcomes:

- run full Docker Compose in CI
- use Postgres for north-star state in production profile
- add GraphQL/MCP auth guards by role and tenant
- build tabbed inspector in Agent Studio
- add MCP Tool Browser screen
- add replay proof for golden journey
- generate CTO demo pack with screenshots and API evidence
