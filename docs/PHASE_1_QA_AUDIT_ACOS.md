# ACOS Phase 1: Complete QA/UX Audit Execution Plan

**Project:** ACOS Control Plane  
**Date:** 2026-04-15  
**Scope:** Comprehensive discovery, screen mapping, and test plan creation  
**Duration:** 2 weeks  
**Effort:** 1 QA Architect + 1 QA Engineer

---

## Executive Summary

ACOS is a multi-tenant workflow and channel management system with 7 primary screens. Current state:
- **Frontend:** React + Vite (ops_ui_v2) at `localhost:5173/ui/`
- **Backend APIs:** Ops API (8081), Shopper API (8080), Chat API (8001)
- **Database:** PostgreSQL (container: acos-db-1)
- **Status:** Running in Docker, unauthenticated state showing 403/404 errors

**Phase 1 Deliverables:**
1. Complete screen inventory with all states
2. Role-based access matrix
3. Component state documentation
4. Test case matrix (200+ test cases)
5. Defect log with baseline issues

---

## Phase 1: ACOS Discovery & Documentation (Weeks 1–2)

### Objective
Create a complete, auditable map of ACOS's UI, all user interactions, states, and role-based access patterns.

### Key Discoveries (Initial Audit)
```
Screens Mapped:
├── /ui/workflows         → Workflow Operations (Workspace Registry)
├── /ui/agents            → Agent Registry  
├── /ui/skills            → Tooling Inventory / Skill Library
├── /ui/channels          → Channel Onboarding (WhatsApp, Telegram)
├── /ui/demo-routes       → Workflow Validation
├── /ui/analytics         → Operational Analytics
├── /ui/tenants           → Tenant Administration
└── /ui/workflows/:id/editor → Workflow Editor (nested route)

Current Issues Discovered:
- 404 errors on API endpoints (/workflows route, likely auth-related)
- 403 Forbidden on /api/v1/ops/context (permission/auth check)
- User shows "Not authenticated" in header
- Create buttons disabled (auth-related)
```

---

## Task 1: Authentication & Role Mapping

### Objective
Understand the authentication model and map which user roles see which screens/actions.

### Method

#### 1.1 Authentication Flow Discovery
**Action:** Analyze how authentication works

**Inputs Needed:**
- Check `ALLOW_INSECURE_DEV_AUTH` in `.env` (currently 0 = secure)
- Review Ops API auth endpoints: `GET /docs` at `http://localhost:8081/docs`
- Find JWT token structure in LocalStorage/SessionStorage

**Steps:**
1. Open browser DevTools → Application → LocalStorage/SessionStorage
2. Check if any auth tokens exist
3. Review `/api/v1/ops/context` endpoint in Ops API docs
4. Identify JWT payload structure (user_id, role, permissions)
5. Test with insecure dev auth enabled (if available)

**Deliverable:** `docs/auth-flow-mapping.md`
```markdown
# ACOS Authentication Flow

## Current Model
- JWT-based authentication via Ops API
- Environment: dev (ALLOW_INSECURE_DEV_AUTH=0, secure mode)
- Context endpoint: GET /api/v1/ops/context (returns current user + role)

## Roles Identified
- [To be discovered]

## Permissions Model
- [To be discovered]

## Test Accounts Needed
- Admin user
- Operator user
- Read-only user
- Tenant user (if multi-tenant)
```

#### 1.2 Role Definitions & Access Control
**Action:** Map which role sees what

**Steps:**
1. Check Ops API models for role definitions
2. Check each screen component for permission checks (e.g., `useContext(AuthContext)`)
3. Document required role for each action:
   - Create Workflow
   - Create Agent
   - Create Skill
   - Link Channel (WhatsApp, Telegram)
   - Create Tenant
   - Approve workflow (if applicable)

**Deliverable:** `docs/roles-access-matrix.csv`
```
Screen,Endpoint,Feature,Required Role,HTTP Method,Status
Workflows,/api/v1/ops/workflows,List workflows,any,GET,403
Workflows,/api/v1/ops/workflows,Create workflow,admin,POST,403
Agents,/api/v1/ops/agents,List agents,any,GET,403
Agents,/api/v1/ops/agents,Create agent,admin,POST,403
Channels,/api/v1/ops/channels/whatsapp,Link WhatsApp,admin,POST,403
Tenants,/api/v1/ops/tenants,Create tenant,super-admin,POST,403
```

