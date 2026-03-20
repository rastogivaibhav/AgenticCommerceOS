# ACOS Environment And Release Governance

## Purpose

This document defines how ACOS resources move from authoring to go-live.

An enterprise operating system for AI-driven commerce cannot rely on ad hoc deployment or undocumented approval paths.

## Governance Principles

### Separation Of Duties
The same individual should not unilaterally author, approve, and promote high-risk changes into production.

### Evidence-Based Promotion
Changes must carry validation evidence before promotion.

### Versioned Promotion
Promotions happen by promoting versioned artifacts, not mutable drafts.

### Safe Rollback
Every production promotion must define a rollback path.

## Environment Model

ACOS should operate with at least these environments:

### Dev
Used for active development and rapid iteration.

### Test
Used for functional integration, contract validation, and automated test execution.

### Stage
Used for realistic pre-production validation with release candidates.

### Prod
Used for live business traffic and governed operational execution.

## Resource Promotion Scope

The following resources require environment-aware promotion:
- workflow versions
- agent versions
- skill versions
- policy versions
- connector versions or config changes
- UI releases where they affect control-plane behavior

## Release Artifact Model

Every promotable artifact should include:
- resource identity
- version number
- artifact hash
- change summary
- validation evidence
- dependency declarations
- rollback target

## Validation Gates By Environment

### Dev To Test
Minimum requirements:
- unit tests pass
- schema validation passes
- API and UI contracts build
- Docker build passes

### Test To Stage
Minimum requirements:
- integration tests pass
- migration safety reviewed
- tenant behavior validated
- audit and metrics behavior validated
- release notes prepared

### Stage To Prod
Minimum requirements:
- release candidate validated in near-production conditions
- approvals complete
- rollback plan documented
- runbooks current
- risk sign-off complete for affected areas

## Approval Model

### Low-Risk Changes
Examples:
- copy updates
- harmless UI refinement
- non-production test fixtures

Approval:
- product or engineering owner

### Medium-Risk Changes
Examples:
- workflow logic changes
- skill contract changes
- new control-plane mutations

Approval:
- engineering owner
- product owner

### High-Risk Changes
Examples:
- production policy changes
- financial action thresholds
- refund approval logic
- model profile changes affecting live customer outputs
- connector changes to systems of record

Approval:
- engineering owner
- business owner
- risk or compliance owner where applicable

## Production Change Types

### Planned Release
Normal promotion through approval and release windows.

### Emergency Fix
Fast-track release with mandatory retrospective review.

### Feature Flag Rollout
Change is promoted but activated only for targeted traffic.

## Rollback Rules

Every production release must define:
- the prior stable version
- rollback conditions
- rollback owner
- rollback validation steps

Rollback should prefer:
- version reactivation
- feature flag disablement
- connector fail-safe routing

## Release Readiness Checklist

Before production promotion, confirm:
- affected tenants identified
- affected workflows identified
- backward compatibility assessed
- metrics and dashboards updated if needed
- audit coverage present
- support teams informed if needed
- operational runbooks updated

## Runtime Governance

Deployment governance alone is not enough.
Live runtime must also support:
- pausing a workflow version
- pausing an agent version
- blocking a skill version
- requiring manual approval for risky live actions
- routing to human fallback when policy confidence is low

## Environment Data Rules

### Dev And Test
- synthetic or sanitized data only
- no production secrets

### Stage
- controlled sanitized datasets
- production-like config with safe boundaries

### Prod
- full policy and audit enforcement
- least-privilege access
- redaction of sensitive operational views where required

## Release Governance Roles

- Product Owner
  accountable for business intent and release value
- Engineering Owner
  accountable for technical correctness and rollback
- Platform Owner
  accountable for deployment safety and runtime health
- Risk And Compliance Owner
  accountable for policy-sensitive release oversight
- Operations Owner
  accountable for adoption readiness and incident handling

## Current Repository Implications

Near-term governance improvements should include:
- explicit environment variables for environment identity
- versioned workflow records
- promotion records in persistence
- audit events for activation and mutation
- a documented release candidate path through Docker Compose

## Go-Live Standard

ACOS is go-live capable only when:
- all production-facing resources are versioned
- promotions are approved and auditable
- rollback is operationally simple
- runtime kill switches exist
- release evidence is preserved
