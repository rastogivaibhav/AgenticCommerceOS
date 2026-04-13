# ACOS Canonical Resource Model

## Purpose

This document maps the current ACOS persistence model to the platform concepts used by the APIs and UI.

It is intentionally grounded in the tables and records that exist today.

## Modeling Principles

### Stable Identity
Business objects such as workflows, tenants, agents, skills, channels, and CRM records use stable primary identifiers.

### Version Where It Matters
Workflow definitions separate stable workflow identity from versioned workflow artifacts and environment promotions.

### Tenant Awareness
Many resources are tenant-scoped even when the default demo data currently uses `default`.

### Environment Awareness
Workflow activation and some channel configuration depend on environment.

### Auditability
Control-plane mutations should leave audit or promotion history whenever they affect live behavior.

## Current Resource Catalog

| Resource | Backing table(s) | Scope | Current notes |
|---|---|---|---|
| Tenant | `tenants` | Tenant-scoped | Stores currency, tax rate, features, promo rules, and connector routes |
| Workflow | `workflows` | Tenant-scoped | Stable workflow identity and family |
| Workflow Version | `workflow_versions` | Workflow-scoped | Stores graph definition, schemas, lifecycle, approval metadata |
| Workflow Promotion | `workflow_promotions` | Environment-scoped | Tracks active version per target environment |
| Run | `runs` | Run-scoped | Stores execution input, output, workflow id/version, cost, score, metadata |
| Event | `events` | Run-scoped | Timestamped execution events tied to a run |
| Audit Event | `audit_events` | Tenant and environment-aware | Immutable control-plane action record |
| Context Session | `context_sessions` | Tenant and customer-scoped | Conversation or journey context boundary |
| Context Event | `context_events` | Session-scoped | Structured context timeline |
| Context Memory | `context_memory` | Tenant and customer-scoped | Durable keyed memory with freshness and expiry |
| Governance Decision | `governance_decisions` | Tenant-scoped | Records allow/deny-style policy decisions |
| Agent | `agents` | Registry-scoped, tenant-aware in usage | Holds purpose, skills, connectors, runtime provider, scorecard, test history |
| Skill | `skills` | Registry-scoped | Holds code, contracts, execution mode, timeout, retries |
| Channel Binding | `channel_bindings` | Tenant and environment-scoped | WhatsApp/Telegram channel configuration and route permissions |
| Channel Sender | `channel_senders` | Binding-scoped | Approved or pending sender identity within a channel |
| Channel Pairing | `channel_pairings` | Binding-scoped | Scan-to-start or pair-code onboarding record |
| Demo Route | `demo_routes` | Tenant-aware operational config | Route-to-workflow mapping for retail demo flows |
| CRM Customer | `crm_customers` | Tenant-scoped | Channel preference, loyalty tier, external IDs, segmentation |
| CRM Case | `crm_cases` | Customer and tenant-scoped | Service/escalation records |
| Product | `products` | Catalog-scoped | Basic catalog items for demo and local operations |
| Order | `orders` | Customer and tenant-scoped | Local order record used by runtime and retail flows |
| Loyalty Balance | `loyalty_points` | Customer-scoped | Current loyalty score/balance |
| Experiment | `experiments` | Global or tenant-aware operational data | Stores simple A/B-style experiment records |

## Current Resource Details

### Tenant

Current fields emphasize operational configuration:
- `id`
- `name`
- `currency`
- `tax_rate`
- `promo_rules`
- `features`
- `connector_routes`

This is lighter than a full enterprise tenant model, but it is already enough to drive journey configuration and channel routing.

### Workflow And Workflow Version

This is the most mature versioned resource pair in the codebase.

Key current invariants:
- workflow identity is stable
- versions are stored separately
- promotions decide which version is active in an environment
- workflow execution stores the chosen workflow id and version on the run

### Run

Runs are the canonical execution record.

Current fields cover:
- request identity
- tenant/customer scope
- journey
- workflow id/version
- environment
- structured input/output
- cost and score
- agent and skill metadata
- creation timestamp

### Agent

Agents are currently treated as first-class operational registry objects.

Current fields include:
- `id`, `name`, `subsystem`, `purpose`
- status, uptime, latency, calls
- `skills`, `bound_skills`
- `connector_bindings`
- `used_by_workflow_ids`
- `runtime_provider`, `model_name`, `agent_version`
- `scorecard`, `history`, `code`
- last test metadata

This is already more concrete than the earlier aspirational “agent management” model.

### Skill

Skills are registry records with both UI-facing and execution-facing properties:
- `id`, `name`, `category`, `type`
- source `code`
- `input_schema`, `output_schema`
- `execution_mode`
- `timeout_seconds`
- `retries`
- lint warnings and usage count

### Channel Model

The channel model is now a distinct part of the resource graph:

- `channel_bindings`
  - configured identity, environment, allowed routes, notification targets, metadata
- `channel_senders`
  - discovered inbound participants with approval state
- `channel_pairings`
  - controlled onboarding from QR or start-link flows

This model supports the current WhatsApp and Telegram onboarding and dispatch flows.

### CRM Model

The current CRM model is intentionally small but operationally useful:
- `crm_customers` links customer identity to phone/email, loyalty tier, channel preference, and external CRM/commerce IDs
- `crm_cases` stores escalation and service activity

These resources are used directly by the workflow executor and retail routing service.

## Tenant And Environment Boundaries

Current behavior is uneven but clearly trending in the right direction:
- many resources carry `tenant_id`
- workflow execution stores `environment_id`
- workflow promotions are explicitly environment-targeted
- channel bindings also carry environment
- row-level security is enabled for context and governance tables

The next step is to make tenant and environment constraints more uniformly enforced across every operational resource.

## Canonical Relationships

The most important live relationships are:
- tenant -> workflows
- workflow -> workflow versions
- workflow version -> workflow promotions
- workflow execution -> runs
- run -> events
- workflow/demo route -> agents, skills, connectors, channels
- channel binding -> sender -> pairing -> demo route -> workflow
- customer -> cases, orders, loyalty state, context memory

## Gaps Compared With A Fully Mature Model

Still missing or only partially represented:
- first-class version objects for agents and skills
- explicit connector registry tables separate from bindings and probes
- richer environment objects beyond string identifiers
- broader immutable artifact metadata such as hashes for all promotable resources
- generalized approval records beyond workflow promotions and audit events

## Guidance For Future Changes

When adding new platform behavior:
- prefer extending existing canonical resources before inventing parallel objects
- keep workflow identity/version/promotion separation intact
- attach tenant and environment metadata early
- persist operator-visible state so the UI and API do not depend on hidden runtime-only behavior
