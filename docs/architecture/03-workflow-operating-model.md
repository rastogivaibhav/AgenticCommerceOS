# ACOS Workflow Operating Model

## Purpose

This document defines how ACOS should think about workflows, agents, skills, runs, and operator controls.

## Core Control-Plane Objects

### Tenant
The business boundary for data, config, access, policy, and reporting.

### Agent
A named execution role with a purpose, allowed skills, model profile, operating budget, and escalation rules.

### Skill
A reusable capability with typed input and output contracts.
Examples:
- catalog lookup
- price quote
- loyalty adjustment
- order status lookup
- return initiation
- explanation generation

### Workflow
A directed, versioned execution plan that coordinates agents and skills.

### Policy
The rules that constrain workflow execution.
Examples:
- refund thresholds
- approval requirements
- model restrictions
- tenant-specific data rules

### Run
A single execution instance of a workflow.

### Event
A timestamped fact emitted during execution.

### Evaluation
A post-run assessment of quality, safety, cost, and business outcome.

## Workflow Types

The current codebase already hints at five journey families:
- discovery
- purchase
- post_purchase
- service
- engagement

These should become explicit workflow families with versioned definitions.

## Workflow Lifecycle

A workflow should progress through these states:

1. Draft
Being authored or edited.

2. Validated
Schema, dependency, and policy checks passed.

3. Approved
Ready for promotion.

4. Deployed
Active in a target environment.

5. Running
Processing live work.

6. Paused
Temporarily unavailable for new executions.

7. Deprecated
Not used for new executions but still visible for history and replay.

## Run Lifecycle

Every run should follow a visible lifecycle:

1. Accepted
Request validated and correlated.

2. Context Built
Tenant, customer, policy, and workflow inputs resolved.

3. Workflow Selected
Target workflow version chosen.

4. Steps Executed
Each step emits status and structured output.

5. Policy Evaluated
Safety, financial, and governance checks applied.

6. Completed Or Escalated
Result delivered, queued for human action, or failed with reason.

7. Evaluated
Quality and business metrics computed.

## Workflow Step Types

Allowed step categories should include:
- decision
- action
- retrieval
- tool invocation
- AI generation
- policy check
- approval gate
- wait or callback
- compensation
- notification

## Governance Rules

### Deterministic Services For Critical Actions
Pricing, checkout, order mutation, refunds, and loyalty updates should not rely on free-form model output.

### AI For Reasoning At The Edges
Use LLMs where the value is classification, explanation, summarization, suggestion, or operator assistance.

### Human Review For Risky Mutations
High-value, policy-sensitive, or customer-impacting actions should support approval gates.

## Operator Controls

The control plane should let operators:
- inspect workflow versions
- see current deployments
- review run timelines
- replay runs against historical or new versions
- pause agents or workflows
- approve or reject gated actions
- compare experiment variants

## Event Model

Every run should emit consistent events such as:
- run.accepted
- run.context_resolved
- workflow.selected
- step.started
- step.completed
- step.failed
- policy.checked
- run.escalated
- run.completed
- evaluation.completed

## Versioning Model

The following resources must be versioned independently:
- workflow definitions
- prompts
- skills
- policies
- UI contract surfaces
- connector adapters

## Workflow Authoring Rules

To keep the platform modular and shippable:
- start with small workflows
- keep side effects explicit
- separate read steps from write steps
- define rollback or compensation for mutations
- attach policy checks before irreversible actions
- define expected telemetry for each step

## Current Baseline And Migration Path

Current state:
- workflows are implicit Python code paths
- routing is keyword-based
- steps are not yet first-class persisted workflow resources

Migration path:
- keep current coded workflows working
- add persisted workflow metadata first
- then externalize definitions and step schemas
- then add visual authoring and deployment promotion

## Enterprise Success Criteria

ACOS workflow operations are enterprise-grade when:
- workflows are versioned and promotable
- runs are replayable and auditable
- risky actions are governed
- tenant isolation is guaranteed
- every live step is observable
