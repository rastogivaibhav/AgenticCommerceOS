# ACOS Test Accounts - Phase 1 Infrastructure

**Date:** 2026-04-15  
**Status:** Test account definitions for automated testing  
**Environment:** Development (ALLOW_INSECURE_DEV_AUTH=1)

---

## Test Account Overview

All test accounts use the username **"dev-user"** with role-based JWT tokens. Tokens are generated via bootstrap endpoints.

| Test Account | Role | Bootstrap Endpoint | Use Case |
|---|---|---|---|
| admin-test | Admin | `/dev/auth/bootstrap/admin` | Full system access, workflow approval, promotions |
| ops-test | Ops | `/dev/auth/bootstrap/ops` | Workflow creation/editing, channel linking, agent management |
| analyst-test | Analyst | `/dev/auth/bootstrap/analyst` | Read-only analytics, view workflows/agents/skills |

---

## Bootstrap Token Acquisition

### For Automated Tests (Playwright)

```javascript
// Helper function to get token for any role
async function getAuthToken(page, role) {
  // Navigate to bootstrap endpoint
  const response = await page.goto(
    `http://localhost:8081/dev/auth/bootstrap/${role}?redirect=%2Fui%2Fworkflows`
  );
  
  // Parse HTML response and extract token
  const html = await response.text();
  const tokenMatch = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
  
  if (tokenMatch && tokenMatch[1]) {
    return tokenMatch[1];
  }
  throw new Error(`Failed to extract token for role: ${role}`);
}

// Helper to authenticate as role
async function authenticateAs(page, role) {
  const token = await getAuthToken(page, role);
  await page.evaluate((tok) => {
    localStorage.setItem('ops_token', tok);
  }, token);
  await page.goto('http://localhost:5173/ui/workflows');
  await page.waitForLoadState('networkidle');
}
```

### For Manual Testing (Browser Console)

```javascript
// Admin role token acquisition
fetch('http://localhost:8081/dev/auth/bootstrap/admin?redirect=%2Fui%2Fworkflows')
  .then(r => r.text())
  .then(html => {
    const match = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
    if (match) {
      localStorage.setItem('ops_token', match[1]);
      console.log('✅ Admin token stored. Reload page.');
    }
  });

// Ops role token acquisition
fetch('http://localhost:8081/dev/auth/bootstrap/ops?redirect=%2Fui%2Fworkflows')
  .then(r => r.text())
  .then(html => {
    const match = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
    if (match) {
      localStorage.setItem('ops_token', match[1]);
      console.log('✅ Ops token stored. Reload page.');
    }
  });

// Analyst role token acquisition
fetch('http://localhost:8081/dev/auth/bootstrap/analyst?redirect=%2Fui%2Fworkflows')
  .then(r => r.text())
  .then(html => {
    const match = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
    if (match) {
      localStorage.setItem('ops_token', match[1]);
      console.log('✅ Analyst token stored. Reload page.');
    }
  });
```

---

## Token Details by Role

### Admin Token
```json
{
  "sub": "dev-user",
  "role": "admin",
  "iat": 1776257406,
  "exp": 1776343806
}
```
**Valid for:** 24 hours  
**Storage:** `localStorage['ops_token']`  
**Header:** `Authorization: Bearer <token>`  
**Permissions:** Full CRUD + approval + promotion on all resources

---

### Ops Token
```json
{
  "sub": "dev-user",
  "role": "ops",
  "iat": 1776257406,
  "exp": 1776343806
}
```
**Valid for:** 24 hours  
**Permissions:** Create, read, update (but not delete or approve) on workflows, agents, skills, channels

---

### Analyst Token
```json
{
  "sub": "dev-user",
  "role": "analyst",
  "iat": 1776257406,
  "exp": 1776343806
}
```
**Valid for:** 24 hours  
**Permissions:** Read-only view of workflows, agents, skills; full analytics access

---

## Test Data Requirements

### Pre-Test State

Before running test suites, the following test data must be present in the database:

#### Workflows (5 seed workflows)
- **WF-BASIC-001:** Simple 2-node workflow (trigger → action)
- **WF-MULTI-002:** Multi-step workflow with 5 nodes and decision branches
- **WF-ERROR-003:** Workflow with intentional error nodes for error handling tests
- **WF-CHANNEL-004:** Workflow that integrates with WhatsApp/Telegram channels
- **WF-EMPTY-005:** Empty workflow (no nodes) - for validation tests

#### Agents (3 seed agents)
- **AGENT-AI-001:** AI agent (Claude) for workflow execution
- **AGENT-HUMAN-002:** Human agent (support team) for approval workflows
- **AGENT-DUMMY-003:** Dummy agent for testing agent deletion

#### Skills (4 seed skills)
- **SKILL-SEND-MSG:** Send message skill (communication category)
- **SKILL-FETCH-DATA:** Fetch data skill (integration category)
- **SKILL-TRANSFORM:** Transform data skill (data category)
- **SKILL-UNUSED:** Unused skill (for deletion testing)

#### Channels (Testing setup)
- **WhatsApp:** Pre-configured with phone number ID (for linking tests)
- **Telegram:** Pre-configured with bot token (for linking tests)

#### Tenants (Admin only - 2 test tenants)
- **TENANT-PRIMARY:** Primary tenant with users (for deletion testing)
- **TENANT-SECONDARY:** Secondary tenant (for CRUD testing)

---

## Token Refresh Strategy

### When Tokens Expire

If a test runs longer than expected and token expires mid-test:

```javascript
// Detect token expiry and refresh
async function ensureValidToken(page, role) {
  const token = JSON.parse(localStorage.getItem('ops_token') || '{}');
  const currentTime = Math.floor(Date.now() / 1000);
  
  // Refresh if expired or < 5 minutes remaining
  if (token.exp < currentTime + 300) {
    await authenticateAs(page, role);
  }
}
```

### Recommended Test Isolation

For parallel test execution:
1. Each test worker gets its own unique role token
2. Tokens are refreshed before each test suite
3. Tokens are cleared in test teardown (for isolation)

```javascript
test.beforeEach(async ({ page }, testInfo) => {
  // Determine role based on test file/tag
  const role = testInfo.tags.includes('@admin') ? 'admin' : 
               testInfo.tags.includes('@ops') ? 'ops' : 'analyst';
  
  // Authenticate with appropriate role
  await authenticateAs(page, role);
});

