# ACOS Workflow Operating Model

## Purpose

This document explains how workflows operate in the current ACOS implementation: how they are defined, versioned, executed, promoted, and observed.

## Core Workflow Objects

### Workflow

A workflow is the stable business identity.

Current persisted fields include:
- `id`
- `tenant_id`
- `name`
- `workflow_family`
- `description`
- `business_owner`
- `status`

### Workflow Version

A workflow version is the deployable artifact.

Current persisted fields include:
- `workflow_id`
- `version`
- `lifecycle_state`
- `change_summary`
- `validation_status`
- `step_definitions`
- `agent_bindings`
- `policy_bindings`
- `input_schema`
- `output_schema`
- `created_by`
- `approved_by`
- `approved_at`

### Workflow Promotion

Promotion records track environment activation.

Current fields include:
- `workflow_id`
- `version`
- `source_environment`
- `target_environment`
- `status`
- `is_active`
- `requested_by`
- `approved_by`
- `note`
- `promoted_at`

### Run

A run is a specific execution of either:
- shopper journey runtime execution
- or saved workflow graph execution

Runs store workflow identity, version, environment, inputs, outputs, cost, score, and execution metadata.

## Workflow Families In Use Today

The code currently seeds and resolves these workflow families:
- `discovery`
- `purchase`
- `post_purchase`
- `service`
- `engagement`

There is also a concrete seeded demo workflow:
- `wf-order-support-demo`

## Workflow Definition Model

Saved workflows are currently represented as graph-shaped `step_definitions`.

The active UI and executor both assume a graph with:
- `nodes`
- `edges`

### Node Types Currently Implemented

- `triggerNode`
  - captures inbound context such as channel, message, customer, and order reference
- `connectorNode`
  - invokes Shopify, Salesforce, WhatsApp, or Telegram actions
- `agentNode`
  - invokes the ADK runtime layer using the configured or requested provider
- `decisionNode`
  - branches based on simple workflow state and prior results
- `humanNode`
  - opens or updates downstream escalation state
- `endNode`
  - records the terminal workflow outcome

## Execution Modes

### 1. Family-Based Shopper Execution

`shopper-api` uses `journey.engine.run_journey` to:
- infer or accept a `journey_type`
- resolve the active workflow for that family and environment
- execute the coded commerce chain
- enrich with AI runtime output, governance, scoring, cost, metrics, traces, and context

This is the customer-facing runtime path.

### 2. Saved Workflow Graph Execution

`ops-api` uses `workflows.executor.execute_saved_workflow` to:
- load the selected workflow and version
- extract the active graph
- execute nodes in dependency order
- record `node_trace` and `tool_trace`
- persist the run

This is the control-plane and channel-demo execution path.

## Default Seeded Workflow Shape

Most seeded workflow families start with a simple graph:
- one trigger node
- one agent node
- one end node

The order-support demo workflow is richer and currently includes:
- WhatsApp inbound trigger
- Shopify order lookup
- Salesforce customer lookup
- support agent
- auto-resolution decision
- WhatsApp reply
- human escalation
- terminal resolved or escalated outcomes

## Workflow Lifecycle In Practice

The current codebase supports this practical lifecycle:

1. Draft
- workflow or version is created
- version starts with draft validation and lifecycle state unless seeded

2. Approved
- version can be approved through ops routes
- approval metadata is stored

3. Promoted
- a version is activated for an environment through a promotion record
- only one active version per workflow/environment should be treated as live

4. Executed
- shopper runtime or saved workflow execution selects the active version

5. Rolled Back
- ops routes can reactivate an earlier version for the environment

6. Archived
- workflows can be archived through the ops API

## Operator Controls Implemented Today

Operators can currently:
- list workflows and workflow details
- create workflows and versions
- approve versions
- promote versions across environments
- roll back versions
- archive workflows
- execute a workflow directly
- run workflow test calls
- inspect runs tied to a workflow
- replay runs
- inspect incident and audit surfaces

These controls are available through `ops-api`, and the main workflow authoring and inspection surfaces are exposed in the React UI.

## Workflow-Adjacent Objects

The operating model also depends on:
- agents
- skills
- tenants
- channel bindings
- channel senders
- channel pairings
- demo routes
- CRM customers and cases

These objects are now part of workflow execution, especially for retail service flows.

## Current Observability Model

Shopper runtime executions record:
- traces
- metrics
- run records
- events
- cost
- score
- context session and memory updates

Saved workflow graph executions record:
- run records
- workflow version and environment
- `node_trace`
- `tool_trace`
- channel reply artifacts
- escalation artifacts

## Current Governance Model

Workflow operations already use:
- JWT role checks on ops endpoints
- audit event logging for sensitive mutations
- environment-aware promotion records
- tenant-aware execution metadata

The saved workflow executor does not yet enforce a fully generic policy engine for every node type, so that remains a hardening area rather than a missing architecture concept.

## Known Limitations

- shopper runtime and saved workflow graph execution are related but not fully unified into one execution engine
- workflow validation is still lighter than a full static contract and dependency checker
- policy bindings exist in the schema, but enforcement is not yet uniformly applied at every graph step
- long-running wait/callback/compensation patterns are not first-class graph nodes yet

## Near-Term Direction

The implementation should continue by:
- strengthening graph validation
- making agent and connector bindings more explicit at version boundaries
- expanding incident and approval hooks around live workflow execution
- converging family-based and graph-based execution where that improves operator clarity
