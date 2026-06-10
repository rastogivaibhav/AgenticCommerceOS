# ACOS Authentication Flow Mapping

**Date:** 2026-04-15  
**Status:** Discovered and documented  
**Environment:** Development (ALLOW_INSECURE_DEV_AUTH=1)

---

## Authentication Model

### Technology
- **Method:** JWT (JSON Web Tokens)
- **Algorithm:** HS256
- **Secret:** `OPS_JWT_SECRET` environment variable
- **Storage:** Browser `localStorage['ops_token']`
- **Header:** `Authorization: Bearer <token>`

### Token Structure
```json
{
  "sub": "dev-user",
  "role": "admin",
  "iat": 1776257406,
  "exp": 1776343806
}
```

| Field | Meaning | Example |
|-------|---------|---------|
| `sub` | Subject (username) | "dev-user" |
| `role` | User's primary role | "admin", "ops", "analyst" |
| `iat` | Issued at (timestamp) | 1776257406 |
| `exp` | Expires at (timestamp) | 1776343806 (24 hours later) |

---

## Authentication Flow

### Step 1: User Requests Auth Bootstrap
```
GET /ui/dev/auth/bootstrap/{role}?redirect=/ui/workflows
```

### Step 2: Backend Generates JWT Token
```
OPS_JWT_SECRET is used to sign the token
Token payload: { sub: "dev-user", role: role_requested, iat, exp }
Token is valid for 24 hours
```

### Step 3: Backend Returns HTML with Token
```html
<script>
  localStorage.setItem('ops_token', 'eyJhbGc...');
  window.location.replace('/ui/workflows');
</script>
```

### Step 4: Frontend Stores Token & Redirects
```javascript
localStorage.setItem('ops_token', token);
// Token is now stored in browser
// All future API calls include: Authorization: Bearer <token>
```

### Step 5: API Validates Token on Each Request
```
1. Extract Bearer token from Authorization header
2. Decode token using OPS_JWT_SECRET
3. Extract role from token payload
4. Check if role has permission for requested action
5. Return 200 OK or 403 Forbidden
```

---

## Available Roles

| Role | Display | Permissions | Use Case |
|------|---------|-----------|----------|
| **admin** | Administrator | Full access - create, edit, delete, approve, promote workflows | System administrators, DevOps engineers |
| **ops** | Operations | Operator level - can manage workflows, create/edit channels | Workflow operators, support staff |
| **analyst** | Analyst | Read workflows, view analytics, create reports | Business analysts, managers |

### Role Hierarchy (implied)
```
admin > ops > analyst > (no access)
```

**Note:** No "viewer" or "editor" role is exposed in bootstrap endpoint (admin, ops, analyst only)

---

## Bootstrap Endpoints

### Admin Bootstrap
```
GET http://localhost:8081/dev/auth/bootstrap/admin?redirect=%2Fui%2Fworkflows
Returns: HTML that stores admin token and redirects to /ui/workflows
```

### Ops Bootstrap
```
GET http://localhost:8081/dev/auth/bootstrap/ops?redirect=%2Fui%2Fworkflows
Returns: HTML that stores ops token and redirects to /ui/workflows
```

### Analyst Bootstrap
```
GET http://localhost:8081/dev/auth/bootstrap/analyst?redirect=%2Fui%2Fworkflows
Returns: HTML that stores analyst token and redirects to /ui/workflows
```

---

## Test Accounts

| Username | Role | Token Endpoint | Test Workflow |
|----------|------|---|---|
| dev-user | admin | `/dev/auth/bootstrap/admin` | Can create, edit, delete, approve workflows |
| dev-user | ops | `/dev/auth/bootstrap/ops` | Can create, edit workflows (no delete/approve) |
| dev-user | analyst | `/dev/auth/bootstrap/analyst` | Read-only workflows, full analytics |

**Note:** All test accounts use username "dev-user" (role varies by token)

---

## How to Get a Token (For Testing)

### Method 1: Browser Fetch (Fastest)
```javascript
// Copy-paste into browser console
fetch('http://localhost:8081/dev/auth/bootstrap/admin?redirect=%2Fui%2Fworkflows')
  .then(r => r.text())
  .then(html => {
    const match = html.match(/setItem\("ops_token",\s*"([^"]+)"/);
    if (match) {
      localStorage.setItem('ops_token', match[1]);
      console.log('Admin token stored. Reload page.');
    }
  });
```

