# ACOS Go-Live Runbook

## Scope
This runbook covers pilot go-live execution for the bounded Week 12 scope:
1. Tenants: `tenant_uat_pilot_a`, `tenant_uat_pilot_b`.
2. Workflow families: `discovery`, `post_purchase`, `service_guidance`, `returns`.
3. Entry gate: Week 11 UAT evidence pass and Week 12 production gate checker pass.

## Roles And Ownership
| Role | Primary Owner | Responsibility |
|---|---|---|
| Incident Commander | Platform Owner | Coordinates go-live and stop/go decisions |
| Workflow Administrator | Workflow Admin Lead | Executes controlled promotions and rollback if needed |
| Operations Lead | Service Ops Lead | Verifies run health and support readiness |
| Risk And Compliance Owner | Risk Lead | Approves production-sensitive transitions |
| Communications Owner | Product Manager | Sends stakeholder updates and decision records |

## Preconditions (T-24h)
1. Week 11 UAT artifact available and passing.
2. Latest Week 12 checker artifact available and passing.
3. `RUNBOOK_WORKFLOW_PROMOTION` and `RUNBOOK_INCIDENT_RESPONSE` reviewed by operations owner.
4. On-call roster and escalation contacts confirmed.
5. Dashboards and alert routes confirmed.

## Go-Live Sequence
### T-60m to T-15m (Final Readiness)
1. Confirm deployment state.
   Command: `docker compose ps`
   Success: `ops-api` is running and healthy enough for pilot operations.
2. Confirm production gate snapshot.
   Command: `docker run --rm -v "${PWD}:/workspace" -w /workspace acos-chat-api python scripts/week12_production_gate_checker.py`
   Success: `checks_passed=7/7`.
3. Confirm open blocker list only contains formal sign-off.

### T-15m to T+30m (Controlled Activation)
1. Incident Commander opens go-live bridge and confirms roles.
2. Workflow Administrator executes approved promotions only.
3. Operations Lead validates baseline:
   - `GET /health`
   - `GET /metrics`
   - sample workflow and run investigation paths.
4. Communications Owner sends "activation complete" update.

### T+30m to T+120m (Stabilization Window)
1. Monitor SLO signals and tenant error rates.
2. If thresholds breach, execute incident runbook and rollback runbook immediately.
3. At T+120m, Incident Commander records go/no-go continuation decision.

## Abort And Rollback Triggers
Trigger rollback when any condition is true:
1. Sustained p95 latency above threshold and not recovering.
2. Tenant error rate exceeds threshold for 10 minutes.
3. Policy/risk control failure affecting production safety.
4. Severe operator-path regression in workflow promotion or run investigation.

Rollback path:
1. Declare rollback on bridge.
2. Execute `RUNBOOK_WORKFLOW_PROMOTION` rollback section.
3. Confirm recovery via SLO and health checks.
4. Capture incident and timeline evidence.

## Evidence Capture Checklist
| Item | Owner | Timestamp (UTC) | Evidence |
|---|---|---|---|
| Week 11 UAT pass artifact linked | Workflow Admin Lead | 2026-04-09T10:06:48Z | `deploy/k8s/observability/evidence/week11-uat-2026-04-09T10-06-48-082049Z.json` |
| Week 12 production checker pass linked | Platform Owner | 2026-04-09T10:22:45Z | `deploy/k8s/observability/evidence/week12-production-gate-2026-04-09T10-22-45-359759Z.json` |
| DR drill record attached | Service Ops Lead | 2026-04-09T10:34:00Z | `docs/week12_production_gate_evidence_pack.md` |
| Rollback drill record attached | Workflow Admin Lead | 2026-04-09T10:42:00Z | `docs/week12_production_gate_evidence_pack.md` |

## Sign-Off Record
Final go-live approval is recorded in the Week 12 evidence pack during W12-PR3.
