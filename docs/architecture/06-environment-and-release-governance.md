# ACOS Environment And Release Governance

## Purpose

This document describes the release and runtime-governance mechanisms that are already present in ACOS, plus the hardening work that is still needed.

## Governance Principles

### Versioned Promotion
Live behavior should change by activating specific workflow versions, not by mutating an implicit draft in place.

### Environment Awareness
Promotion and execution need to carry environment identity explicitly.

### Evidence And Audit
Operational mutations should leave promotion or audit records that operators can inspect later.

### Safe Fallbacks
Connectors and AI runtimes should degrade to preview or sandbox behavior when live dependencies are not ready.

## Current Environment Model

The current code uses:
- `OPS_ENVIRONMENT` to identify the running service environment
- `environment_id` on runs
- `target_environment` and `source_environment` on workflow promotions
- environment-specific filtering for channel bindings and workflow activation

The repo does not yet implement a first-class `environments` table, but environment identity is already operationally meaningful.

## Current Promotion Model

Workflow release governance is the most mature release mechanism in the codebase.

Current implementation supports:
- creating a workflow version
- approving a version
- promoting a version into an environment
- rolling back to a prior version
- archiving a workflow

Promotion state is stored in `workflow_promotions`, and workflow execution resolves active versions from that state.

## Current Runtime Governance Controls

The platform already includes:
- role-gated ops endpoints
- workflow approval and promotion flows
- audit event storage
- workflow rollback
- incident endpoints for workflow health, pause, failsafe, rollback, and audit lookup
- tenant traffic controls in `shopper-api`
- row-level security for context and governance tables

## Current Connector Release Behavior

Connector behavior is intentionally staged:
- `sandbox` when the connector is not configured
- `configured_preview` when credentials exist but a live action is intentionally not executed
- `live` when the connector is configured and the action is allowed

This gives ACOS a practical release-safety mechanism for external systems even before a fuller connector registry exists.

## Mock And Demo Guardrails

The repository includes explicit controls for mock-route exposure:
- `ALLOW_MOCK_ROUTES`
- `ALLOW_NON_DEV_MOCK_ROUTES`

`ops-api` blocks non-dev mock routes unless the explicit override is set, which is an important current safeguard.

## Release Artifact Reality

Today the most concrete promotable artifact in ACOS is the workflow version plus its environment promotion record.

Agents, skills, connectors, and UI behavior are still more lightly governed than workflows, even though they are operationally important.

## Current Promotion Readiness Checks

The codebase already makes room for release checks through:
- startup auth validation
- schema readiness checks
- health endpoints
- metrics endpoints
- workflow validation status fields
- audit and promotion history
- runbooks and evidence-pack docs in `docs/`

What is still mostly process-driven rather than fully enforced in code:
- artifact hashing
- automated environment-specific validation gates for every promotable object
- uniform dependency validation across workflow, agent, skill, and connector changes

## Practical Environment Semantics Today

### Dev
- default environment for local work
- sandbox connectors and mock routes are expected here

### Stage/Test
- supported by workflow promotion fields and environment parameters
- not yet represented as separate deployment stacks in the repo

### Prod
- represented in promotion targets and runtime metadata
- should run with mock routes disabled, stricter auth, and fully configured connectors

## Rollback Model

Rollback currently works best at the workflow level:
- identify the prior version
- reactivate it for the target environment
- audit the action
- replay or inspect affected runs

This is a meaningful operational capability that already exists in the codebase.

## Remaining Governance Gaps

The biggest gaps are:
- no first-class promotion system yet for agent versions, skill versions, or connector contracts
- no unified release object spanning workflow, UI, connectors, and runtime provider changes
- limited automated enforcement of evidence requirements before promotion
- partial reliance on demo data and sandbox flows for some operational paths

## Near-Term Governance Direction

The most valuable next hardening steps are:
- extend version/promotion concepts beyond workflows
- validate workflow graphs and dependencies more strictly before approval
- make release evidence more machine-checkable
- keep production behavior safely separated from demo and mock paths
