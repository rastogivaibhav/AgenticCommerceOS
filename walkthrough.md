# Blue Team Remediation — Walkthrough

## Verification Result

```
101 passed, 0 failed in 1.24s
```

72 original tests + **29 new security tests** — all green.

---

## What Was Fixed

### Sprint 0 — P0 Blockers ✅

| Fix | File(s) | What Changed |
|-----|---------|-------------|
| FIX-01: Auth | [acosplatform/auth/api_key.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/auth/api_key.py) | API key (Shopper), JWT bearer (Ops) via `Depends()` |
| FIX-02: Validation | [acosplatform/models/requests.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/models/requests.py) | Pydantic [JourneyRequest](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/models/requests.py#11-41) — typed/bounded all fields |
| FIX-03: CORS | Both [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) files | `allow_origins=ALLOWED_ORIGINS` env var, no wildcard |
| FIX-04: Credentials | [.env.example](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.env.example), [.gitignore](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.gitignore), [docker-compose.yml](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/docker-compose.yml) | No hardcoded passwords; all via env vars |

### Sprint 1 — P1 Hardening ✅

| Fix | File(s) | What Changed |
|-----|---------|-------------|
| FIX-07: Prompt injection | [acosplatform/auth/sanitize.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/auth/sanitize.py) + ADK provider | Regex detection + message sanitization before LLM |
| FIX-08: Docker safety | [Dockerfile](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/Dockerfile), [.dockerignore](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.dockerignore) | Non-root `acos` user; dev/git/test files excluded |
| FIX-09: Tenant isolation | [acosplatform/journey/context.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/journey/context.py) | `authenticated_tenant_id` enforcement |
| FIX-11: Transactions | [acosplatform/db/connection.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/db/connection.py) | `autocommit=False` + [transaction()](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/db/connection.py#72-85) context manager |
| FIX-05: Rate limiting | [acosplatform/middleware/rate_limit.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/middleware/rate_limit.py), [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) | `slowapi` on `/journey` (60/min) and `/replay` (10/min) |

### Sprint 2 — Compliance ✅

| Fix | File(s) | What Changed |
|-----|---------|-------------|
| FIX-10: Audit logging | [acosplatform/audit/logger.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/audit/logger.py) | Structured JSON audit events with actor/resource/outcome |
| Error handling | Both [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) files | Generic 500 handler; no stack traces to callers |
| Swagger disabled | Both [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) files | `docs_url=None`, `redoc_url=None`, `openapi_url=None` |
| Deep health check | Both [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) files | Reports DB connectivity in health response |
| FIX-12: Static Assets | [apps/ops_api/main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) | Downloaded React/Babel locally and mounted via `StaticFiles` |
| FIX-13: Pinned Deps | [requirements.txt](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/requirements.txt) | Explicit versions for all dependencies |

### Sprint 3 — Polish ✅

| Fix | Files | What Changed |
|-----|-------|-------------|
| FIX-17: Security tests | [tests/test_security.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/tests/test_security.py) | 29 security tests: auth bypass, validation, injection, isolation |
| FIX-15: API versioning | [apps/shopper_api/main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/shopper_api/main.py), [apps/ops_api/main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) | Added `/v1/journey` and `/v1/replay/{id}` alias routes |
| FIX-16: Date deprecation| 8 files | Swapped `datetime.utcnow()` to timezone-aware `datetime.now(UTC)` |
| FIX-18: Metrics Endpoint | [acosplatform/observability/metrics.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/observability/metrics.py), [main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) | Exposes `/metrics` on both APIs for Prometheus scraping |

---

## JLP Ops Dashboard Demo

> [!NOTE]
> The Ops Dashboard has been customized explicitly for John Lewis Partnership to highlight the exact business value and "superpowers" of ACOS. It includes ROI metrics like estimated support savings and visualizes autonomous orchestration. Check out the recording below!

![ACOS x JLP Dashboard Interaction Recording](file:///C:/Users/vrast/.gemini/antigravity/brain/4ae7081b-6496-4f88-ba77-a9ec853006e9/jlp_dashboard_demo_1774009223899.webp)

---

## Security Control Coverage

| Attack Scenario | Before | After |
|-----------------|--------|-------|
| Unauthenticated journey calls | ✅ Anyone can call | 🔒 API key required |
| Ops dashboard access | ✅ Public | 🔒 JWT bearer required |
| Customer impersonation | ✅ Any customer_id | 🔒 Validated format; JWT binding possible |
| Prompt injection | ✅ Pass-through to LLM | 🔒 Sanitized before prompt construction |
| Hardcoded DB password | ✅ `acos:acos` | 🔒 `${DB_PASSWORD}` env var; port unexposed |
| Wildcard CORS | ✅ `allow_origins=["*"]` | 🔒 Whitelist from `ALLOWED_ORIGINS` |
| Invalid tenant access | ✅ Any string accepted | 🔒 Enum validation; 422 on invalid |
| Secrets in Docker image | ✅ Everything copied | 🔒 [.dockerignore](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.dockerignore) excludes `.env`, `.git`, tests |
| Container root exploit | ✅ Ran as root | 🔒 Non-root `acos` user |
| Schema API exposure | ✅ Swagger at `/docs` | 🔒 Disabled in production mode |

---

## Files Created / Modified

**New files:**
- [acosplatform/auth/api_key.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/auth/api_key.py) — API key + JWT auth
- [acosplatform/auth/sanitize.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/auth/sanitize.py) — Prompt injection sanitizer
- [acosplatform/models/requests.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/models/requests.py) — Pydantic request model
- [acosplatform/audit/logger.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/audit/logger.py) — Structured audit logger
- [tests/test_security.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/tests/test_security.py) — 29 security tests
- [.env.example](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.env.example), [.gitignore](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.gitignore), [.dockerignore](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/.dockerignore)

**Modified files:**
- [apps/shopper_api/main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/shopper_api/main.py) — Auth, CORS, validation, error handling
- [apps/ops_api/main.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_api/main.py) — JWT auth on all sensitive routes, React UI login form
- [acosplatform/db/connection.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/db/connection.py) — `autocommit=False` + [transaction()](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/db/connection.py#72-85) CM
- [acosplatform/journey/context.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/acosplatform/journey/context.py) — Tenant isolation enforcement
- [integrations/adk/provider.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/integrations/adk/provider.py) — Sanitize messages before LLM
- [Dockerfile](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/Dockerfile) — Non-root user
- [docker-compose.yml](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/docker-compose.yml) — Env var references, DB port unexposed
- [tests/test_api.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/tests/test_api.py) — Auth headers on all API tests
