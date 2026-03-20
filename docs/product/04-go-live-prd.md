# PRD: ACOS Go-Live Foundation

## Purpose

This document defines the product and platform requirements for ACOS to be considered go-live ready for an initial enterprise deployment.

It is not the PRD for the final vision.
It is the PRD for the first release that can be responsibly put in front of a real enterprise pilot or controlled production scope.

## Product Definition

ACOS go-live means:

- a governed control plane exists
- versioned workflows can be promoted safely
- runs are observable and replayable
- operator responsibilities are clear
- release governance is enforceable
- the platform delivers measurable retail value in a bounded scope

## Proposed Initial Go-Live Scope

Recommended bounded scope:
- one or two tenants
- a limited set of workflow families
- low to medium operational risk actions first

Recommended initial workflow families:
- discovery
- post_purchase order status
- service guidance without uncontrolled financial mutation
- controlled returns initiation with policy guardrails

## Why This Scope

This sequence matches the current repository direction while avoiding overreach into the hardest enterprise areas too early.

## Go-Live Users

- Commerce Operations Lead
- Service Operations Lead
- Workflow Administrator
- Platform Engineer
- AI Product Manager
- Risk And Compliance Owner

## Goals

### Goal 1
Operate ACOS as a real enterprise control plane, not a prototype dashboard.

### Goal 2
Support safe, observable, governed workflow execution across a bounded retail scope.

### Goal 3
Demonstrate business value and operational trust in a pilot environment.

## Non-Goals

- broad omnichannel enterprise rollout on day one
- replacement of all systems of record
- unrestricted autonomous financial actions

## Go-Live Functional Requirements

### GR-1 Workflow Management
Operators can list, inspect, version, and activate workflow definitions.

### GR-2 Version-Aware Execution
Every run records the workflow version used.

### GR-3 Run Investigation
Operators can inspect a run timeline with step, policy, and outcome visibility.

### GR-4 Replay
Operators can replay runs with governed access.

### GR-5 Approval Controls
Production promotions and risky policy-sensitive actions require explicit approval where configured.

### GR-6 Auditability
Control-plane mutations and risky runtime decisions generate audit evidence.

### GR-7 Tenant Awareness
All relevant control-plane data and workflows are tenant-aware.

### GR-8 Real React Control Plane
At least the foundational operational views are delivered through the real frontend, not only inline API HTML.

## Go-Live Non-Functional Requirements

### GNFR-1 Containerized Operation
The full initial release runs through Docker Compose or an equivalent container deployment model.

### GNFR-2 Security
Auth, role enforcement, secrets handling, and audit requirements are in place for the live scope.

### GNFR-3 Observability
Logs, metrics, and health endpoints are sufficient for pilot operations.

### GNFR-4 Reliability
Critical workflows support retries, failure visibility, and safe fallback behavior.

### GNFR-5 Data Governance
Sensitive data handling and tenant isolation rules are implemented for the pilot scope.

### GNFR-6 Release Governance
Promotion and rollback are documented and operationally usable.

## Retail Business KPIs

The go-live pilot should measure:
- containment rate for supported journeys
- first-contact resolution rate
- median time to resolution
- run failure and escalation rate
- operator replay rate
- cost per resolved interaction
- customer satisfaction proxy or explicit score where available

## Product Success Criteria

ACOS go-live is successful when:
- operators can safely manage workflow versions without editing code
- failures can be investigated quickly through the control plane
- pilot workflows produce measurable service or commerce value
- release risk is controlled through approvals and rollback

## Required Architectural Foundations

The following documents are considered normative dependencies for go-live:
- vision and principles
- reference architecture
- workflow operating model
- canonical resource model
- retail capability map
- environment and release governance
- operator journeys and RACI
- design library

## Acceptance Criteria

To call ACOS go-live ready for the initial scope, all of the following must be true:

- versioned workflow resources exist in persistence
- runs reference workflow versions
- control-plane UI exposes workflow and run investigation surfaces
- promotions are environment-aware and auditable
- risky changes have approval support
- health and metrics exist for the live slice
- Dockerized startup path is documented and working
- pilot KPIs are measurable

## Delivery Sequence To Reach Go-Live

### Slice A
Workflow registry and version model.

### Slice B
React control-plane foundation with workflow inventory and run list.

### Slice C
Workflow detail, promotion path, and audit coverage.

### Slice D
Run timeline, replay, and policy visibility.

### Slice E
Approval queue, release governance support, and production readiness checklist.

## Risks To Go-Live

- treating mocked domain behavior as if it were production truth
- shipping workflow activation without clear approval ownership
- building a UI that looks complete but lacks operational causality
- lacking reliable environment and rollback controls

## Exit Decision

ACOS should only go live when the initial bounded scope is both:
- operationally controllable
- commercially meaningful

If either is missing, the release is still a prototype, not a product launch.
