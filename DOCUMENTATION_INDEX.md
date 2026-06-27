# Documentation Index

This index maps the current ACOS documentation set for contributors, operators, and release owners.

## Core Docs

| Document | Purpose |
|---|---|
| [README.md](README.md) | Project overview, architecture, quick start |
| [docs/dev/repo-map.md](docs/dev/repo-map.md) | Current repository map and legacy/generated-file guidance |
| [INSTALLATION.md](INSTALLATION.md) | Local and environment setup |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment and operations guidance |
| [API.md](API.md) | API contracts and examples |
| [TESTING.md](TESTING.md) | Test strategy and command references |
| [CHANGELOG.md](CHANGELOG.md) | Release history and docs updates |

## Governance And Product Docs

| Document | Purpose |
|---|---|
| [docs/product/04-go-live-prd.md](docs/product/04-go-live-prd.md) | Go-live requirements and acceptance criteria |
| [docs/product/weekly_readiness_journey.md](docs/product/weekly_readiness_journey.md) | Week-by-week readiness status and gate evidence |
| [docs/product/week6_12_architecture_execution_plan.md](docs/product/week6_12_architecture_execution_plan.md) | Delivery slices, exit gates, closure records |
| [docs/architecture/01-vision-and-principles.md](docs/architecture/01-vision-and-principles.md) | Platform vision and architecture principles |
| [docs/architecture/02-reference-architecture.md](docs/architecture/02-reference-architecture.md) | Reference architecture |

## Operational Runbooks

| Document | Purpose |
|---|---|
| [docs/observability/slo_runbook.md](docs/observability/slo_runbook.md) | SLO triage and safe-mode procedures |
| [docs/RUNBOOK_GO_LIVE.md](docs/RUNBOOK_GO_LIVE.md) | Cutover execution and stop/go conditions |
| [docs/RUNBOOK_WORKFLOW_PROMOTION.md](docs/RUNBOOK_WORKFLOW_PROMOTION.md) | Promotion and rollback process |
| [docs/RUNBOOK_INCIDENT_RESPONSE.md](docs/RUNBOOK_INCIDENT_RESPONSE.md) | Severity model and incident workflow |

## Community And Security

| Document | Purpose |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute code and docs |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community standards |
| [SECURITY.md](SECURITY.md) | Vulnerability disclosure and security controls |
| [LICENSE](LICENSE) | Apache 2.0 terms |

## Fast Paths

- New contributor: `README.md` -> `docs/dev/repo-map.md` -> `INSTALLATION.md` -> `CONTRIBUTING.md`
- Operator on-call: `docs/RUNBOOK_INCIDENT_RESPONSE.md` -> `docs/observability/slo_runbook.md`
- Release owner: `docs/product/weekly_readiness_journey.md` -> `docs/product/week6_12_architecture_execution_plan.md`

## Last Updated

- Date: `2026-06-27`
- Context: repository hygiene cleanup and current-reality documentation refresh.
