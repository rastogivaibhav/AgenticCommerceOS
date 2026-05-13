# Security Policy

## Reporting Vulnerabilities
Do not open public issues for security vulnerabilities.

Report privately to: **security@acos.dev**

Include:
- issue summary,
- impact,
- reproduction steps,
- affected endpoints/components,
- suggested fix (optional).

## Response Targets
- Acknowledgment: within 24 hours.
- Initial triage: within 48 hours.
- Fix timeline based on severity.

| Severity | Target |
|---|---|
| Critical | 24-48 hours |
| High | 7 days |
| Medium | 14 days |
| Low | Next planned release |

## Security Controls in ACOS
- RBAC-enforced operational endpoints (`require_ops_roles`).
- Audit logging for control-plane mutations.
- Tenant traffic controls (rate, quota, in-flight).
- CORS controls via `ALLOWED_ORIGINS`.
- Environment-based secret configuration.
- Production runbooks for go-live, incident response, and rollback.

## Operational Security Practices
1. Keep `ALLOW_INSECURE_DEV_AUTH=0` in non-dev environments.
2. Rotate `OPS_JWT_SECRET` and API keys regularly.
3. Restrict `ALLOWED_ORIGINS` to trusted domains.
4. Track release decisions through evidence artifacts in `deploy/k8s/observability/evidence/`.
5. Keep runbooks current when operational behavior changes.

## Security Validation References
- [docs/observability/slo_runbook.md](./docs/observability/slo_runbook.md)
- [docs/RUNBOOK_INCIDENT_RESPONSE.md](./docs/RUNBOOK_INCIDENT_RESPONSE.md)
- [docs/RUNBOOK_WORKFLOW_PROMOTION.md](./docs/RUNBOOK_WORKFLOW_PROMOTION.md)
- [docs/week12_production_gate_evidence_pack.md](./docs/week12_production_gate_evidence_pack.md)

## Supported Versions
Security fixes are prioritized for active release lines used in production pilots.

## Last Updated
2026-04-09
