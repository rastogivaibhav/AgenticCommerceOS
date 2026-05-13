# PRD: ACOS Control Plane Foundation

## Document Status

Working PRD for the next durable product slice.

## Product Name

ACOS Control Plane Foundation

## Product Thesis

Before ACOS can become a full operating system for AI-driven commerce, it needs a trustworthy control-plane foundation that replaces demo-only behavior with versioned, inspectable, and governed operational capabilities.

## Problem Statement

The current project can execute prototype commerce journeys, but operators do not yet have an enterprise-grade way to:
- manage workflows as products rather than code paths
- inspect runs with clear operational semantics
- control agent and skill behavior through governed configuration
- ship frontend and backend changes as one coherent, containerized product surface

## Users

### Operations Lead
Needs visibility into runs, errors, costs, and throughput.

### AI Product Manager
Needs safe experimentation, version tracking, and measurable rollout control.

### Support And Service Ops
Needs run inspection, replay, and escalation support.

### Platform Engineer
Needs containerized deployability, telemetry, and clear service boundaries.

### Compliance And Risk Owner
Needs audit, policy visibility, and tenant-safe controls.

## Goals

### Goal 1
Ship a real control-plane foundation that is more than a static dashboard.

### Goal 2
Introduce first-class managed resources for workflows, agents, or skills in a way that is visible in the UI and persisted in storage.

### Goal 3
Keep every iteration runnable through Docker Compose.

### Goal 4
Establish enterprise-grade delivery discipline for future prompts.

## Non-Goals

- fully replacing all mocked domain systems
- building every advanced editor described in the aspirational V2 plan
- introducing production-grade multi-region infrastructure in one step

## Baseline Reality

Today:
- the execution model lives mostly in Python code
- the ops dashboard is mainly inline HTML served by the API
- the Vite React app exists but is not the real product
- runs and events exist, but workflow resources do not yet exist as managed entities

## MVP Scope

The first control-plane foundation should include:

### 1. Control-Plane Resource Model
At least one first-class managed entity persisted in Postgres and exposed via API and UI.
Recommended starting entity:
- Workflow Definitions

### 2. Versioned API Surface
Ops APIs for:
- list workflows
- get workflow detail
- create or update draft workflow
- activate a workflow version
- list runs by workflow

### 3. Real Control-Plane UI
A React-based UI that replaces at least one inline HTML operational surface.

### 4. Dockerized Delivery
The full slice must build and run from Docker Compose.

### 5. Trust Signals
The slice must include:
- authentication
- audit events for control-plane mutations
- health checks
- metrics
- automated tests

## Functional Requirements

### FR-1
Operators can view a list of workflow definitions and their status.

### FR-2
Operators can view workflow versions and activation state.

### FR-3
Operators can inspect runs associated with a workflow.

### FR-4
Operators can create or edit workflow metadata in draft state.

### FR-5
Operators can activate a workflow version through a governed API path.

### FR-6
The UI is served as a real built frontend artifact, not an inline script blob.

## Non-Functional Requirements

### NFR-1
The slice runs locally through Docker Compose with documented startup steps.

### NFR-2
All new control-plane resources are tenant-aware.

### NFR-3
All mutation endpoints produce audit events.

### NFR-4
All new APIs are versioned and typed.

### NFR-5
Tests cover API behavior, persistence, and at least one UI integration path where practical.

## Success Metrics

### Delivery Metrics
- container build passes
- compose startup succeeds
- health endpoints are green
- tests pass in CI or local verification environment

### Product Metrics
- operators can inspect workflow inventory without code access
- operators can identify which workflow version produced a run
- control-plane mutations are observable and auditable

## Acceptance Criteria

- a user can run the slice with Docker Compose
- the ops UI shows real control-plane data from the API
- at least one managed entity is persisted and versioned
- audit, metrics, and health behavior are part of the slice
- the implementation leaves the codebase in a cleaner architectural state than before

## Risks

- trying to build the full future dashboard too early
- over-investing in visual design before operational semantics are stable
- adding resource models without clear runtime ownership

## Recommended Follow-On PRDs

After this foundation, future slices should target:
- Agent Registry
- Skill Registry
- Workflow Simulation
- Policy And Approval Gates
- Evaluation And Experiment Operations
