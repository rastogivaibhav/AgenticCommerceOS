# ACOS Vision And Principles

## Working Product Definition

ACOS stands for Agentic Commerce Operating System.

In the current repository, ACOS is best described as a governed commerce runtime and operations plane:
- a shopper-facing journey runtime
- a control plane for workflow and operational governance
- a chat and channel intake layer
- a shared persistence and connector substrate for retail service flows

It is no longer just a thin prototype, but it is also not yet a fully hardened enterprise platform across every domain and environment.

## What The Repository Contains Today

The codebase already implements:
- `shopper-api` for authenticated journey execution
- `ops-api` for workflow lifecycle, agents, skills, channels, runs, replay, analytics, audit, and incident controls
- `chat-api` for Slack and message-driven workflow execution
- a React control-plane UI served by `ops-api`
- persisted workflow versions and promotions
- a graph-based workflow executor for saved workflows
- demo retail routing across WhatsApp, Telegram, Shopify, and Salesforce
- tenant-aware context, governance, rate limiting, metrics, and audit foundations

## Product Direction

ACOS is evolving toward a platform with five tightly connected layers:

1. Commerce Runtime
Journey execution for discovery, purchase, post-purchase, service, and engagement flows.

2. Workflow Orchestration
Versioned workflow definitions, graph execution, promotion, rollback, replay, and operational controls.

3. Agent And Skill System
Named agents, reusable skills, runtime-provider selection, connector bindings, and governed execution contracts.

4. Control Plane
The operator surface for workflows, analytics, channels, tenants, incidents, approvals, and investigation.

5. Platform Foundation
Tenancy, security, persistence, observability, release governance, and evidence-backed operations.

## Core Vision Statement

ACOS provides a governed environment where AI-assisted commerce work can run across shopper, service, and operator workflows with explicit versions, observable execution, and human-operable controls.

## Business Outcomes

ACOS is intended to support:
- faster customer resolution across retail journeys
- safer adoption of AI-assisted execution through audit, replay, and approval
- reusable commerce workflow infrastructure rather than one-off agents
- better operator confidence through explicit runtime state and investigation surfaces
- channel-aware automation that still preserves escalation and rollback paths

## Architectural Principles

### 1. Runtime And Control Plane Stay Separate
Live customer execution and operational governance are implemented as distinct services with different auth models and responsibilities.

### 2. Workflow State Must Be Explicit
ACOS can use LLMs for reasoning, but workflow identity, version, promotion state, step graph, and operator actions must stay visible and structured.

### 3. Deterministic Systems Stay In The Loop
Commerce mutations and system-of-record lookups should go through typed connectors and business services, not free-form model output alone.

### 4. Human Override Is A Product Feature
Pause, replay, approval, rollback, escalation, and notification are core behaviors, not afterthoughts.

### 5. Tenant And Environment Boundaries Matter
Data, traffic limits, context access, and promotion state all need tenant- and environment-aware handling.

### 6. Evidence Beats Aspirational Docs
Architecture docs should describe what the code actually does today, then call out the remaining gaps clearly.

### 7. Vertical Slices Over Abstract Frameworks
ACOS should continue shipping end-to-end slices such as workflow execution, channel intake, and connector-backed service support instead of building disconnected infrastructure first.

## Product Design Principles

### Operator Confidence Over Magic
The system should make it obvious which workflow ran, which version was active, which connectors were touched, and how a case was escalated.

### Sandbox Before Live
Connector actions should degrade honestly to preview or sandbox modes when live dependencies are not ready.

### Retail-Specific, Not Generic Automation
The system is oriented around commerce journeys, retail service flows, CRM context, and governed operational execution.

## Strategic Framing

The most accurate short description of ACOS today is:

"A commerce-focused AI runtime and control plane with persisted workflows, graph execution, channel demos, connector probes, and operator governance surfaces."
