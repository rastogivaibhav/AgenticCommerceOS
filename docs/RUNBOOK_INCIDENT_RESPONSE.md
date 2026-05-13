# ACOS Incident Response Runbook

## Purpose
Provide a consistent response flow for operational incidents during pilot and go-live operations.

## Severity Model
| Severity | Definition | Initial Response Target |
|---|---|---|
| P0 | Critical outage or safety breach | Immediate |
| P1 | Major degradation with customer impact | 15 minutes |
| P2 | Partial degradation with workaround | 30 minutes |
| P3 | Minor issue, no immediate impact | Next business cycle |

## Detection Signals
1. SLO alerts from `docs/observability/slo_runbook.md`.
2. Error spikes from analytics and traces.
3. Repeated tenant throttling with cross-tenant impact.
4. Operator reports of failed workflows, promotions, or investigations.

## Incident Workflow
1. Detect and classify severity.
2. Open incident channel and assign commander.
3. Stabilize blast radius:
   - pause affected workflow,
   - activate failsafe path,
   - apply tenant safe-mode controls when needed.
4. Diagnose using traces, audit events, and recent promotions.
5. Mitigate (fix, rollback, or traffic reduction).
6. Validate recovery and monitor for 30 minutes.
7. Close incident and capture post-incident actions.

## Command And Endpoint Quick Reference
1. Health:
   `GET /health`
2. Metrics:
   `GET /metrics`
3. SLO snapshot:
   `GET /analytics/slo?tenant_id=<id>&window_minutes=60`
4. Traces:
   `GET /analytics/traces?tenant_id=<id>&limit=200`
5. Audit:
   `GET /api/audit`

## Containment Playbooks
### Workflow Incident
1. Pause or rollback affected workflow version.
2. Confirm active version and run behavior.

### Tenant Saturation Incident
1. Apply tenant safe mode and lower in-flight/throughput limits.
2. Shift impacted connectors to degraded/local mode if needed.

### Promotion Regression
1. Halt active promotion wave.
2. Execute rollback to prior stable version.
3. Revalidate critical journeys.

## Incident Record Template
| Field | Value |
|---|---|
| Incident ID |  |
| Severity |  |
| Commander |  |
| Start Timestamp (UTC) |  |
| Affected Tenant(s) |  |
| Trigger Signal |  |
| Containment Steps |  |
| Resolution Summary |  |
| End Timestamp (UTC) |  |
| Follow-up Actions |  |