---

## Task 2: Screen State Matrix Documentation

### Objective
For each of the 7 screens, document **every possible state** a user could see.

### Method

#### 2.1 Workflows Screen States
**File:** `docs/screens/workflows-states.md`

**States to Document:**

| State | Trigger | Visual | Data | User Can | Issues |
|-------|---------|--------|------|----------|--------|
| **Empty** | No workflows exist in DB | Metrics: 0/0/0/0, empty table | `workflows: []` | Create (if auth allows) | Currently shows 404 error |
| **Loading** | Page loads, fetching data | Skeleton table, spinners | `isLoading: true` | None (disabled) | Check animation smoothness |
| **Loaded** | API returns workflows | Table with rows, metrics updated | `workflows: [...]` | Click to edit, delete, duplicate | Verify sorting/filtering works |
| **Search Active** | User types in search box | Table filters, search pill visible | `searchTerm: "xyz"` | Clear search, refine query | Test special characters |
| **Error** | API 500 or network error | Error banner, retry button | `error: "Failed to load"` | Retry, go back | Test various error scenarios |
| **Unauthorized** | User lacks permission | "Not authenticated" message, buttons disabled | N/A | View only (if read-only) | Check error message clarity |

**Detailed State Document:**
```markdown
# Workflows Screen State Matrix

## 1. Empty State
- **When:** No workflows exist in database
- **Visual:**
  - Metrics cards show 0 / 0 / 0 / 0
  - Table headers visible but no rows
  - "Create Workflow" button enabled (if authenticated)
  - Consider: empty state illustration + helpful message

- **Data Returned:**
  ```json
  {
    "workflows": [],
    "totalCount": 0,
    "activeVersions": 0,
    "draftOnly": 0,
    "demoEntrypoints": 0
  }
  ```

- **User Actions Available:**
  - Click "Create Workflow" (if auth allows)
  - Use search (returns no results)

- **Expected Behavior:**
  - Search box functional but disabled visually
  - Create button enabled with clear primary CTA
  - No data in table, no pagination

## 2. Loading State
- **When:** Page first loads, user refreshes, data refetching
- **Visual:**
  - Skeleton placeholders for table rows (8 rows)
  - Spinners on metrics cards
  - Search box disabled
  - Create button disabled
  - No flickering or layout shift

- **Duration:** Typically 500ms-2s
- **Accessible:** Should announce "Loading workflows" to screen readers

## 3. Loaded State (With Data)
- **When:** API returns workflows successfully
- **Visual:**
  - Table rows populated with workflow data
  - Columns: Workflow, Family, Status, Active Version, Last Promotion, Actions (...)
  - Metrics cards show actual counts
  - Search box enabled
  - Create button enabled

- **Sorting:** Click column header to sort ascending/descending
- **Pagination:** If 20+ workflows, pagination controls appear
- **Row Actions:** Click ... → Edit, Delete, Duplicate, Promote to Prod

## 4. Search/Filter State
- **When:** User enters text in search box
- **Visual:**
  - Table filters to matching workflows
  - Search pill visible showing query
  - Results count displayed
  - "Clear filters" button appears

- **Behavior:**
  - Debounced search (500ms)
  - Real-time filtering
  - Case-insensitive
  - Searches: workflow name, family, description

## 5. Error State
- **When:** API fails (500, timeout, network error)
- **Visual:**
  - Red error banner with icon
  - Error message: "Failed to load workflows. Please try again."
  - Retry button
  - Fallback data displayed if available

- **Variants:**
  - 404 Not Found: "No workflows available" (informational, not error)
  - 403 Forbidden: "You don't have access to workflows"
  - 500 Server Error: "Unexpected error. Please contact support."

## 6. Unauthorized State
- **When:** User not authenticated OR lacks permission
- **Visual:**
  - Header shows "Not authenticated"
  - Create button disabled with tooltip: "Requires authentication"
  - Table shows permission error
  - Optional: Link to login page

- **Behavior:**
  - All action buttons disabled
  - Read-only access (if allowed)
  - Clear messaging about required permissions
```

