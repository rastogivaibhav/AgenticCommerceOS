# Contributing to ACOS Control Plane

Thanks for contributing. ACOS is an operations-heavy project, so high-signal changes with clear tests and docs are the goal.

## Before You Start
- Read [README.md](./README.md).
- Read [docs/product/04-go-live-prd.md](./docs/product/04-go-live-prd.md).
- For operational changes, update the relevant runbook in `docs/`.

## Development Setup
```bash
git clone https://github.com/rastogivaibhav/AgenticCommerceOS.git
cd AgenticCommerceOS
cp .env.example .env

docker compose up --build -d
```

Optional local Python setup:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Branch and Commit Conventions
- Branch prefixes: `feature/`, `fix/`, `docs/`, `test/`, `refactor/`.
- Commit style: Conventional Commits.

Examples:
- `feat(ops-api): add workflow promotion guard`
- `fix(tenancy): enforce in-flight cap across tenants`
- `docs(runbook): add rollback drill evidence template`

## Required Checks
Run the smallest relevant checks for your change and include results in your PR.

Common checks:
```bash
python -m pytest tests/test_week12_production_gate_checker.py -q
python scripts/week12_production_gate_checker.py
```

Integration checks when touching ops journeys:
```bash
python -m pytest tests/integration/test_uat_week11_journeys.py -q
```

UI checks when touching `apps/ops_ui_v2`:
```bash
cd apps/ops_ui_v2
npm ci
npm run test
```

## Pull Request Checklist
- Clear problem statement.
- Focused diff with rationale.
- Tests added/updated where needed.
- Docs/runbooks updated if behavior changed.
- Evidence artifacts referenced when closing gates.

## Security and Responsible Disclosure
Do not open public issues for vulnerabilities.
Use [SECURITY.md](./SECURITY.md) and report privately.

## Community
- Be respectful and constructive.
- Follow [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

Thanks for helping make ACOS production-ready.
