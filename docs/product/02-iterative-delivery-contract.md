# Iterative Delivery Contract

## Purpose

This document defines how future prompts should be translated into shippable ACOS slices.

The rule is simple:
every prompt should produce a deployable improvement, not disconnected partial work.

## Delivery Philosophy

Favor vertical slices over horizontal scaffolding.

Good:
- a workflow inventory page backed by a real API and database table

Bad:
- adding half of a registry, part of a page, and placeholder routes that do not ship

## Mandatory Ship Criteria Per Prompt

Each future slice must satisfy all of the following unless explicitly exempted:

### 1. Runnable
The result must run from Docker or Docker Compose.

### 2. Valuable
The slice must create a real operator, platform, or customer-facing outcome.

### 3. Integrated
Frontend, backend, persistence, and docs should align where the slice touches them.

### 4. Verifiable
The work must include the strongest available verification in the environment.

### 5. Reversible
The slice should avoid dead-end design choices and should support safe iteration.

## Enterprise-Grade Definition Of Done

For any feature-bearing prompt, the default definition of done is:

- code builds
- containers start
- health checks pass
- authentication is enforced where needed
- tenant behavior is considered
- persistence changes are migration-safe
- logs and metrics are not degraded
- tests are added or updated
- docs are updated
- no feature is left as a misleading stub

## Prompt Planning Template

Every implementation prompt should answer:

1. What is the user-visible or operator-visible outcome?
2. What is the smallest shippable slice that achieves it?
3. Which service, API, UI, and data changes are required?
4. How will it run in Docker?
5. How will it be verified?

## Preferred Sequence Of Modular Slices

### Slice 1
Control-plane foundation with real React-served UI and a first-class resource model.

### Slice 2
Workflow registry and version activation.

### Slice 3
Run timeline and replay experience tied to workflow versions.

### Slice 4
Agent registry with allowed skills and execution policies.

### Slice 5
Skill registry with schemas, connector metadata, and validation.

### Slice 6
Policy gates and approval workflows for sensitive actions.

### Slice 7
Simulation, evaluation, and experimentation operations.

## Technical Guardrails

### Do Not Replace The Whole Stack At Once
Evolve the current services incrementally.

### Do Not Introduce UI Without Data Contracts
Every page must have a stable API and typed resource model.

### Do Not Add Claims Without Evidence
If a feature is marked complete, it must exist in code and be runnable.

### Do Not Keep Dual Product Surfaces Longer Than Necessary
If React becomes the primary ops UI, the inline HTML dashboard should be retired slice by slice.

## Containerization Rules

Each slice should leave the repo in a state where:
- services have clear startup commands
- dependencies are installable in image build
- environment variables are documented
- health endpoints reflect meaningful readiness

## Documentation Rules

Each slice should update only the docs affected by the change:
- PRD when scope changes
- reference architecture when boundaries change
- design library when UI patterns change
- README or runbook when startup changes

## Quality Gates For Future Work

Before calling a slice done, verify:
- no aspirational README text contradicts implementation
- task tracking reflects reality
- demo data does not violate current validation rules
- tests cover the critical path

## Working Principle

One prompt, one shippable product improvement.
If a prompt is too broad, narrow it into the next best enterprise-safe slice.