---

#### 2.2 Agents Screen States

**File:** `docs/screens/agents-states.md`

| State | Trigger | Metrics Shown | Table Display | Create Button | Issues |
|-------|---------|---------------|----------------|---------------|--------|
| **Empty** | No agents exist | 0 agents, 0 types | Empty table | Enabled | Currently shows 404 |
| **Loaded** | Agents fetched | Count + breakdown by type | Rows with Name, Type, Description, Actions | Enabled | Verify type filtering |
| **Loading** | Data fetching | Previous metrics or N/A | Skeleton rows | Disabled | Check animation |
| **Type Filter** | User clicks filter | Filtered count | Shows only selected type | Enabled | Test all types |
| **Error** | API fails | Last known or error icon | Error message | Disabled | Document error copy |

---

#### 2.3 Skills Screen States

| State | Trigger | Display | Create Button | Actions |
|-------|---------|---------|---|---|
| **Empty** | No skills defined | Empty state | Enabled | Create |
| **Loaded** | Skills fetched | List/Grid view | Enabled | Create, Edit, Delete, Test |
| **Filter By Category** | User filters | Filtered skills | Enabled | Same as loaded |
| **Error** | API fails | Error message | Disabled | Retry |

---

#### 2.4 Channels Screen States

**Special Considerations:** Channels has **external integrations** (WhatsApp, Telegram)

| State | Trigger | UI | Buttons | Notes |
|-------|---------|-----|---------|-------|
| **Not Linked** | Channel not configured | "Link WhatsApp" / "Link Telegram" buttons prominent | Link buttons enabled | Redirect to 3rd party? |
| **Linking In Progress** | User clicks Link button | Modal/dialog, waiting for OAuth callback | Buttons disabled, spinner | Check timeout behavior |
| **Linked** | Integration successful | Channel status = "Active", unlink button | Unlink button enabled | Show channel ID, sync status |
| **Link Error** | OAuth failed or API error | Error message with details | Retry button | Document error scenarios |
| **Unlinked** | User clicked Unlink | Back to "Not Linked" state | Link buttons re-enabled | Confirm dialog first? |

---

#### 2.5 Analytics Screen States

| State | Trigger | Display | Export | Refresh |
|-------|---------|---------|--------|---------|
| **Fallback Mode** | No data or API unavailable | "Analytics is in fallback mode" message | Export grayed | Refresh enabled |
| **Data Available** | Metrics loaded | Charts, metrics, trends | Export enabled (CSV/JSON) | Refresh enabled |
| **Loading** | Page loads or user refreshes | Skeleton charts, spinners | Grayed | Spinning |
| **Export In Progress** | User clicks Export | Modal with format options | Disabled during export | Disabled |
| **Export Complete** | Download finishes | Toast confirmation, file downloaded | Re-enabled | Enabled |

---

#### 2.6 Tenants Screen States

| State | Trigger | Display | Create Button | Actions |
|-------|---------|---------|---|---|
| **Empty** | No tenants | Empty state message | Enabled | Create |
| **Loaded** | Tenants fetched | List with Name, Status, Users, Created | Enabled | Edit, Delete, Manage Users, View Usage |
| **Loading** | Data fetching | Skeleton rows | Disabled | N/A |
| **Tenant Selected** | Click tenant row | Tenant detail panel (side or modal) | Depends on permission | Edit, Delete, Users |
| **Error** | API fails | Error message | Disabled | Retry |

---

#### 2.7 Demo Routes Screen

| State | Trigger | Display | Validate Button | Results |
|-------|---------|---------|---|---|
| **Default** | Page loads | Route list, supported paths | Enabled | None shown yet |
| **Validating** | User clicks Validate | Spinner, progress indicator | Disabled | None yet |
| **Validation Complete** | API responds | Results table (passed/failed), statistics | Enabled | Pass/fail per route, duration |
| **Validation Error** | API fails | Error message with retry | Re-enabled | None |

---

#### 2.8 Workflow Editor (Nested Route: /ui/workflows/:id/editor)

