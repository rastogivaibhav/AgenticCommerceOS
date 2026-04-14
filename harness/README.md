# ACOS Test Harness

This directory centralizes all automated tests for ACOS.

## Layout

- `harness/python/tests/` - Python unit/integration/system suites (pytest)
- `harness/playwright/specs/ui/` - UI smoke and navigation tests (Vite dev server)
- `harness/playwright/specs/integration/` - API + DB integration journeys
- `harness/playwright/specs/module-proof/` - Real-world module proof suite

## Run Python Harness

```bash
python -m pytest harness/python/tests -v
```

## Run Playwright Harness

```bash
cd apps/ops_ui_v2
npm run test:e2e:ui
npm run test:e2e:integration
npm run test:e2e:modules
```

## Notes

- Integration and module-proof Playwright suites expect the platform stack to be running (`docker compose up -d`).
- Module-proof tests validate shopper-api, ops-api, chat-api, and control-plane UI behavior as a cohesive operational check.
