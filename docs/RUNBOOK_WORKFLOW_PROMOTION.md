# ACOS Workflow Promotion Runbook

## Purpose
This runbook defines the controlled promotion and rollback flow for workflow versions across environments.

## Scope
1. Promotion path: `dev -> test -> stage -> prod`.
2. Applies to workflow families in pilot scope.
3. Enforces approval and audit requirements before production changes.

## Required Inputs
1. `workflow_id`
2. `version`
3. `source_environment`
4. `target_environment`
5. `approval_note`
6. authorized operator token with required role

## Pre-Promotion Checklist
1. Change summary documented.
2. Validation state is approved.
3. Rollback target version identified.
4. Risk/compliance approval captured for production promotion.
5. Monitoring owner assigned for post-promotion window.

## Promotion Procedure
1. Review workflow detail and active versions.
2. Approve target version when required.
3. Promote version to target environment.
4. Verify promotion appears in audit and promotion history.
5. Validate run health and SLO signals for at least 30 minutes.

## API Route References
1. Create version:
   `POST /api/v1/workflows/{workflow_id}/versions`
2. Approve version:
   `POST /api/v1/workflows/{workflow_id}/versions/{version}/approve`
3. Promote version:
   `POST /api/v1/workflows/{workflow_id}/versions/{version}/promote`
4. Rollback:
   `POST /api/v1/workflows/{workflow_id}/rollback`
5. Audit trail:
   `GET /api/audit`

## Rollback Procedure
Execute rollback immediately when stop conditions are reached:
1. Freeze additional promotions for impacted workflow family.
2. Identify last known stable version.
3. Call rollback endpoint with reason and target environment.
4. Validate:
   - errors trend down,
   - latency stabilizes,
   - no additional policy-risk alerts.
5. Record rollback outcome in incident and audit logs.

## Rollback Validation Checklist
1. Rollback API returned success.
2. Active version reflects rollback target.
3. New runs use rollback version.
4. SLO signals return to acceptable band.
5. Incident commander confirms service stability.

## Rollback Drill Template
| Field | Value |
|---|---|
| Drill ID | RB-YYYYMMDD-01 |
| Workflow ID |  |
| Trigger Condition |  |
| Initiated By |  |
| Start Timestamp (UTC) |  |
| Stable Version Target |  |
| End Timestamp (UTC) |  |
| Outcome |  |
| Follow-up Actions |  |