| State | Trigger | Canvas | Sidebar | Save Button |
|-------|---------|--------|---------|---|
| **Empty Editor** | User creates new workflow | Blank canvas, node palette on left | Node properties panel | Disabled (no nodes) |
| **Edit Mode** | User loads existing workflow | Workflow nodes rendered | Selected node properties | Enabled (changes made) |
| **Node Selected** | User clicks node | Highlight selected | Properties shown in sidebar | Enabled |
| **Unsaved Changes** | User edits node properties | Canvas/properties updated | "Unsaved changes" indicator | Enabled (yellow/blue) |
| **Saving** | User clicks Save | Canvas disabled | Spinner on Save button | Disabled |
| **Save Success** | API responds 200 | Node count updated, unsaved indicator cleared | Confirmation toast | Re-enabled |
| **Save Error** | API fails | Canvas remains editable | Error message in sidebar | Re-enabled (retry possible) |
| **Validation Error** | Invalid workflow structure | Red borders on invalid nodes | Error list in sidebar | Disabled until fixed |

**Key Questions for Editor:**
- Does it auto-save drafts?
- Can user publish/promote from editor or separate screen?
- Are there undo/redo controls?
- Can user duplicate nodes?
- Keyboard shortcuts?

---

## Task 3: Component State & Interaction Documentation

### Objective
Document all reusable UI components and their states.

### Method

**File:** `docs/components/component-states.md`

```markdown
# ACOS UI Component States

## Button Component
**Used in:** All screens (Create, Save, Delete, Retry, Link, Unlink, Export, Validate, Refresh)

### States:
- **Default:** Background color, cursor pointer, clickable
- **Hover:** Background darkened, subtle shadow
- **Active/Pressed:** Background deeper, inner shadow
- **Disabled:** Gray background, gray text, cursor not-allowed, no hover effect
- **Loading:** Spinner icon + "Loading..." text, disabled
- **Success:** Green background, checkmark icon, fade after 2s
- **Error/Danger:** Red background, warning icon

### Variants in ACOS:
- Primary: "Create Workflow", "Create Agent", "Create Skill", "Create Tenant"
- Secondary: "Link WhatsApp", "Link Telegram"
- Danger: Implied "Delete" actions
- Ghost: "Refresh", "Retry"

## Table Component
**Used in:** Workflows, Agents, Skills, Tenants, Demo Routes results, Analytics

### Features:
- Sortable columns (click header to sort A→Z or Z→A)
- Selectable rows (checkbox column)
- Pagination (if 20+ rows)
- Filters (search box, filter pills)
- Row actions menu (... button for Edit, Delete, etc.)
- Responsive: On mobile, collapse to cards

### States:
- **Empty:** No rows, empty state message
- **Loading:** Skeleton rows (8 placeholder rows)
- **Loaded:** Data rows displayed
- **Row Hover:** Highlight row, show action buttons
- **Row Selected:** Highlight row, checkbox checked, bulk action toolbar appears
- **Sorting:** Column header highlighted, sort indicator (▲/▼)
- **Filtering:** Rows filtered, filter pills visible, "Clear filters" button

## Form Component (Create/Edit Modals)

### Found In:
- Create Workflow modal
- Create Agent modal
- Create Skill modal
- Create Tenant modal
- Channel link modals

### Fields & States:
Each field has:
- **Default:** Placeholder text, empty input
- **Focused:** Blue border, cursor in field
- **Filled:** Text entered, border normal
- **Error:** Red border, error message below field, icon
- **Disabled:** Gray background, cursor not-allowed
- **Readonly:** Gray background, no cursor change
- **Loading:** Spinner (for async validation or submit)

### Form-Level States:
- **Pristine:** Submit button disabled, no validation
- **Dirty:** User changed field, submit button enabled
- **Submitting:** All fields disabled, spinner on submit button
- **Success:** Modal closes, toast appears: "Workflow created successfully"
- **Error:** Error banner at top of modal, fields retain values for editing

## Modal/Dialog Component

### States:
- **Closed:** Not visible
- **Opening:** Fade in animation, backdrop appears
- **Open:** Full opacity, interactive
- **Closing:** Fade out, still accepting input briefly
- **Scrolling:** If content tall, scrollbar appears inside modal

### Properties:
- Backdrop: Clicking outside modal closes it (confirm first if unsaved changes?)
- Keyboard: Escape key closes modal
- Focus: Focus stays within modal (trap)

## Toast/Notification Component

### Types Found in ACOS:
- Success: "Workflow created successfully" (green, 3 sec)
- Error: "Failed to save. Please try again." (red, 5 sec or until dismissed)
- Info: "Syncing channel..." (blue, auto-dismiss or persistent)
- Warning: "Unsaved changes will be lost" (orange, until dismissed)

### Behavior:
- Position: Top-right or bottom-right
- Auto-dismiss: Success (3s), Error (5s or manual), Info (varies)
- Stack: Multiple toasts stack vertically
- Accessibility: `role="status"` or `role="alert"`

## Sidebar/Navigation Component

**File:** `src/components/Sidebar.jsx`

### Items:
- Workflows (icon + text)
- Channels (icon + text)
- Routes (icon + text)
- Agents (icon + text)
- Skills (icon + text)
- Analytics (icon + text)
- Tenants (icon + text)

### States:
- **Default:** Text visible, hover highlight
- **Active:** Current route highlighted
- **Hover:** Background color change
- **Mobile:** Collapse to icons, drawer on tap
- **Responsive:** Hide on small screens, show in bottom tab bar?

## Header Component

### Current Display:
- Left: "ACOS" logo
- Center: "Workflow Operations" (dynamic page title)
- Right: 
  - Theme toggle button (light/dark)
  - Context: "Not authenticated" (status)

### Expected:
- User avatar + dropdown (if authenticated)
- Logout button
- Notifications bell (if applicable)
- Settings icon (if applicable)
```

