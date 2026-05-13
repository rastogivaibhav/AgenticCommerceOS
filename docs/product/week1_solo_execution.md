# Week 1 Solo Execution Plan (Codex-Driven)

## Goal
Ship the first production-hardening slice while preserving local development speed.

## Scope (Week 1)
1. Fail-closed auth defaults.
2. Safe DB health probing (no pool leaks).
3. Consistent auth on control-plane endpoints.
4. UI auth header alignment for protected endpoints.
5. Config and deployment docs aligned to the new auth model.
6. Endpoint-level RBAC claims and policy checks.
7. Startup config validation for non-dev environments.

## Completed in this slice
1. Added explicit dev-only auth bypass flag: `ALLOW_INSECURE_DEV_AUTH`.
2. Updated auth module to fail closed when `SHOPPER_API_KEYS`/`OPS_JWT_SECRET` are missing.
3. Added `check_connection()` helper and switched health endpoints to use it.
4. Added auth dependencies on key ops list/detail endpoints.
5. Updated UI data calls (agents/skills/tenants/workflow API) to send bearer headers.
6. Updated `.env.example`, `docker-compose.yml`, and deployment docs for new env contract.
7. Added focused auth-configuration test file.
8. Centralized frontend API/auth calls into `src/api/client.js`.
9. Added role-based access checks (`admin`, `ops`, `analyst`) to ops routes.
10. Added startup validation that hard-fails non-dev boot when auth secrets are missing.
11. Added startup validation tests for non-dev gating behavior.
12. Added `scripts/mint_dev_jwt.py` to mint role-specific local JWTs quickly.
13. Removed duplicate workflow route definitions; workflow update source is now `apps/ops_api/main.py`.
14. Added `scripts/switch_ops_role.ps1` for one-command local role switching via `/dev/auth/bootstrap`.
15. Added local token-helper usage snippets in `README.md` and `DEPLOYMENT.md`.
16. Added deterministic ops RBAC contract tests for 401/403 and role policy checks (`tests/test_ops_rbac_contract.py`).

## Codex Task Format (use this for every next task)
```
Task: <short title>
Outcome: <user-visible result>
Files: <absolute or repo-relative paths>
Checks:
  - <command 1>
  - <command 2>
Done when:
  - <acceptance criterion 1>
  - <acceptance criterion 2>
```

## Next 2 Tasks (Week 1 continuation)
1. Add centralized frontend error toast handling for 401/403/500 responses.
2. Add role-to-screen mapping in UI so analyst role cannot trigger mutating actions.

## Risk Notes
1. Repo contains pre-existing in-flight changes; keep PRs small and file-scoped.
2. Python test environment currently lacks required runtime dependencies in this workspace.
3. Frontend build is green; full backend test verification still requires dependency setup.
