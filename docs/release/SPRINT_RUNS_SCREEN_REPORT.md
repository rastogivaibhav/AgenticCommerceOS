# Sprint Report — Runs Screen Gap Closure

## Scope

The UX review identified a missing operator screen for runs. This sprint adds a dedicated Runs Command Centre so reviewers can inspect actual captured north-star orchestration runs rather than relying only on Studio Proof and replay cards.

## Added Backend APIs

- `GET /api/northstar/runs`
- `GET /api/northstar/runs/{run_id}`

The runs API is derived from captured replay snapshots and exposes:

- run ID
- tenant ID
- status
- created timestamp
- session ID
- journey ID
- correlation ID
- channel
- customer ID
- intent and confidence
- primary agent
- participating agent count
- tool call count
- evidence event count
- handoff count
- failed tool count
- response preview

The run detail endpoint returns the summary, the persisted replay snapshot, and the full orchestration result including tool trace and evidence timeline.

## Added UI

New screen:

- `/ui/runs`

New file:

- `apps/ops_ui_v2/src/pages/Runs.jsx`

Updated:

- `apps/ops_ui_v2/src/App.jsx`
- `apps/ops_ui_v2/src/components/Sidebar.jsx`
- `apps/ops_ui_v2/src/api/northstarAPI.js`
- `apps/ops_ui_v2/src/pages/StudioProof.css`

## Runs Screen Capabilities

The Runs screen provides:

- run list
- search/filter by intent, agent, customer or run ID
- status filter
- golden journey creation button
- run detail panel
- session, journey and correlation IDs
- response text
- participating agents
- tool calls
- evidence timeline
- human handoff section
- replay selected run

## Demo Flow Update

Recommended demo flow is now:

1. `/ui/demo-guide`
2. `/ui/runs`
3. `/ui/studio-proof`
4. `/ui/test-center`

The Runs screen should be used immediately after running the golden journey to prove the system captures and exposes operational run history.

## Tests Added

New test file:

- `harness/python/tests/northstar/test_runs_screen_api.py`

Coverage:

- create a north-star message run
- list captured runs
- inspect run detail
- verify agent/tool/evidence counts
- verify viewer role can read runs

## Validation Evidence

```text
pytest -q harness/python/tests/northstar
22 passed
```

```text
pytest -q harness/python/tests/integration/test_uat_week11_journeys.py harness/python/tests/test_week12_production_gate_checker.py
27 passed
```

```text
python scripts/northstar_smoke.py
success
Intent: styling_advice
Tool calls: 7
Evidence events: 15
```

```text
python scripts/production_runtime_check.py
status: pass
docker_available: false
```

```text
cd apps/ops_ui_v2 && npm ci && npm run build
Vite build successful
```

## Known Notes

- Docker remains unavailable in this sandbox, so runtime Compose certification still needs a Docker-enabled runner.
- `npm ci` reports dependency vulnerabilities inherited from the existing frontend dependency tree. The production build succeeds, but an npm audit/fix sprint is still recommended.