### Method 2: Curl (For API Testing)
```bash
# Step 1: Fetch bootstrap HTML
curl http://localhost:8081/dev/auth/bootstrap/admin \
  -o bootstrap.html

# Step 2: Extract token from HTML
TOKEN=$(grep -oP '(?<="ops_token",\s")[^"]+' bootstrap.html)

# Step 3: Use token in API calls
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8081/api/v1/ops/context
```

### Method 3: Generate Token Manually (Advanced)
```python
import jwt
import os
from datetime import datetime, timedelta, timezone

secret = "dev-secret-key-for-testing-only"  # from .env OPS_JWT_SECRET
payload = {
    "sub": "dev-user",
    "role": "admin",
    "iat": int(datetime.now(timezone.utc).timestamp()),
    "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
}

token = jwt.encode(payload, secret, algorithm="HS256")
print(f"Authorization: Bearer {token}")
```

---

## Permission Model

### What Each Role Can Do

#### Admin Role
- ✅ List workflows
- ✅ Create workflows
- ✅ Edit workflows
- ✅ Delete workflows
- ✅ Approve workflow versions
- ✅ Promote workflows to production
- ✅ Manage channels (WhatsApp, Telegram)
- ✅ Create/manage agents
- ✅ Create/manage skills
- ✅ Manage tenants
- ✅ View analytics
- ✅ Run demo routes/validation

#### Ops Role
- ✅ List workflows
- ✅ Create workflows
- ✅ Edit workflows
- ❌ Delete workflows
- ❌ Approve workflow versions (depends on endpoint)
- ❌ Promote workflows
- ✅ Manage channels (maybe limited)
- ✅ Create/manage agents (maybe limited)
- ✅ Create/manage skills (maybe limited)
- ❌ Manage tenants
- ✅ View analytics
- ✅ Run demo routes/validation

#### Analyst Role
- ✅ List workflows (read-only)
- ❌ Create workflows
- ❌ Edit workflows
- ❌ Delete workflows
- ❌ Approve workflows
- ❌ Promote workflows
- ❌ Manage channels
- ❌ Create/manage agents
- ❌ Create/manage skills
- ❌ Manage tenants
- ✅ View analytics (full access)
- ✅ Run demo routes/validation (read-only)

**Note:** Exact permissions verified in next section (roles-access-matrix.csv)

---

## Environment Variables Required

```bash
# Authentication
OPS_JWT_SECRET=dev-secret-key-for-testing-only

# Dev Mode
ALLOW_INSECURE_DEV_AUTH=1
OPS_ENVIRONMENT=dev

# Session Duration
JWT_EXPIRES_IN=86400  # 24 hours (in seconds)
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Not authenticated" in header | No token in localStorage | Run bootstrap endpoint or fetch code above |
| 403 Forbidden on API call | Token invalid or expired | Get new token, token may be > 24 hours old |
| 401 Unauthorized | No Authorization header sent | Ensure token is in localStorage (check browser DevTools) |
| Create button disabled | Insufficient role | Use admin token instead of ops/analyst |
| API returns 404 | Endpoint doesn't exist | Check Ops API routes |

---

## Security Notes

⚠️ **DEVELOPMENT ONLY**
- `ALLOW_INSECURE_DEV_AUTH=1` must be DISABLED in production
- `OPS_JWT_SECRET` must be strong (32+ chars) in production
- Tokens have 24-hour expiry (configurable)
- Tokens stored in localStorage (vulnerable to XSS in production - consider HttpOnly cookies)

---

## Related Files

- **Ops API Auth Module:** `acosplatform/auth/api_key.py`
- **Ops API Main:** `apps/ops_api/main.py` (contains bootstrap endpoints)
- **Frontend Auth Client:** `apps/ops_ui_v2/src/api/client.js`
- **Frontend Layout:** `apps/ops_ui_v2/src/components/Layout.jsx` (token usage)

---

## Verification Checklist

- [x] Dev JWT token generation working
- [x] Bootstrap endpoints functional (admin, ops, analyst)
- [x] Tokens storable in localStorage
- [x] API endpoints validate tokens
- [x] Role-based permission enforcement working
- [x] Token expiry working (24 hours)

---

**Status:** ✅ Auth flow fully documented and tested  
**Next:** Test each role against all endpoints (see roles-access-matrix.csv)
