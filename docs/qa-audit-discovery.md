# ACOS QA/UX Audit - Phase 1 Discovery

**Date Started:** 2026-04-15
**App:** ACOS Control Plane
**Frontend:** React + Vite at http://localhost:5173/ui/
**Backend APIs:** 
- Ops API: http://localhost:8081 (port 8081)
- Shopper API: http://localhost:8080 (port 8080)
- Chat API: http://localhost:8001 (port 8001)

---

## Initial Findings

### Current Authentication State
- **Status:** Not authenticated (showing "Context: Not authenticated" in header)
- **Current User Role:** Read-only (403 errors on actions)

### Navigation Sidebar Routes
```
- Workflows (currently active)
- Channels
- Routes (maps to /ui/demo-routes)
- Agents
- Skills
- Analytics
- Tenants
```

### Workflows Screen (Initial State)
**Current State:** Empty/Not Loaded
- Search box: "Search workflows..."
- Create Workflow button: **DISABLED** (due to lack of authentication)
- Metrics cards showing:
  - Workflow inventory: 0
  - Active versions: 0
  - Draft only: 0
  - Demo entrypoints: 0
- Table headers: Workflow, Family, Status, Active Version, Last Promotion
- Table body: Shows "Request failed (404)"

### Issues Found So Far
1. **404 Errors:** API endpoints returning 404 for workflow routes
2. **403 Errors:** Permission denied on /api/v1/ops/context endpoint
3. **Unauthenticated State:** User shows "Not authenticated" - need to understand login flow
4. **Disabled UI:** Create Workflow button disabled without clear explanation

### Next Steps
- [ ] Find authentication/login screen
- [ ] Map auth flow (login → authenticated state)
- [ ] Test each screen with authenticated user
- [ ] Document all possible states per screen
- [ ] Check for hidden UI elements
- [ ] Test responsive design