---

## Task 4: Create Comprehensive Test Case Matrix

### Objective
Design test cases covering all screens, states, and user actions.

### Method

**File:** `docs/test-cases/acos-test-matrix.csv`

**Structure:**
```csv
Test ID,Screen,Feature,Scenario,User Role,Precondition,Steps,Expected Result,Test Type,Status
WF-001,Workflows,List Display,Load empty workflows,unauthenticated,DB empty,1. Navigate to /ui/workflows 2. Observe page,Empty state displays: 0 metrics + empty table,Smoke,Blocked (Auth issues)
WF-002,Workflows,List Display,Load with 10 workflows,admin,10 workflows in DB,1. Navigate to /ui/workflows 2. Verify load time,Table shows all 10 rows + metrics updated,Functional,Blocked (Auth issues)
WF-003,Workflows,Search,Search by name,admin,5 workflows with "test" in name,1. Enter "test" in search 2. Wait 500ms,Table filters to 5 matching workflows,Functional,Blocked
WF-004,Workflows,Sorting,Sort by name A→Z,admin,Workflows loaded,1. Click "Workflow" column header,Table sorted A→Z + ▲ indicator visible,Functional,Blocked
WF-005,Workflows,Sorting,Sort by status,admin,Workflows loaded,1. Click "Status" column header,Table sorted by status value,Functional,Blocked
WF-006,Workflows,Pagination,Navigate to page 2,admin,20+ workflows loaded,1. Click "Next" or page 2 button,Page 2 displayed + Previous button enabled,Functional,Blocked
WF-007,Workflows,Create,Create workflow form,admin,Authenticated on Workflows,1. Click "Create Workflow" button,Modal opens with form fields,Functional,Blocked
WF-008,Workflows,Create,Form validation - name required,admin,Create modal open,1. Leave name empty 2. Click Save,Error: "Workflow name required" + red border,Validation,Blocked
WF-009,Workflows,Create,Form validation - unique name,admin,Create modal + "Test Workflow" exists,1. Enter "Test Workflow" 2. Submit,Error: "Name already exists",Validation,Blocked
WF-010,Workflows,Create,Successful creation,admin,Create modal open with valid data,1. Fill form 2. Click Save 3. Wait for response,Modal closes + Success toast + workflow in list,Functional,Blocked
WF-011,Workflows,Edit,Open existing workflow,admin,Click on workflow row,1. Click workflow row or "Edit" action,Navigates to /ui/workflows/:id/editor,Functional,Blocked
WF-012,Workflows,Delete,Delete workflow,admin,Select workflow + click delete,1. Click delete 2. Confirm in modal,Workflow removed from list + success toast,Functional,Blocked
AG-001,Agents,List Display,Empty agent list,admin,No agents exist,Navigate to /ui/agents,Empty state + Create button enabled,Functional,Blocked
AG-002,Agents,List Display,Loaded agents,admin,5+ agents exist,Navigate to /ui/agents,Table shows agents + metrics,Functional,Blocked
AG-003,Agents,Create,Create agent form,admin,On Agents screen,Click "Create Agent",Modal opens with form fields,Functional,Blocked
SK-001,Skills,List Display,Empty skills,admin,No skills,Navigate to /ui/skills,Empty state displays,Functional,Blocked
SK-002,Skills,List Display,Loaded skills,admin,10+ skills,Navigate to /ui/skills,Table shows skills + category filter,Functional,Blocked
CH-001,Channels,Link WhatsApp,Link button visible,admin,On Channels screen,View screen,WhatsApp link button visible,Functional,Blocked
CH-002,Channels,Link WhatsApp,Click Link button,admin,Not yet linked,Click "Link WhatsApp",Redirect to WhatsApp OAuth or form,Functional,Blocked
CH-003,Channels,Link Telegram,Link button visible,admin,On Channels screen,View screen,Telegram link button visible,Functional,Blocked
AN-001,Analytics,Fallback Mode,Display fallback,any,Analytics unavailable,Navigate to /ui/analytics,"Fallback mode message + Export disabled",Functional,Blocked
TN-001,Tenants,Create Tenant,Form opens,admin,On Tenants screen,Click "Create Tenant",Modal with form fields,Functional,Blocked
DR-001,Demo Routes,Validate,Run validation,admin,On Demo Routes screen,Click "Run Validation",Progress spinner + results table,Functional,Blocked
```

