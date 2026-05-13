# Weeks 6-12 Architecture Execution Plan (Solo + Codex)

## Status Refresh (as of 2026-04-09)
1. Week 6: Closed (workflow governance lifecycle complete with test coverage).
2. Week 7: Closed (tenant network isolation evidence pass on policy-enforcing CNI path).
3. Week 8: Closed (connector contract runtime and failure-handling paths validated).
4. Week 9: Closed (observability dashboards + SLO alert wiring + evidence artifact complete).
5. Week 10: Closed (tenant traffic controls and performance/noisy-neighbor evidence complete).
6. Week 11: Closed (pilot UAT evidence passed; defect threshold gate documented and closed).
7. Week 12: Closed (final checker pass, evidence pack complete, and formal go/no-go sign-off recorded).

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

2. Week 7 (Closed): Multi-tenant network baseline
   - Deliverables:
     - Namespace-per-tenant manifest template.
     - Default-deny NetworkPolicy baseline.
     - Explicit allow policies (DNS + control-plane service egress).
     - Strict service-to-service mTLS policy manifest (Istio).
   - Exit criteria:
     - Tenant namespace can be bootstrapped from template.
     - Default-deny confirmed by policy tests/checklist.

3. Week 8 (Closed): Integration layer for pilot retailers
   - Deliverables:
     - Connector contract spec for catalog/pricing/promo/order.
     - Retry, timeout, and dead-letter behavior for connector failures.
     - Tenant-scoped connector config routing.
   - Exit criteria:
     - Connector contract tests green for success/failure/retry paths.

4. Week 9 (Closed): Observability + SRE controls
   - Deliverables:
     - OTel trace envelope with `tenant_id`, `workflow_id`, `run_id`.
     - Error budget/SLO dashboard definitions.
     - On-call runbooks for top 5 failure modes.
   - Exit criteria:
     - Traces visible end-to-end for at least one journey per workflow family.

5. Week 10 (Closed): Performance + tenancy protections
   - Deliverables:
     - Tenant quotas and rate-limits enforced.
     - Load-test baseline and noisy-neighbor checks.
     - Backpressure behavior and graceful degradation strategy.
   - Exit criteria:
     - Documented performance baseline and limit policy.

6. Week 11 (Closed): Pilot UAT execution
   - Deliverables:
     - Pilot script pack for 2-3 tenants.
     - Defect triage rubric and burn-down board.
     - Business KPI instrumentation validation.
   - Exit criteria:
     - UAT scripts pass with accepted defect threshold.

7. Week 12 (Closed): Production readiness gate
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

## Active Next 5 Tasks (Post-Week-12 Follow-Through)
1. Archive superseded Week-12 interim artifacts in the evidence index (keep files, mark latest canonical).
2. Execute first pilot cutover window and capture operational outcomes.
3. Track first-week production KPIs against go-live baseline.
4. Record any post-cutover defects and complete follow-up triage.
5. Prepare next roadmap slice after Week-12 gate closure.

## PR-Sized Execution Slices (Weeks 10-12)

### Week 10 (Performance + Tenancy Protections)
1. W10-PR1: Close noisy-neighbor integration evidence
   - File targets: `apps/ops_ui_v2/tests-e2e-integration/tenant-quota.spec.js`, `tests/test_tenant_traffic_controls.py`, `deploy/k8s/observability/evidence/week10-quota-*.json`.
   - Commands: `pytest tests/test_tenant_traffic_controls.py -q`; `cd apps/ops_ui_v2; npx playwright test --config playwright.config.integration.js tests-e2e-integration/tenant-quota.spec.js`.
   - Exit gate: fresh Week-10 evidence artifact written with `overall_pass=true` and both tenants (`default`, `eu-store`) validated.

2. W10-PR2: Publish load/performance baseline artifact pack
   - File targets: `scripts/load_test_chat_api.py`, `deploy/k8s/performance/evidence/` (new artifact folder), `docs/observability/week10_performance_baseline.md` (new summary).
   - Commands: `locust -f scripts/load_test_chat_api.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m --headless`; `python scripts/load_test_chat_api.py --help` (syntax sanity check if script is extended with argparse).
   - Exit gate: baseline report captured with p50/p95/p99 latency, throughput, and error rate for single-tenant and mixed-tenant runs.