test.afterEach(async ({ page }) => {
  // Clear token for isolation
  await page.evaluate(() => {
    localStorage.removeItem('ops_token');
  });
});
```

---

## API Testing with Tokens

### Using Token in API Calls (Fetch)

```javascript
async function apiCall(endpoint, method = 'GET', body = null) {
  const token = localStorage.getItem('ops_token');
  
  const response = await fetch(
    `http://localhost:8081${endpoint}`,
    {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: body ? JSON.stringify(body) : null
    }
  );
  
  return response.json();
}

// Example: List workflows
const workflows = await apiCall('/api/v1/ops/workflows', 'GET');

// Example: Create workflow
const newWorkflow = await apiCall('/api/v1/ops/workflows', 'POST', {
  name: 'Test Workflow',
  family: 'test-family',
  description: 'Created during testing'
});
```

### Using Token in Curl

```bash
# Set token variable
TOKEN=$(node -e "
  const jwt = require('jsonwebtoken');
  const secret = 'dev-secret-key-for-testing-only';
  const token = jwt.sign(
    { sub: 'dev-user', role: 'admin' },
    secret,
    { expiresIn: '24h' }
  );
  console.log(token);
")

# Use token in API call
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8081/api/v1/ops/workflows
```

---

## Role-Based Test Scenarios

### Admin-Only Tests
- ✅ Workflow approval
- ✅ Workflow promotion to production
- ✅ Workflow deletion
- ✅ Tenant management (CRUD)
- ✅ Channel unlinking

### Ops-Only Tests
- ✅ Workflow creation/editing
- ✅ Agent creation/editing
- ✅ Skill creation/editing
- ✅ Channel linking (WhatsApp, Telegram)

### Analyst-Only Tests
- ✅ Workflow viewing (read-only)
- ✅ Analytics full access
- ✅ Demo route validation

### Cross-Role Tests
- ✅ All roles can list workflows (analyst read-only)
- ✅ All roles can view analytics
- ✅ All roles can run demo route validation

---

## Test Account Isolation

For concurrent testing, use separate browser contexts with different tokens:

```javascript
const adminContext = await browser.newContext();
const opsContext = await browser.newContext();
const analystContext = await browser.newContext();

// Load tokens into each context
await authenticateAs(adminContext.pages()[0], 'admin');
await authenticateAs(opsContext.pages()[0], 'ops');
await authenticateAs(analystContext.pages()[0], 'analyst');

// Run tests concurrently with isolated contexts
await Promise.all([
  testAdminFeatures(adminContext),
  testOpsFeatures(opsContext),
  testAnalystFeatures(analystContext)
]);

// Clean up
await adminContext.close();
await opsContext.close();
await analystContext.close();
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Token not found in HTML | Bootstrap endpoint not responding. Check backend service. |
| localStorage is empty after auth | Check browser privacy/incognito mode settings. |
| API returns 403 with valid token | Token may have wrong role. Verify role matches endpoint requirements. |
| Token expired during test | Use `ensureValidToken()` helper before critical operations. |
| "Not authenticated" in header | Token not in localStorage. Call `authenticateAs()` again. |

---

## Related Documentation

- **Auth Flow:** docs/auth-flow-mapping.md
- **Roles Access Matrix:** docs/roles-access-matrix.csv
- **Test Matrix:** docs/test-cases/acos-comprehensive-test-matrix.csv
- **Playwright Fixtures:** tests/fixtures/acos-helpers.ts

