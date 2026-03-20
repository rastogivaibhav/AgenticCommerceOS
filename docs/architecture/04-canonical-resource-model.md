# ACOS Canonical Resource Model

## Purpose

This document defines the canonical resource model for ACOS.

Its job is to prevent architectural drift as the platform grows from prototype to enterprise operating system.
Every new slice should align its APIs, persistence, and UI to these core objects.

## Modeling Principles

### Explicit Ownership
Each resource must have a single owning bounded context.

### Stable Identity
Each resource needs a stable primary identifier that survives version changes.

### Versioned Change
Mutable operational resources should separate stable identity from versioned definition.

### Tenant Awareness
Resources must declare whether they are:
- global
- tenant-scoped
- environment-scoped
- run-scoped

### Auditability
Any mutable resource must support created, updated, approved, and activated history.

## Core Resource Catalog

## 1. Tenant

### Purpose
Represents a business boundary for brand, region, operating rules, data isolation, and reporting.

### Ownership
Platform and governance.

### Scope
Tenant-scoped root object.

### Minimum Fields
- `tenant_id`
- `name`
- `status`
- `brand_code`
- `region`
- `default_currency`
- `feature_flags`
- `data_residency_policy`
- `created_at`
- `updated_at`

### Invariants
- tenant ids are immutable
- tenant status controls runtime eligibility
- tenant configuration cannot bypass global security controls

## 2. Environment

### Purpose
Represents the deployment stage for ACOS resources and runtime behavior.

### Ownership
Platform engineering.

### Minimum Fields
- `environment_id`
- `name`
- `type` such as `dev`, `test`, `stage`, `prod`
- `status`
- `release_policy`
- `created_at`

### Invariants
- production requires stricter approval policy than lower environments
- resources may be promoted across environments without changing logical identity

## 3. User

### Purpose
Represents a human operator or system principal interacting with ACOS.

### Ownership
Identity and access management.

### Minimum Fields
- `user_id`
- `display_name`
- `email`
- `role_assignments`
- `tenant_access`
- `status`
- `created_at`

### Invariants
- authorization is role- and tenant-aware
- privileged actions must be attributable to a user or service principal

## 4. Agent

### Purpose
Represents a named execution role that can operate within workflows using approved skills.

### Ownership
Agent management bounded context.

### Scope
Tenant-scoped, environment-promotable.

### Stable Fields
- `agent_id`
- `tenant_id`
- `name`
- `description`
- `owner_team`
- `status`
- `created_at`
- `updated_at`

### Versioned Fields
- `version`
- `model_profile`
- `system_behavior_contract`
- `allowed_skill_ids`
- `execution_budget`
- `escalation_rules`
- `policy_bindings`

### Invariants
- an active agent version must reference only approved skill versions
- an agent cannot execute outside tenant and environment policy boundaries

## 5. Skill

### Purpose
Represents a reusable capability with typed contracts and governed execution semantics.

### Ownership
Skill registry bounded context.

### Scope
Global or tenant-scoped depending on type.

### Stable Fields
- `skill_id`
- `name`
- `category`
- `owner_team`
- `scope`
- `status`

### Versioned Fields
- `version`
- `input_schema`
- `output_schema`
- `execution_mode` such as `deterministic`, `connector`, `ai-assisted`
- `connector_binding`
- `timeout_policy`
- `retry_policy`
- `risk_classification`
- `test_fixtures`

### Invariants
- every skill version must declare typed input and output contracts
- any side-effecting skill must declare idempotency and compensation expectations

## 6. Connector

### Purpose
Represents the governed integration contract between ACOS and an external system.

### Ownership
Integration platform.

### Minimum Fields
- `connector_id`
- `name`
- `system_type`
- `owner_team`
- `authentication_mode`
- `data_classification`
- `status`

### Versioned Fields
- `api_contract_version`
- `endpoint_configuration`
- `rate_limits`
- `error_mapping_rules`
- `observability_contract`

### Invariants
- no skill may invoke an external system without a declared connector
- connector contracts must be environment-aware

## 7. Workflow

### Purpose
Represents a named business process family such as discovery, purchase, service, or post-purchase.

### Ownership
Journey orchestration.

### Stable Fields
- `workflow_id`
- `tenant_id`
- `name`
- `workflow_family`
- `business_owner`
- `status`
- `created_at`
- `updated_at`

### Versioned Fields
- `version`
- `entry_conditions`
- `step_definitions`
- `agent_bindings`
- `policy_bindings`
- `input_schema`
- `output_schema`
- `rollback_strategy`
- `telemetry_contract`

### Invariants
- a workflow version must be immutable once approved
- an active workflow version must be associated with a promotion record
- write steps must define preconditions and postconditions

## 8. Workflow Version

### Purpose
The deployable versioned artifact of a workflow.

### Ownership
Journey orchestration.