**Total Test Cases Target:** 200+ (minimum 25 per screen)

---

## Task 5: Baseline Defect Audit

### Objective
Identify and log all issues found during Phase 1 discovery.

### Method

**File:** `docs/defects/baseline-defects.csv`

```csv
ID,Screen,Severity,Type,Title,Steps to Reproduce,Expected,Actual,Status,Notes
BUG-001,All,High,Auth,Unauthenticated state blocks all data,"1. Navigate to any screen 2. Observe","Data loads successfully","404/403 errors, 'Not authenticated' shown",Open,"Auth flow broken or not implemented in dev env"
BUG-002,Workflows,High,API,Workflows endpoint returns 404,"1. Go to /ui/workflows 2. Check network tab","GET /api/v1/ops/workflows returns 200 + data","Returns 404 Not Found",Open,"Likely auth header issue or endpoint doesn't exist"
BUG-003,All,High,Auth,Context endpoint returns 403,"1. Go to any screen 2. Network tab: /api/v1/ops/context","Returns 200 + user context","Returns 403 Forbidden",Open,"Permission check failing - likely JWT issue"
BUG-004,Workflows,Medium,UX,Create button disabled without explanation,"1. Not authenticated 2. On workflows screen","Button shows with tooltip or clear disabled state","Button disabled with no explanation",Open,"Add hover tooltip: 'Requires authentication'"
BUG-005,All,Medium,UX,Empty state metrics show wrong count,"1. Load screen with no data","Metrics cards show N/A or 0","Shows undefined or previous data",Open,"Need to verify metric calculation"
BUG-006,Analytics,Low,UX,Export button functionality unclear,"1. Analytics screen","Export button clearly shows action (CSV/JSON options)","No indication of what Export does",Open,"Add dropdown or tooltip"
```

**Total Baseline Defects:** 3–5 critical (auth), 10–15 medium (UX), 5–10 low (polish)

---

## Task 6: Setup Test Infrastructure

### Objective
Prepare testing environment for Phase 2.

### Method

#### 6.1 Test Data Seeding

**File:** `tests/fixtures/seed-acos-data.sql`

