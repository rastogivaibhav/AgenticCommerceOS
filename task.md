# ACOS — Task Checklist

## Phases 1–9: Core Build ✅ Complete

## Phase 10: Blue Team Security Hardening

### Sprint 0 — P0 Blockers
- [x] FIX-01: Auth (API key for Shopper, JWT for Ops)
- [x] FIX-02: Pydantic request validation models
- [x] FIX-03: CORS hardening (whitelist origins)
- [x] FIX-04: Credential management (.env, .gitignore)

### Sprint 1 — P1 Hardening
- [x] FIX-05: Rate limiting (slowapi)
- [x] FIX-06: Persist loyalty + billing state to DB
- [x] FIX-07: Prompt injection sanitization
- [x] FIX-08: Docker non-root user + .dockerignore
- [x] FIX-09: Tenant isolation enforcement

### Sprint 2 — Compliance
- [x] FIX-10: Structured audit logging
- [x] FIX-11: DB transactions (remove autocommit)
- [x] FIX-12: Error handlers and disabling Swagger
- [x] FIX-13: Pin requirements versions
- [x] FIX-14: Deep health checks

### Sprint 3 — Polish
- [x] FIX-15: API versioning /v1/
- [x] FIX-16: Replace datetime.utcnow()
- [x] FIX-17: Security test suite
- [x] FIX-18: Prometheus metrics endpoint

## Phase 11: Advanced Ops Dashboard (V2)

### Sprint 4 — V2 Foundation & Listings
- [ ] FE-01: Initialize Vite React App in `apps/ops_ui_v2` alongside REST API
- [ ] FE-02: Implement "List of Agents" View
- [ ] FE-03: Implement "List of Skills" View

### Sprint 5 — Advanced Code Editors
- [ ] FE-04: Agent Editor Widget (Assoc. Skills, Agent History, Report Card)
- [ ] FE-05: Skill Editor Widget (Code edit, Lint view, Stop in-flight)

### Sprint 6 — Workflow & Live Simulation
- [ ] FE-06: User Journey Planner (Interactive graph node editor using React Flow)
- [ ] FE-07: Live Simulation / Train Track View (Real-time orchestration visualization)
