# ACOS Documentation Library

This folder is the architecture, product, and operational source of truth for ACOS.

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
- Use PRDs and architecture docs before changing implementation.
- Keep each delivery slice testable, runnable, and documented.
- Treat readiness docs and evidence packs as release records.
- Keep runbooks current whenever operational behavior changes.

## Current Baseline
ACOS currently includes:
- `shopper-api` for customer runtime flows.
- `ops-api` for governed control-plane operations.
- `chat-api` for channel integrations.
- Postgres persistence for workflows, runs, and audit artifacts.
- Week 6-12 readiness evidence with closed Week 12 gate.
