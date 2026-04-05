# Weeks 6-12 Architecture Execution Plan (Solo + Codex)

## Virtual Architecture Team (Operating Roles)
1. Principal Tech Lead (you + Codex): delivery slicing, quality gate ownership, release control.
2. Retail Enterprise Architect: tenant isolation model, environment promotion policy, integration topology.
3. AI Architect: agent runtime contracts, governance SDK policy decisions, context lifecycle.
4. Solution Architect: API contracts, data model evolution, integration sequencing and failure strategy.
5. Product Manager Lens: pilot acceptance scripts, KPI instrumentation, defect burn-down gate.
6. Retail Operator Lens: usability, recovery paths, and runbook quality for real store teams.

## Scope and Sequence
1. Week 6: Workflow governance lifecycle
   - Deliverables:
     - Draft -> approve -> promote -> rollback lifecycle exposed via API.
     - Immutable audit trail for each lifecycle transition.
     - Contract tests for lifecycle routes and expected state transitions.
   - Exit criteria:
     - Workflow contract tests green.
     - Rollback + approval flows validated in test suite.

2. Week 7: Multi-tenant network baseline
   - Deliverables:
     - Namespace-per-tenant manifest template.
     - Default-deny NetworkPolicy baseline.
     - Explicit allow policies (DNS + control-plane service egress).
     - Strict service-to-service mTLS policy manifest (Istio).
   - Exit criteria:
     - Tenant namespace can be bootstrapped from template.
     - Default-deny confirmed by policy tests/checklist.

3. Week 8: Integration layer for pilot retailers
   - Deliverables:
     - Connector contract spec for catalog/pricing/promo/order.
     - Retry, timeout, and dead-letter behavior for connector failures.
     - Tenant-scoped connector config routing.
   - Exit criteria:
     - Connector contract tests green for success/failure/retry paths.

4. Week 9: Observability + SRE controls
   - Deliverables:
     - OTel trace envelope with `tenant_id`, `workflow_id`, `run_id`.
     - Error budget/SLO dashboard definitions.
     - On-call runbooks for top 5 failure modes.
   - Exit criteria:
     - Traces visible end-to-end for at least one journey per workflow family.

5. Week 10: Performance + tenancy protections
   - Deliverables:
     - Tenant quotas and rate-limits enforced.
     - Load-test baseline and noisy-neighbor checks.
     - Backpressure behavior and graceful degradation strategy.
   - Exit criteria:
     - Documented performance baseline and limit policy.

6. Week 11: Pilot UAT execution
   - Deliverables:
     - Pilot script pack for 2-3 tenants.
     - Defect triage rubric and burn-down board.
     - Business KPI instrumentation validation.
   - Exit criteria:
     - UAT scripts pass with accepted defect threshold.

7. Week 12: Production readiness gate
   - Deliverables:
     - Go-live checklist + evidence pack.
     - DR drill + rollback drill proof.
     - Security sign-off and cutover plan.
   - Exit criteria:
     - Formal go/no-go with rollback plan approval.

## Solo Execution Pattern (How We Actually Ship)
1. Keep each week split into 2-3 PR-sized slices.
2. Every slice must include:
   - implementation
   - tests
   - operational docs/runbook delta
3. Use hard acceptance criteria before starting next slice.
4. Keep feature surface frozen while governance/security/env validation remain open.

## Immediate Next 5 Tasks
1. Run Week-5 Postgres-backed RLS tests against a live local DB and capture evidence.
2. Finalize Week-6 lifecycle by validating approve/promote/rollback/archive contract coverage.
3. Add namespace + network policy lint/check script for Week-7 artifacts.
4. Define connector interface schema for Week-8 (catalog/pricing/promo/order) and add tests.
5. Add trace context middleware (`tenant_id`, `run_id`) for Week-9 bootstrap.