```sql
-- Seed test workflows
INSERT INTO workflows (id, name, family, description, status) VALUES
  ('wf-001', 'Customer Support', 'support', 'Main support workflow', 'active'),
  ('wf-002', 'Order Processing', 'ecommerce', 'Checkout and order flow', 'draft'),
  ('wf-003', 'Returns Management', 'support', 'Handle returns', 'active');

-- Seed test agents
INSERT INTO agents (id, name, type, description, status) VALUES
  ('ag-001', 'Support Agent', 'human', 'For customer support tasks', 'active'),
  ('ag-002', 'Chatbot Agent', 'ai', 'LLM-powered assistant', 'active');

-- Seed test skills
INSERT INTO skills (id, name, category, description) VALUES
  ('sk-001', 'Send Email', 'communication', 'Send email via SMTP'),
  ('sk-002', 'Query Database', 'data', 'Fetch from PostgreSQL');

-- Seed test users
INSERT INTO users (id, email, role, tenant_id) VALUES
  ('user-admin-001', 'admin@acos.local', 'admin', 'tenant-001'),
  ('user-operator-001', 'operator@acos.local', 'operator', 'tenant-001'),
  ('user-readonly-001', 'viewer@acos.local', 'read-only', 'tenant-001');
```

#### 6.2 Test Account Setup

**File:** `docs/test-accounts.md`

```
Test Accounts for ACOS:

Admin Account:
- Email: admin@acos.local
- Password: AdminPassword123!
- Tenant: default
- Roles: admin
- Permissions: Create/Edit/Delete all resources, manage tenants

Operator Account:
- Email: operator@acos.local
- Password: OperatorPassword123!
- Tenant: default
- Roles: operator
- Permissions: Create/Edit workflows, approve promotions, manage channels

Read-Only Account:
- Email: viewer@acos.local
- Password: ViewerPassword123!
- Tenant: default
- Roles: read-only
- Permissions: View all screens, no create/edit/delete

Multi-Tenant User:
- Email: tenant-user@acos.local
- Password: TenantPassword123!
- Tenant: tenant-custom-001
- Permissions: Limited to own tenant resources
```

#### 6.3 Playwright Test Fixtures

**File:** `tests/e2e/fixtures/acos-helpers.ts`

```typescript
import { Page } from '@playwright/test';

export class AcosFixture {
  constructor(private page: Page) {}

  async loginAsAdmin() {
    // POST /api/v1/ops/auth/login with admin credentials
    // Store JWT in localStorage
  }

  async loginAsOperator() {
    // Similar but with operator credentials
  }

  async navigateToWorkflows() {
    await this.page.goto('/ui/workflows');
    await this.page.waitForSelector('[data-testid="workflows-table"]');
  }

  async createWorkflow(name: string, family: string) {
    // Click Create, fill form, submit
  }

  async searchWorkflows(query: string) {
    // Type in search box, wait for results
  }

  async logout() {
    // Clear JWT, navigate to login
  }
}
```

---

## Phase 1 Deliverables Checklist

- [ ] **Auth Flow Mapping** (`docs/auth-flow-mapping.md`)
  - JWT structure documented
  - Role definitions listed
  - Test accounts created

- [ ] **Access Control Matrix** (`docs/roles-access-matrix.csv`)
  - All screens mapped to required roles
  - All API endpoints mapped to required roles
  - Feature-level permissions documented

- [ ] **Screen State Documentation** (`docs/screens/`)
  - workflows-states.md (8 states)
  - agents-states.md (5+ states)
  - skills-states.md (5+ states)
  - channels-states.md (5+ states)
  - analytics-states.md (5+ states)
  - tenants-states.md (5+ states)
  - demo-routes-states.md (4+ states)
  - workflow-editor-states.md (7+ states)

- [ ] **Component State Library** (`docs/components/component-states.md`)
  - Button (6+ variants/states)
  - Table (6+ features)
  - Modal/Dialog (4 states)
  - Form fields (6 states)
  - Toast notifications (4 types)
  - Sidebar navigation (4 states)
  - Header (current + expected)