3. W10-PR3: Backpressure + graceful degradation runbook closure
   - File targets: `docs/observability/slo_runbook.md`, `docs/product/weekly_readiness_journey.md`.
   - Commands: `pytest tests/test_observability_trace_slo.py -q`; `pytest tests/test_api.py -q`.
   - Exit gate: runbook has explicit trigger thresholds + mitigation sequence, and Week-10 status can be moved from `Started` to `Done`.

### Week 11 (Pilot UAT Execution)
4. W11-PR1: Stabilize operator-journey integration tests
   - File targets: `tests/integration/test_uat_week11_journeys.py`, `tests/fixtures/uat_pilot_data.py`, `tests/integration/conftest.py`.
   - Commands: `pytest tests/integration/test_uat_week11_journeys.py -v`; `pytest tests/integration/test_uat_week11_journeys.py -k Journey1 -v` (focused iteration).
   - Exit gate: journey suites execute against current API behavior without blanket failures.

5. W11-PR2: Harden UAT evidence collector and pass/fail rubric
   - File targets: `scripts/week11_uat_evidence_collector.py`, `deploy/k8s/observability/evidence/week11-uat-*.json`, `docs/week11_uat_evidence_pack.md` (new).
   - Commands: `python scripts/week11_uat_evidence_collector.py`.
   - Exit gate: collector exits `0`, artifact records `overall_pass=true`, and evidence pack links test counts by journey.

6. W11-PR3: Pilot KPI and defect burn-down gate
   - File targets: `docs/week11_uat_evidence_pack.md`, `docs/product/weekly_readiness_journey.md`.
   - Commands: `pytest tests/integration/test_uat_week11_journeys.py -v --maxfail=1`.
   - Exit gate: accepted defect threshold documented and Weeks 11 gate marked closed with artifact reference.

### Week 12 (Production Readiness Gate)
7. W12-PR1: Fix production gate checker false negatives
   - File targets: `scripts/week12_production_gate_checker.py`, `tests/test_week12_production_gate_checker.py` (new), `deploy/k8s/observability/evidence/week12-production-gate-*.json`.
   - Commands: `pytest tests/test_week12_production_gate_checker.py -q`; `python scripts/week12_production_gate_checker.py`.
   - Exit gate: checker validates real repo paths/modules and produces accurate readiness percentage.

8. W12-PR2: DR drill + rollback drill evidence templates and proofs
   - File targets: `docs/week12_production_gate_evidence_pack.md` (new/update), `docs/RUNBOOK_GO_LIVE.md` (new), `docs/RUNBOOK_WORKFLOW_PROMOTION.md` (new), `docs/RUNBOOK_INCIDENT_RESPONSE.md` (new).
   - Commands: `python scripts/week12_production_gate_checker.py`; `Get-ChildItem deploy/k8s/observability/evidence/week11-uat-*.json,deploy/k8s/observability/evidence/week12-production-gate-*.json`.
   - Exit gate: drill evidence and rollback proof are attached in the production evidence pack with owners and timestamps.

9. W12-PR3: Final go/no-go record and cutover sign-off
   - File targets: `docs/product/weekly_readiness_journey.md`, `docs/product/week6_12_architecture_execution_plan.md`, `docs/week12_production_gate_evidence_pack.md`.
   - Commands: `python scripts/week12_production_gate_checker.py`; `pytest -q`.
   - Exit gate: formal go/no-go decision logged with rollback approval and named sign-offs.

## Current Blockers To Burn Down First
1. None for Weeks 6-12 gate closure. Latest canonical Week-12 artifact: `deploy/k8s/observability/evidence/week12-production-gate-2026-04-09T10-32-24-158102Z.json` (`7/7`, `overall_pass=true`).

## Week-12 Closure Record
1. Formal go/no-go decision logged: `GO` at `2026-04-09T10:55:00Z`.
2. Named sign-offs recorded in `docs/week12_production_gate_evidence_pack.md`.
3. Rollback approval recorded with explicit rollback authority.