### Minimum Fields
- `workflow_version_id`
- `workflow_id`
- `version`
- `lifecycle_state`
- `change_summary`
- `validation_status`
- `approved_by`
- `approved_at`
- `artifact_hash`

### Invariants
- exactly zero or one version is active per workflow per environment
- version artifacts are immutable after approval

## 9. Policy

### Purpose
Defines governance constraints for workflows, skills, agents, tenants, and actions.

### Ownership
Governance and risk.

### Stable Fields
- `policy_id`
- `name`
- `policy_type`
- `owner_team`
- `scope`
- `status`

### Versioned Fields
- `version`
- `conditions`
- `actions`
- `approval_requirements`
- `exception_rules`
- `evidence_requirements`

### Invariants
- policies must be independently versionable from workflows
- production policy exceptions must be time-bound and auditable

## 10. Run

### Purpose
Represents a single execution of a workflow version.

### Ownership
Journey orchestration runtime.

### Minimum Fields
- `run_id`
- `tenant_id`
- `environment_id`
- `workflow_id`
- `workflow_version_id`
- `entry_channel`
- `initiator_type`
- `initiator_id`
- `status`
- `started_at`
- `completed_at`
- `correlation_id`

### Invariants
- every run must reference the exact workflow version used
- terminal statuses must be explicit
- all run mutations must be append-only in event history

## 11. Run Step

### Purpose
Represents a single executed step within a run.

### Ownership
Journey orchestration runtime.

### Minimum Fields
- `run_step_id`
- `run_id`
- `step_name`
- `step_type`
- `sequence_number`
- `agent_id`
- `skill_id`
- `status`
- `started_at`
- `completed_at`
- `input_ref`
- `output_ref`

### Invariants
- steps must preserve execution order and causality
- failed steps must declare failure reason and retry state

## 12. Event

### Purpose
Represents an immutable fact emitted by the system.

### Ownership
Shared event model.

### Minimum Fields
- `event_id`
- `event_type`
- `resource_type`
- `resource_id`
- `tenant_id`
- `environment_id`
- `timestamp`
- `actor_type`
- `actor_id`
- `payload`

### Invariants
- events are immutable
- sensitive fields must be redacted according to data policy

## 13. Evaluation Result

### Purpose
Represents the assessment of run quality, safety, cost, and business performance.

### Ownership
Analytics and evaluation.

### Minimum Fields
- `evaluation_id`
- `run_id`
- `tenant_id`
- `quality_score`
- `safety_score`
- `cost_score`
- `business_outcome_score`
- `evaluated_at`

### Invariants
- evaluation criteria must be versioned
- evaluation should preserve raw evidence references where allowed

## 14. Deployment Promotion

### Purpose
Represents the promotion of a workflow, skill, or policy version into an environment.

### Ownership
Release governance.

### Minimum Fields
- `promotion_id`
- `resource_type`
- `resource_id`
- `resource_version`
- `source_environment`
- `target_environment`
- `status`
- `requested_by`
- `approved_by`
- `promoted_at`

### Invariants
- production promotions require explicit approval
- rollback must reference the superseded version

## 15. Approval Decision

### Purpose
Represents a governed decision for release, exception, or risky workflow action.

### Ownership
Governance and risk.

### Minimum Fields
- `approval_id`
- `approval_type`
- `subject_type`
- `subject_id`
- `decision`
- `decided_by`
- `decided_at`
- `rationale`

### Invariants
- approvals must preserve full decision history
- denials and overrides must be audit logged

## Relationship Model

High-level relationships:
- one `Tenant` has many `Workflow`, `Agent`, `Run`, and policy bindings
- one `Workflow` has many `WorkflowVersion`
- one `WorkflowVersion` references many step definitions
- step definitions reference `Agent`, `Skill`, and `Policy`
- one `Run` references one `WorkflowVersion`
- one `Run` has many `RunStep` and `Event`
- one `EvaluationResult` belongs to one `Run`
- one `DeploymentPromotion` targets one versioned resource

## Minimum API Contract Rules

Each top-level resource API should expose:
- list
- get detail
- create draft or initial record
- update draft where applicable
- validate
- approve where applicable
- activate or promote where applicable
- audit history

## Minimum Persistence Rules

Each versioned resource should separate:
- stable identity table
- version table
- activation or promotion table
- audit or event history

## Current Repository Mapping

Current code to future resource mapping:
- current journey code paths map to future `Workflow` and `WorkflowVersion`
- current plugin modules map to future `Skill`
- current tenant config maps to future `Tenant`
- current runs and events already map partially to future `Run` and `Event`
- current replay and scoring logic map to future `Run`, `RunStep`, and `EvaluationResult`

## Near-Term Implementation Recommendation

Implement in this order:

1. `Workflow` and `WorkflowVersion`
2. `DeploymentPromotion`
3. `Run` linkage to workflow versions
4. `Agent`
5. `Skill`
6. `Policy`

This order best fits the current repository and the control-plane-first strategy.