- [ ] **Test Case Matrix** (`docs/test-cases/acos-test-matrix.csv`)
  - 200+ test cases
  - Organized by screen → feature → scenario
  - Includes preconditions and expected results

- [ ] **Baseline Defect Log** (`docs/defects/baseline-defects.csv`)
  - Auth-related issues (3–5)
  - UX/UI issues (10–15)
  - API integration issues (5–10)

- [ ] **Test Infrastructure** (`tests/`)
  - Test account list with credentials
  - Seed data SQL script
  - Playwright fixtures and helpers
  - Docker compose override for test env (if needed)

---

## Phase 1 Success Criteria

✅ **All 7 screens documented with 5+ states each**  
✅ **Authentication model understood and documented**  
✅ **Role-based access mapped (admin, operator, read-only, etc.)**  
✅ **200+ test cases designed (not yet executed)**  
✅ **Component library documented (buttons, modals, forms, etc.)**  
✅ **Baseline defects logged (auth, UX, API issues)**  
✅ **Test infrastructure ready (accounts, fixtures, data)**  
✅ **No execution blockers identified for Phase 2**

---

## Phase 1 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Auth system blocked in dev** | Can't test as authenticated user | Use `ALLOW_INSECURE_DEV_AUTH=1` OR reverse-engineer JWT | High |
| **API endpoints return 404** | Can't load data to see real states | Check Ops API Swagger docs; verify routes exist | High |
| **Database empty (no test data)** | Can't test loaded/filtered states | Use seed SQL script to populate test data | Medium |
| **Responsive design not tested** | Mobile screens undocumented | Test at 375px, 768px, 1280px breakpoints | Medium |
| **Keyboard navigation not tested** | Accessibility issues missed | Tab through every screen; test SR support | Medium |

---

## Next Steps (Phase 2)

Once Phase 1 deliverables are approved:
1. **Fix Auth Issues** - Verify JWT flow and test account creation
2. **Execute Test Cases** - Run 200+ tests against all screens
3. **Audit Accessibility** - WCAG 2.1 AA compliance
4. **Design System Spec** - Document all components and tokens
5. **Create Test Automation** - Playwright test suite

---

## Appendix: ACOS Architecture Reference

```
Frontend:
├── apps/ops_ui_v2 (React + Vite + Tailwind)
│   ├── /src/pages/
│   │   ├── WorkflowRegistry.jsx (Workflows screen)
│   │   ├── WorkflowEditor.jsx (Editor)
│   │   ├── Agents.jsx
│   │   ├── Skills.jsx
│   │   ├── Channels.jsx
│   │   ├── DemoRoutes.jsx
│   │   ├── Analytics.jsx
│   │   └── Tenants.jsx
│   └── /src/components/
│       ├── Layout.jsx (Main wrapper)
│       ├── Sidebar.jsx (Navigation)
│       ├── Header.jsx (Page header)
│       └── ... (reusable components)

Backend APIs:
├── apps/ops_api (Port 8081) - Main control plane API
│   └── endpoints: /workflows, /agents, /skills, /channels, /tenants, /analytics
├── apps/shopper_api (Port 8080) - Shopper-facing API
├── apps/chat_api (Port 8001) - Chat/messaging API

Database:
└── PostgreSQL (acos-db-1)
```

---

## Document Inventory

```
docs/
├── PHASE_1_QA_AUDIT_ACOS.md (this file)
├── auth-flow-mapping.md
├── roles-access-matrix.csv
├── test-accounts.md
├── screens/
│   ├── workflows-states.md
│   ├── agents-states.md
│   ├── skills-states.md
│   ├── channels-states.md
│   ├── analytics-states.md
│   ├── tenants-states.md
│   ├── demo-routes-states.md
│   └── workflow-editor-states.md
├── components/
│   └── component-states.md
├── test-cases/
│   └── acos-test-matrix.csv
└── defects/
    └── baseline-defects.csv

tests/
├── fixtures/
│   ├── seed-acos-data.sql
│   └── acos-helpers.ts
└── e2e/ (Phase 2)
```

---

**Created:** 2026-04-15  
**Status:** Ready for Phase 1 execution  
**Next Review:** Upon completion of Phase 1 deliverables
