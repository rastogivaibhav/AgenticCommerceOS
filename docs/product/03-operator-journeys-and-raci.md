# ACOS Operator Journeys And RACI

## Purpose

This document defines who uses the ACOS control plane, what they need to do, and who is responsible for what.

The intent is to turn the UX and architecture into a real operating model for enterprise teams.

## Primary Roles

### AI Product Manager
Owns business goals, rollout intent, and experiment framing.

### Commerce Operations Lead
Owns day-to-day business operations and performance oversight.

### Service Operations Lead
Owns service workflow quality, escalations, and customer outcomes.

### Platform Engineer
Owns deployment safety, runtime reliability, and observability.

### Workflow Administrator
Owns workflow configuration, lifecycle state, and validation readiness.

### Risk And Compliance Owner
Owns policy-sensitive review and approval.

### Analyst
Owns reporting, evaluation interpretation, and performance insights.

## Operator Journey 1: Review Workflow Inventory

### Goal
Understand which workflows exist, what version is active, and where risk or drift exists.

### Primary User
Workflow Administrator

### Steps
1. Open workflows inventory.
2. Filter by tenant, family, status, environment, or owner.
3. Inspect active version and last promotion state.
4. Identify workflows needing review, validation, or promotion.

### Required UX
- workflow inventory page
- status filters
- version and environment badges
- quick drill-in to workflow detail

## Operator Journey 2: Promote A Workflow Version

### Goal
Move a validated workflow version into the next environment safely.

### Primary User
Workflow Administrator

### Supporting Users
Product Owner, Engineering Owner, Risk And Compliance Owner

### Steps
1. Open workflow detail.
2. Review version diff, validation status, and linked dependencies.
3. Submit for approval if required.
4. Approve or reject.
5. Promote to target environment.
6. Monitor early run health and rollback signals.

### Required UX
- diff viewer
- approval timeline
- promotion dialog
- post-promotion health summary

## Operator Journey 3: Investigate A Failed Run

### Goal
Explain why a run failed and what should happen next.

### Primary User
Commerce Operations Lead or Service Operations Lead

### Steps
1. Open runs inventory.
2. Filter by failure, workflow, tenant, or time.
3. Open run detail.
4. Inspect timeline, steps, policy decisions, and payload references.
5. Decide whether to replay, escalate, or route to human handling.

### Required UX
- run timeline
- policy outcome panel
- step-level causality
- replay and escalation actions

## Operator Journey 4: Approve A Risky Action Or Release

### Goal
Provide governed approval for high-risk changes or live actions.

### Primary User
Risk And Compliance Owner

### Steps
1. Open approval inbox.
2. Review change context, affected tenant, and risk classification.
3. Review evidence and rollback plan.
4. Approve, reject, or request changes.

### Required UX
- approval queue
- evidence pack
- decision logging
- tenant and environment scope visibility

## Operator Journey 5: Evaluate Business Performance

### Goal
Understand whether AI-driven workflows are producing business value.

### Primary User
AI Product Manager and Analyst

### Steps
1. Open overview or analytics area.
2. Compare run volume, quality, cost, and business outcomes.
3. Identify improvement opportunities by workflow, tenant, or channel.
4. Create backlog or experiment actions.

### Required UX
- KPI overview
- workflow segmentation
- experiment comparison
- exportable or shareable insight views

## Operator Journey 6: Handle A Live Incident

### Goal
Reduce customer and business impact during a workflow, agent, or connector issue.

### Primary User
Platform Engineer and Commerce Operations Lead

### Steps
1. Detect abnormal error or latency signal.
2. Identify impacted workflow, agent, skill, or connector.
3. Pause or degrade affected execution path.
4. Activate rollback or fail-safe route.
5. Monitor recovery.
6. Capture incident notes and evidence.

### Required UX
- incident-oriented health views
- kill switches
- dependency mapping
- rollback shortcuts

## RACI Matrix

### Workflow Definition
- Responsible: Workflow Administrator
- Accountable: AI Product Manager
- Consulted: Commerce Operations Lead, Service Operations Lead
- Informed: Platform Engineer

### Workflow Promotion To Production
- Responsible: Workflow Administrator, Platform Engineer
- Accountable: Engineering Owner or Platform Owner
- Consulted: AI Product Manager, Risk And Compliance Owner
- Informed: Commerce Operations Lead, Service Operations Lead

### Policy Change
- Responsible: Risk And Compliance Owner
- Accountable: Risk And Compliance Owner
- Consulted: AI Product Manager, Engineering Owner
- Informed: Operations stakeholders

### Agent And Skill Approval
- Responsible: Workflow Administrator, Engineering Owner
- Accountable: Engineering Owner
- Consulted: Risk And Compliance Owner, AI Product Manager
- Informed: Operations stakeholders

### Run Investigation
- Responsible: Commerce Operations Lead or Service Operations Lead
- Accountable: Respective operations lead
- Consulted: Platform Engineer, Analyst
- Informed: AI Product Manager

### Incident Response
- Responsible: Platform Engineer
- Accountable: Platform Owner
- Consulted: Commerce Operations Lead, Risk And Compliance Owner
- Informed: AI Product Manager, Analyst

### Evaluation And Experiment Review
- Responsible: Analyst
- Accountable: AI Product Manager
- Consulted: Commerce Operations Lead, Service Operations Lead
- Informed: Platform Engineer

## UX Implications

The control plane should not be designed only as a dashboard.
It should support:
- work queues
- approvals
- investigations
- promotions
- incident response
- performance review

## Near-Term Product Recommendation

The first real control-plane UX should prioritize the roles and journeys that unlock safe operations earliest:

1. Workflow Administrator reviewing workflow inventory
2. Operations Lead investigating runs
3. Platform Engineer managing promotion and rollback
4. Risk Owner approving sensitive changes
