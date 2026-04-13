# ACOS Documentation Library

This folder is the architecture, product, and operational documentation set for the current ACOS codebase.

## Document Map

### Architecture
- `architecture/01-vision-and-principles.md`
- `architecture/02-reference-architecture.md`
- `architecture/03-workflow-operating-model.md`
- `architecture/04-canonical-resource-model.md`
- `architecture/05-retail-capability-map.md`
- `architecture/06-environment-and-release-governance.md`

### Product and Readiness
- `product/01-prd-control-plane-foundation.md`
- `product/02-iterative-delivery-contract.md`
- `product/03-operator-journeys-and-raci.md`
- `product/04-go-live-prd.md`
- `product/05-document-set-review.md`
- `product/weekly_readiness_journey.md`
- `product/week6_12_architecture_execution_plan.md`

### Evidence Packs
- `week11_uat_evidence_pack.md`
- `week12_production_gate_evidence_pack.md`

### Runbooks
- `observability/slo_runbook.md`
- `RUNBOOK_GO_LIVE.md`
- `RUNBOOK_WORKFLOW_PROMOTION.md`
- `RUNBOOK_INCIDENT_RESPONSE.md`

## How To Use This Library

- Use the architecture docs as the code-backed description of the current platform shape.
- Use product docs for roadmap intent, scope sequencing, and release-readiness decisions.
- Keep runbooks aligned with real API endpoints, workflow operations, and incident controls.
- Update the relevant architecture docs whenever the workflow model, persisted resources, channel model, or service topology changes.

## Current Baseline

ACOS currently includes:
- `shopper-api` for authenticated journey execution on `/v1/journey`
- `ops-api` for workflow governance, replay, channels, agents, skills, analytics, and `/ui`
- `chat-api` for Slack and message-driven workflow execution
- `apps/ops_ui_v2` for the React control-plane frontend
- PostgreSQL persistence for workflow versions, promotions, runs, audit, context, CRM, channels, agents, and skills
- connector-aware retail demo flows spanning Shopify, Salesforce, WhatsApp, Telegram, and runtime-provider selection

## Most Code-Sensitive Docs

When implementation changes, check these first:
- `architecture/02-reference-architecture.md`
- `architecture/03-workflow-operating-model.md`
- `architecture/04-canonical-resource-model.md`
- `architecture/05-retail-capability-map.md`
