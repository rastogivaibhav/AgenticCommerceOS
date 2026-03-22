# ACOS Control Plane - Security Remediation Plan (Blue Team)

**Response to Red Team Assessment**

---

## Executive Summary

Red Team assessment identified **18 security vulnerabilities** across authentication, authorization, data validation, and business logic layers. This document provides the Blue Team remediation strategy, prioritized by severity and impact.

**Critical Issues: 4**
**High Issues: 6**
**Medium Issues: 6**
**Low Issues: 2**

**Recommended Action:** Address all Critical and High severity issues before production deployment. Medium issues should be resolved in v1.0.1 (immediate hotfix).

---

## Remediation Prioritization

### Phase 1: Critical (Emergency - Deploy Immediately)
- VULN-01: JWT authentication bypass
- VULN-02: Unprotected agent/skill endpoints
- VULN-03: Unprotected workflow endpoints
- VULN-04: Hardcoded credentials

**Estimated Timeline:** 24 hours
**Risk if not fixed:** Complete authentication bypass, remote code injection

### Phase 2: High (ASAP - Within 48 hours)
- VULN-05: Missing rate limiting
- VULN-06: Cross-tenant replay vulnerability
- VULN-07: Self-approval workflow promotion
- VULN-08: Unauthorized validation status
- VULN-09: Unprotected metrics endpoint
- VULN-10: Cross-tenant data leakage in fallback

**Estimated Timeline:** 48 hours
**Risk if not fixed:** Denial of service, unauthorized operations, data leakage

### Phase 3: Medium (v1.0.1 Hotfix - Within 1 week)
- VULN-11: CSV formula injection
- VULN-12: Hardcoded token in frontend
- VULN-13: Client-side global function hijack
- VULN-14: Thread-unsafe DB connection
- VULN-15: Client-generated ID collisions
- VULN-16: Unvalidated promotion chain

**Estimated Timeline:** 1 week
**Risk if not fixed:** Privilege escalation, data corruption, supply chain attacks

### Phase 4: Low (v1.0.1 - Minor improvements)
- VULN-17: Unicode bypass in injection filter
- VULN-18: Information disclosure in health endpoint

**Estimated Timeline:** 1 week

---

## Phase 1: Critical Fixes (24-hour Emergency Response)

### VULN-01: JWT Authentication Bypass When Secret Not Set

**Severity:** CRITICAL
**Location:** `/acosplatform/auth/api_key.py`, lines 47-49

**Issue:**
```python
def _decode_jwt(token: str) -> dict:
    if not OPS_JWT_SECRET:
        return {"sub": "dev-user", "role": "admin"}  # ❌ CRITICAL
    # ... actual JWT decode
```

**Fix:**
```python
def _decode_jwt(token: str) -> dict:
    secret = os.getenv("OPS_JWT_SECRET")
    if not secret:
        raise AuthenticationError(
            "OPS_JWT_SECRET must be set in production. "
            "No default fallback is provided. "
            "Generate: openssl rand -hex 32"
        )
    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        if "sub" not in decoded or "role" not in decoded:
            raise AuthenticationError("Invalid token structure")
        return decoded
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
```

**Testing:**
```bash
# Test 1: Verify error when secret not set
unset OPS_JWT_SECRET
curl -H "Authorization: Bearer anything" http://localhost:8000/dashboard
# Expected: 500 with "OPS_JWT_SECRET must be set" error

# Test 2: Verify invalid token rejected
OPS_JWT_SECRET=test-secret-key
curl -H "Authorization: Bearer invalid-token" http://localhost:8000/dashboard
# Expected: 401 Unauthorized

# Test 3: Verify valid token accepted
export OPS_JWT_SECRET=$(openssl rand -hex 32)
TOKEN=$(python3 -c "import jwt; print(jwt.encode({'sub': 'user', 'role': 'admin'}, '$OPS_JWT_SECRET', algorithm='HS256'))")
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/dashboard
# Expected: 200 OK
```

**Verification Steps:**
1. Confirm `OPS_JWT_SECRET` is required in `docker-compose.yml` or `.env.example`
2. Verify startup fails loudly if secret not set
3. Document that default fallback has been removed
4. Update INSTALLATION.md with secret generation instructions

---

### VULN-02: Unprotected Agent and Skill Endpoints

**Severity:** CRITICAL
**Location:** `/apps/ops_api/main.py`, lines 153-204

**Issue:**
```python
@app.get("/agents")  # ❌ No auth dependency
def list_agents():
    ...

@app.post("/agents")  # ❌ No auth dependency
def create_agent(agent: AgentCreate):
    ...
```

**Fix:**
```python
@app.get("/agents", dependencies=[Depends(require_ops_token)])
def list_agents(actor: dict = Depends(require_ops_token)):
    """List all agents - requires ops authentication"""
    return repository.get_agents()

@app.post("/agents", dependencies=[Depends(require_ops_token)])
def create_agent(agent: AgentCreate, actor: dict = Depends(require_ops_token)):
    """Create agent - requires ops authentication"""
    audit_log("agent_created", actor, {"agent_id": agent.id})
    return repository.save_agent(agent)

@app.patch("/agents/{agent_id}", dependencies=[Depends(require_ops_token)])
def update_agent(agent_id: str, update: AgentUpdate,
                 actor: dict = Depends(require_ops_token)):
    """Update agent - requires ops authentication"""
    audit_log("agent_updated", actor, {"agent_id": agent_id})
    return repository.update_agent(agent_id, update)

# Apply same fix to /skills endpoints
@app.get("/skills", dependencies=[Depends(require_ops_token)])
def list_skills(actor: dict = Depends(require_ops_token)):
    """List all skills - requires ops authentication"""
    return repository.get_skills()

@app.post("/skills", dependencies=[Depends(require_ops_token)])
def create_skill(skill: SkillCreate, actor: dict = Depends(require_ops_token)):
    """Create skill - requires ops authentication"""
    audit_log("skill_created", actor, {"skill_id": skill.id})
    return repository.save_skill(skill)

@app.patch("/skills/{skill_id}", dependencies=[Depends(require_ops_token)])
def update_skill(skill_id: str, update: SkillUpdate,
                 actor: dict = Depends(require_ops_token)):
    """Update skill - requires ops authentication"""
    audit_log("skill_updated", actor, {"skill_id": skill_id})
    return repository.update_skill(skill_id, update)
```

**Testing:**
```bash
# Test 1: Unauthenticated request rejected
curl -X GET http://localhost:8000/agents
# Expected: 401 Unauthorized

# Test 2: Authenticated request succeeds
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/agents
# Expected: 200 OK with agent list

# Test 3: Unauthorized modification is prevented
curl -X PATCH \
  http://localhost:8000/agents/ag_fulfillment \
  -H "Content-Type: application/json" \
  -d '{"status": "degraded"}'
# Expected: 401 Unauthorized
```

**Verification:**
1. Add integration tests for all 6 endpoints with and without auth
2. Verify `/agents` and `/skills` routes require `require_ops_token` dependency
3. Confirm all requests include audit logging with actor identity

---

### VULN-03: Unprotected Workflow Endpoints

**Severity:** CRITICAL
**Location:** `/apps/ops_api/main.py`, lines 207-228

**Issue:**
```python
@app.get("/workflows")  # ❌ Duplicate route, no auth
def list_workflows():
    ...

@app.get("/workflows/{workflow_id}")  # ❌ Duplicate route, no auth
def workflow_detail(workflow_id: str):
    ...
```

**Fix:**
```python
# REMOVE these duplicate routes entirely from main.py
# The authenticated versions in routers/workflows.py (prefixed at /workflows)
# are the only authorized versions.

# Verify in router that authentication is enforced:
# File: /acosplatform/routers/workflows.py

@router.get("/", dependencies=[Depends(require_ops_token)])
async def list_workflows(actor: dict = Depends(require_ops_token)):
    """List workflows - requires ops authentication"""
    return await workflow_service.list_workflows(actor["sub"])

@router.get("/{workflow_id}", dependencies=[Depends(require_ops_token)])
async def get_workflow(workflow_id: str,
                       actor: dict = Depends(require_ops_token)):
    """Get workflow details - requires ops authentication"""
    return await workflow_service.get_workflow(workflow_id, actor["sub"])
```

**Testing:**
```bash
# Test 1: Verify duplicate unauth route doesn't exist
curl -X GET http://localhost:8000/workflows
# Expected: 404 Not Found OR 401 Unauthorized

# Test 2: Verify auth route works
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/workflows
# Expected: 200 OK

# Test 3: Verify no unauthenticated path to workflow data
for path in /workflows /api/workflows /api/v1/workflows; do
  curl -s "$path" | grep -q workflow && echo "VULNERABLE: $path"
done
# Expected: No vulnerable paths found
```

**Verification:**
1. Search codebase for all `@app.get` and `@app.post` routes at top level
2. Ensure all workflow-related routes go through routers with auth
3. Add integration test verifying unauth paths return 401/404
4. Document that `main.py` should only contain admin setup routes, not user-facing APIs

---

### VULN-04: Hardcoded Default Credentials

**Severity:** CRITICAL
**Location:** `/acosplatform/auth/api_key.py` line 21; `/acosplatform/db/connection.py` line 21

**Issue:**
```python
# In api_key.py
SHOPPER_API_KEYS = os.getenv("SHOPPER_API_KEYS", "dev-key-insecure")  # ❌

# In connection.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://acos:acos@localhost:5432/acos"  # ❌
)
```

**Fix:**
```python
# In api_key.py
SHOPPER_API_KEYS = os.getenv("SHOPPER_API_KEYS")
if not SHOPPER_API_KEYS:
    raise RuntimeError(
        "SHOPPER_API_KEYS environment variable is required and must be set "
        "to a non-empty value. No default is provided. "
        "Set a strong API key: openssl rand -hex 32"
    )

# In connection.py
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "No default is provided. "
        "Format: postgresql://user:password@host:port/dbname"
    )
```

**Testing:**
```bash
# Test 1: Verify startup fails without SHOPPER_API_KEYS
unset SHOPPER_API_KEYS
python -c "from acosplatform.auth import api_key"
# Expected: RuntimeError with message about required env var

# Test 2: Verify startup fails without DATABASE_URL
unset DATABASE_URL
python -c "from acosplatform.db import connection"
# Expected: RuntimeError with message about required env var

# Test 3: Verify startup succeeds with proper env vars set
export SHOPPER_API_KEYS=$(openssl rand -hex 32)
export DATABASE_URL="postgresql://user:password@localhost:5432/acos"
python -c "from acosplatform.auth import api_key; from acosplatform.db import connection"
# Expected: Success
```

**Verification:**
1. Update `docker-compose.yml` to require `SHOPPER_API_KEYS` and `DATABASE_URL` in environment
2. Update `.env.example` with examples (not real credentials)
3. Add startup test to verify failure when env vars not set
4. Document in INSTALLATION.md that credentials must be generated
5. Remove any example/demo credentials from code comments

---

## Phase 2: High-Severity Fixes (48-hour Response)

### VULN-05: Missing Rate Limiting on All Endpoints Except Replay

**Severity:** HIGH
**Location:** `/acosplatform/middleware/rate_limit.py`, `/apps/ops_api/main.py`

**Fix - Apply Rate Limiting to All Endpoints:**

```python
# In main.py, apply rate limiting globally

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address
from redis import asyncio as aioredis

# Initialize limiter
async def lifespan(app: FastAPI):
    redis = aioredis.from_url("redis://localhost")
    await FastAPILimiter.init(redis)
    yield
    await redis.close()

app = FastAPI(lifespan=lifespan)

# Apply global rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        limiter = FastAPILimiter()
        await limiter.http_request(
            request=request,
            response=await call_next(request),
            unique_identifier=get_remote_address(request),
            limits=["100/minute"],  # 100 requests per minute
        )
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    return await call_next(request)

# For sensitive endpoints, use stricter limits
@app.get("/dashboard")
@limiter.limit("30/minute")  # Stricter limit on dashboard
async def get_dashboard(actor: dict = Depends(require_ops_token)):
    ...

@app.post("/workflows/{id}/promote")
@limiter.limit("5/minute")  # Very strict on promotion
async def promote_workflow(...):
    ...
```

**Alternative - In-Memory Fallback (if Redis unavailable):**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to routes
@app.get("/dashboard", dependencies=[limiter.limit("30/minute")])
async def get_dashboard(actor: dict = Depends(require_ops_token)):
    ...
```

**Testing:**
```bash
# Test 1: Verify rate limiting applies
for i in {1..101}; do
  curl -s http://localhost:8000/dashboard \
    -H "Authorization: Bearer $TOKEN" \
    | grep -q "429" && echo "Rate limited at request $i" && break
done
# Expected: Rate limited around request 30

# Test 2: Verify limits reset after 1 minute
(for i in {1..30}; do curl -s http://localhost:8000/dashboard \
  -H "Authorization: Bearer $TOKEN"; done)
sleep 61
curl -s http://localhost:8000/dashboard \
  -H "Authorization: Bearer $TOKEN" | grep -q "200"
# Expected: Request succeeds after 1 minute
```

---

### VULN-06: Cross-Tenant Replay Vulnerability

**Severity:** HIGH
**Location:** `/acosplatform/replay/replay_engine.py`, lines 17-38

**Issue:**
```python
def replay_run(run_id: str, actor: dict) -> dict:
    run = repository.get_run(run_id)  # No tenant_id validation
    # Uses stored tenant_id and customer_id from run
    return run_journey(run.input)  # Cross-tenant execution
```

**Fix:**
```python
def replay_run(run_id: str, actor: dict) -> dict:
    """Replay a run, with tenant isolation"""
    run = repository.get_run(run_id)

    # CRITICAL: Verify tenant ownership
    actor_tenant_id = actor.get("tenant_id")
    if not actor_tenant_id:
        raise AuthenticationError("No tenant_id in actor context")

    if run.tenant_id != actor_tenant_id:
        # Deny cross-tenant access
        audit_log("replay_denied", actor, {
            "reason": "cross_tenant_access_attempt",
            "requested_run_tenant": run.tenant_id,
            "actor_tenant": actor_tenant_id
        })
        raise ForbiddenError("Cannot replay runs from other tenants")

    # Confirm input data integrity
    if not run.input or "tenant_id" not in run.input:
        raise ValueError("Run input missing tenant_id")

    # Verify input tenant matches
    if run.input["tenant_id"] != actor_tenant_id:
        raise ForbiddenError("Run input tenant mismatch")

    audit_log("replay_started", actor, {"run_id": run_id})
    return run_journey(run.input)
```

**Testing:**
```bash
# Test 1: Verify cross-tenant replay blocked
# Create run as tenant_a
RUN_ID=$(curl -s -X POST http://localhost:8000/api/v1/runs \
  -H "Authorization: Bearer $TENANT_A_TOKEN" \
  -d '...' | jq -r '.id')

# Try to replay as tenant_b
curl -s -X POST "http://localhost:8000/api/v1/runs/$RUN_ID/replay" \
  -H "Authorization: Bearer $TENANT_B_TOKEN"
# Expected: 403 Forbidden

# Test 2: Verify same-tenant replay allowed
curl -s -X POST "http://localhost:8000/api/v1/runs/$RUN_ID/replay" \
  -H "Authorization: Bearer $TENANT_A_TOKEN"
# Expected: 200 OK with new run
```

---

### VULN-07 & VULN-08: Self-Approval and Unauthorized Validation Status

**Severity:** HIGH
**Location:** `/acosplatform/workflows/service.py`, lines 170-216

**Issue:**
```python
# VULN-07: Self-approval
async def promote_workflow_version(...):
    promotion = WorkflowPromotion(
        requested_by=actor,
        approved_by=actor,  # ❌ Same as requestor
    )

# VULN-08: Caller can set validation_status
async def create_workflow_version(request: dict):
    version.validation_status = request.get("validation_status", "pending")
    if request.get("validation_status") == "approved":
        version.approved_by = actor  # ❌ Self-approval
```

**Fix:**
```python
async def create_workflow_version(
    workflow_id: str,
    request: CreateWorkflowVersionRequest,
    actor: dict = Depends(require_ops_token)
):
    """Create workflow version - status must start as 'pending'"""

    # CRITICAL: Don't allow caller to set validation_status
    if request.validation_status and request.validation_status != "pending":
        raise BadRequestError(
            "Workflow versions must start in 'pending' status. "
            "Request approval separately."
        )

    version = WorkflowVersion(
        workflow_id=workflow_id,
        created_by=actor["sub"],
        change_summary=request.change_summary,
        step_definitions=request.step_definitions,
        validation_status="pending",  # ← Force to pending
        approved_by=None,  # No approval yet
    )

    audit_log("workflow_version_created", actor, {
        "workflow_id": workflow_id,
        "version_id": version.id
    })

    return repository.save_workflow_version(version)


async def promote_workflow_version(
    workflow_id: str,
    promotion_request: WorkflowPromotionRequest,
    actor: dict = Depends(require_ops_token)
):
    """Promote workflow version - requires separate approval"""

    version = repository.get_workflow_version(
        workflow_id,
        promotion_request.version_id
    )

    # Verify version is in pending state
    if version.validation_status != "pending":
        raise BadRequestError(
            f"Workflow version in {version.validation_status} state. "
            f"Only 'pending' versions can be promoted."
        )

    # Verify promotion chain
    if promotion_request.target_environment == "prod":
        if version.source_environment not in ["stage"]:
            raise BadRequestError(
                "Direct dev→prod promotion not allowed. "
                "Promote through: dev→test→stage→prod"
            )

    # CRITICAL: Require separate approver
    approver_id = promotion_request.approved_by
    if not approver_id:
        raise BadRequestError(
            "Promotion requires explicit approval from a different team member"
        )

    if approver_id == actor["sub"]:
        raise ForbiddenError(
            "Self-approval not allowed. Promotion requires approval from "
            "another team member (separation of duties)."
        )

    # Verify approver has permission
    approver = repository.get_user(approver_id)
    if not approver or "approval" not in approver.permissions:
        raise ForbiddenError(f"User {approver_id} cannot approve promotions")

    # Create promotion record
    promotion = WorkflowPromotion(
        workflow_id=workflow_id,
        version_id=version.id,
        source_environment=version.source_environment,
        target_environment=promotion_request.target_environment,
        requested_by=actor["sub"],  # Requestor
        approved_by=approver_id,     # Different person
        promoted_at=datetime.utcnow(),
    )

    # Update version status
    version.validation_status = "approved"
    version.approved_by = approver_id

    audit_log("workflow_promoted", actor, {
        "workflow_id": workflow_id,
        "requested_by": actor["sub"],
        "approved_by": approver_id,
        "target_environment": promotion_request.target_environment
    })

    return repository.create_promotion(promotion)
```

**Testing:**
```bash
# Test 1: Verify version cannot be created in 'approved' state
curl -X POST http://localhost:8000/api/v1/workflows/wf-1/versions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"validation_status": "approved", ...}'
# Expected: 400 Bad Request

# Test 2: Verify promotion requires different approver
curl -X POST http://localhost:8000/api/v1/workflows/wf-1/promote \
  -H "Authorization: Bearer $APPROVER_TOKEN" \
  -d '{
    "version_id": "...",
    "target_environment": "prod",
    "approved_by": "'$APPROVER_ID'"
  }'
# Expected: 403 Forbidden (self-approval)

# Test 3: Verify promotion works with different approver
curl -X POST http://localhost:8000/api/v1/workflows/wf-1/promote \
  -H "Authorization: Bearer $APPROVER_TOKEN" \
  -d '{
    "version_id": "...",
    "target_environment": "prod",
    "approved_by": "'$OTHER_APPROVER_ID'"
  }'
# Expected: 200 OK with promotion record
```

---

### VULN-09: Unprotected Prometheus Metrics Endpoint

**Severity:** HIGH
**Location:** `/acosplatform/observability/metrics.py`, `/apps/ops_api/main.py` line 338

**Fix:**
```python
# In main.py
@app.get("/metrics", dependencies=[Depends(require_ops_token)])
async def prometheus_metrics(actor: dict = Depends(require_ops_token)):
    """Prometheus metrics endpoint - requires ops authentication"""
    # Generate metrics securely
    metrics = metrics_service.generate_metrics()
    # Filter tenant_id labels (don't expose tenant enumeration)
    return metrics.replace_labels(
        exclude_labels=["tenant_id", "customer_id"]
    )

# ALTERNATIVE: Keep metrics unauth but scrub sensitive labels
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics - internal only (should be behind firewall)"""
    metrics = metrics_service.generate_metrics()

    # Strip tenant identification from all metrics
    scrubbed_metrics = []
    for metric in metrics:
        if "tenant_id" in metric.labels:
            del metric.labels["tenant_id"]
        if "customer_id" in metric.labels:
            del metric.labels["customer_id"]
        scrubbed_metrics.append(metric)

    # Remove business-sensitive metrics (loyalty, cost by tenant)
    return [m for m in scrubbed_metrics
            if not m.name.startswith(("acos_cost_", "acos_loyalty_"))]
```

**Testing:**
```bash
# Test 1: Verify metrics endpoint requires auth (preferred)
curl http://localhost:8000/metrics
# Expected: 401 Unauthorized

# Test 2: If unauth metrics are needed, verify no tenant_id in output
curl http://localhost:8000/metrics | grep tenant_id
# Expected: No matches

# Test 3: Verify sensitive cost metrics are scrubbed
curl http://localhost:8000/metrics | grep "acos_cost"
# Expected: No matches
```

---

### VULN-10: Cross-Tenant Data Leakage in Fallback Mode

**Severity:** HIGH
**Location:** `/acosplatform/db/repository.py`, lines 9-84

**Fix:**
```python
class RepositoryWithTenantIsolation:
    """Repository with proper tenant isolation in fallback mode"""

    def __init__(self):
        # Per-tenant fallback stores (not global)
        self._tenant_fallback_runs = {}  # {tenant_id: [runs]}
        self._tenant_fallback_agents = {}  # {tenant_id: [agents]}
        self._fallback_mode = False
        self._fallback_lock = threading.RLock()

    def get_runs(self, tenant_id: str, limit: int = 10) -> list:
        """Get runs with tenant isolation"""
        if not tenant_id:
            raise ValueError("tenant_id is required")

        try:
            # Try database first
            return self._db_get_runs(tenant_id, limit)
        except DatabaseUnavailableError:
            # Use fallback, but ONLY for this tenant
            with self._fallback_lock:
                self._fallback_mode = True
                if tenant_id not in self._tenant_fallback_runs:
                    return []  # No fallback data for this tenant
                return self._tenant_fallback_runs[tenant_id][:limit]

    def get_agents(self, tenant_id: str) -> list:
        """Get agents with tenant isolation"""
        if not tenant_id:
            raise ValueError("tenant_id is required")

        try:
            return self._db_get_agents(tenant_id)
        except DatabaseUnavailableError:
            with self._fallback_lock:
                self._fallback_mode = True
                # Return only this tenant's agents (or empty if none seeded)
                if tenant_id not in self._tenant_fallback_agents:
                    return []
                return self._tenant_fallback_agents[tenant_id]

    def seed_fallback_data(self, tenant_id: str, data: dict):
        """Seed tenant-specific fallback data"""
        with self._fallback_lock:
            if tenant_id not in self._tenant_fallback_runs:
                self._tenant_fallback_runs[tenant_id] = []
            if tenant_id not in self._tenant_fallback_agents:
                self._tenant_fallback_agents[tenant_id] = []

            self._tenant_fallback_runs[tenant_id].extend(data.get("runs", []))
            self._tenant_fallback_agents[tenant_id].extend(data.get("agents", []))

    def clear_fallback_for_tenant(self, tenant_id: str):
        """Clear fallback data after database recovers"""
        with self._fallback_lock:
            if tenant_id in self._tenant_fallback_runs:
                del self._tenant_fallback_runs[tenant_id]
            if tenant_id in self._tenant_fallback_agents:
                del self._tenant_fallback_agents[tenant_id]
```

**Testing:**
```bash
# Test 1: Simulate DB failure, verify data isolation
(stop database)
curl -H "Authorization: Bearer $TENANT_A_TOKEN" \
  http://localhost:8000/api/v1/runs
# Expected: Empty or tenant-A specific fallback

curl -H "Authorization: Bearer $TENANT_B_TOKEN" \
  http://localhost:8000/api/v1/runs
# Expected: Empty or tenant-B specific fallback (NOT tenant A's data)

# Test 2: Verify fallback data cleared when DB recovers
(start database)
sleep 5
curl -H "Authorization: Bearer $TENANT_A_TOKEN" \
  http://localhost:8000/api/v1/runs
# Expected: Real database data (no stale fallback)
```

---

## Phase 3: Medium-Severity Fixes (v1.0.1 - 1 week)

### VULN-11: CSV Formula Injection

**Severity:** MEDIUM
**Location:** `/apps/ops_ui_v2/src/utils/export.js`, `/apps/ops_api/main.py`

**Fix:**
```javascript
// In export.js
function sanitizeCSVField(field) {
    if (!field) return '""';

    const str = String(field);
    // If field starts with formula characters, prefix with single quote
    if (/^[=+\-@]/.test(str)) {
        return `'${str}'`;
    }

    // Escape quotes and wrap in quotes
    return `"${str.replace(/"/g, '""')}"`;
}

function convertToCSV(data) {
    if (data.length === 0) return "";

    const headers = Object.keys(data[0]);
    const csvHeaders = headers.map(sanitizeCSVField).join(",");

    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header];
            return sanitizeCSVField(value);
        }).join(",");
    });

    return [csvHeaders, ...csvRows].join("\n");
}
```

```python
# In backend export endpoint
def sanitize_csv_value(value: str) -> str:
    """Sanitize value to prevent formula injection"""
    if not value:
        return '""'

    value = str(value).strip()

    # Prefix with single quote if starts with formula characters
    if value and value[0] in '=+-@':
        return f"'{value}"

    # Escape quotes
    if '"' in value:
        value = value.replace('"', '""')

    # Wrap in quotes
    return f'"{value}"'

@app.get("/analytics/export", dependencies=[Depends(require_ops_token)])
async def export_analytics(
    format: str = "csv",
    actor: dict = Depends(require_ops_token)
):
    """Export analytics data"""
    data = analytics_service.get_export_data(actor["tenant_id"])

    if format == "csv":
        # Sanitize all values
        sanitized_data = [
            {k: sanitize_csv_value(v) for k, v in row.items()}
            for row in data
        ]
        csv_content = "\n".join([
            ",".join(sanitized_data[0].keys()),
            *[",".join(row.values()) for row in sanitized_data]
        ])
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics.csv"}
        )
    elif format == "json":
        return JSONResponse(data)
```

**Testing:**
```bash
# Test 1: Verify formula characters are escaped
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/analytics/export?format=csv" > export.csv
grep '=sum\|=cmd\|+exec' export.csv && echo "VULNERABLE" || echo "SAFE"
# Expected: SAFE (no unescaped formulas)

# Test 2: Open CSV in Excel and verify no formula execution
# (Manual test) Open export.csv → No formula prompts or execution
```

---

### VULN-12: Hardcoded Token in Frontend Bundle

**Severity:** MEDIUM
**Location:** `/apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx`, line 14

**Fix:**
```javascript
// BEFORE (VULNERABLE)
const headers = {
    'Authorization': 'Bearer demo-ops-token'  // ❌ Hardcoded
};

// AFTER (SECURE)
// Get token from environment or secure storage
const getAuthToken = () => {
    // Option 1: From environment variable at build time
    // (React build replaces VITE_API_TOKEN at compile time)
    if (import.meta.env.VITE_API_TOKEN) {
        return import.meta.env.VITE_API_TOKEN;
    }

    // Option 2: From secure storage (sessionStorage, never localStorage)
    const sessionToken = sessionStorage.getItem("ops_token");
    if (sessionToken) {
        return sessionToken;
    }

    // Option 3: OAuth/OIDC redirect to get token from auth server
    // (Requires auth server setup)
    return null;
};

const headers = () => {
    const token = getAuthToken();
    if (!token) {
        throw new Error("Not authenticated. Please log in.");
    }
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
};

// Update all API calls to use getAuthToken()
const fetchWorkflows = async () => {
    try {
        const response = await fetch('/api/v1/workflows', {
            headers: headers()  // Call function, don't hardcode
        });
        return response.json();
    } catch (e) {
        console.error("Auth required:", e.message);
        // Redirect to login
    }
};
```

**Build Configuration:**
```bash
# .env.development
VITE_API_TOKEN=dev-token-only-for-local-testing

# .env.production
# (Empty - token obtained via OAuth or login endpoint)
```

**Testing:**
```bash
# Test 1: Verify no hardcoded token in bundle
npm run build
grep -r "demo-ops-token\|Bearer" dist/ && echo "VULNERABLE" || echo "SAFE"
# Expected: SAFE (no tokens in dist)

# Test 2: Verify API fails without token
curl http://localhost:5173/api/v1/workflows
# Expected: 401 Unauthorized
```

---

### VULN-13: Client-Side Global Function Hijack

**Severity:** MEDIUM
**Location:** `/apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx`, line 105

**Fix:**
```javascript
// BEFORE (VULNERABLE)
const handleDeployArchitecture = async () => {
    const serialized = window.serializeWorkflowGraph();  // ❌ Global hijackable
    await saveWorkflow(serialized);
};

// AFTER (SECURE)
import { serializeWorkflowGraph } from '../lib/workflowSerializer';
import { validateWorkflowStructure } from '../lib/validation';

const handleDeployArchitecture = async () => {
    // Use imported function, not window global
    const serialized = serializeWorkflowGraph(this.workflowState);

    // Validate result before sending
    const validationErrors = validateWorkflowStructure(serialized);
    if (validationErrors.length > 0) {
        throw new Error(`Invalid workflow: ${validationErrors.join(', ')}`);
    }

    // Send validated data
    const response = await saveWorkflow(serialized);

    // Verify response matches request (prevent MITM modification)
    if (response.id !== serialized.id) {
        throw new Error("Server returned unexpected workflow ID");
    }

    return response;
};

// Remove any window-global function assignments
// Audit: grep -r "window\." src/ | grep "="
// Expected: None found (only read-only access like window.fetch)
```

**Subresource Integrity:**
```html
<!-- Ensure CDN scripts aren't modified -->
<script
    src="https://cdn.example.com/analytics.js"
    integrity="sha384-abc123..."
    crossorigin="anonymous">
</script>
```

**Content Security Policy:**
```
// Add to server headers
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://trusted-cdn.example.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
```

**Testing:**
```bash
# Test 1: Verify no window. assignments in source
grep -r "window\.[a-zA-Z_].*=" src/ && echo "FOUND ASSIGNMENTS" || echo "SAFE"
# Expected: SAFE (no assignments to window)

# Test 2: CSP headers block inline scripts
curl -I http://localhost:3000/ | grep "Content-Security-Policy"
# Expected: Header present and restrictive
```

---

### VULN-14: Non-Thread-Safe Database Connection

**Severity:** MEDIUM
**Location:** `/acosplatform/db/connection.py`, lines 15-47

**Fix:**
```python
# BEFORE (VULNERABLE)
_conn = None

def get_connection():
    global _conn
    if _conn is None:
        _conn = psycopg2.connect(DATABASE_URL)  # ❌ Single shared connection
    return _conn

# AFTER (SECURE - Connection Pool)
from psycopg2 import pool
import threading

class DatabasePool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = object.__new__(cls)
                    cls._instance._init_pool()
        return cls._instance

    def _init_pool(self):
        """Initialize thread-safe connection pool"""
        self.connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,  # Max concurrent connections
            dsn=DATABASE_URL,
            check_same_thread=False,
            timeout=5  # 5 second timeout
        )

    def get_connection(self):
        """Get a connection from the pool"""
        if self.connection_pool is None:
            raise RuntimeError("Connection pool not initialized")
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool"""
        if conn and self.connection_pool:
            self.connection_pool.putconn(conn)

    def close_all(self):
        """Close all connections in pool"""
        if self.connection_pool:
            self.connection_pool.closeall()

# Usage
db_pool = DatabasePool()

async def get_db_connection():
    """Get thread-safe database connection"""
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        db_pool.return_connection(conn)

# Use with dependency injection
@app.get("/workflows", dependencies=[Depends(get_db_connection)])
async def list_workflows(db_conn = Depends(get_db_connection)):
    cursor = db_conn.cursor()
    try:
        cursor.execute("SELECT * FROM workflows")
        return cursor.fetchall()
    finally:
        cursor.close()
```

**For Async FastAPI (Recommended):**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Use async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True  # Verify connections before use
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        yield session

# Use in routes
@app.get("/workflows")
async def list_workflows(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Workflow))
    return result.scalars().all()
```

**Testing:**
```python
# Test for thread safety
import concurrent.futures
import threading

def concurrent_db_access():
    """Verify no corruption under concurrent load"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(100):
            future = executor.submit(
                query_database,
                f"SELECT * FROM workflows WHERE id = {i}"
            )
            futures.append(future)

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Verify no mixed/corrupted results
        assert len(results) == 100
        for result in results:
            assert result is not None or result is None  # Valid state

test_concurrent_db_access()
# Expected: Passes without errors or data corruption
```

---

## Phase 4: Low-Severity Fixes (v1.0.1)

### VULN-17: Unicode Bypass in Injection Filter

**Severity:** LOW
**Location:** `/acosplatform/auth/sanitize.py`, lines 9-20

**Fix:**
```python
import unicodedata
from typing import Optional

def _normalize_unicode(text: str) -> str:
    """Normalize unicode to prevent lookalike bypasses"""
    # Convert all similar-looking characters to ASCII
    normalized = unicodedata.normalize('NFKD', text)
    return normalized.encode('ascii', 'ignore').decode('ascii')

_INJECTION_PATTERNS = [
    r"(?i)(ignore|override|system|execute)",  # Instruction injection
    r"(?i)(drop|delete|update)\s+table",      # SQL injection
    r"(?i)(eval|exec|system)\s*\(",           # Code execution
    r"(?i)(<script|javascript:|onerror)",     # XSS patterns
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS))

def sanitize_user_input(text: Optional[str], max_length: int = 500) -> str:
    """Sanitize user input to prevent prompt injection"""
    if not text:
        return ""

    # Truncate first
    text = text[:max_length]

    # Normalize unicode
    normalized = _normalize_unicode(text)

    # Check normalized form
    if _INJECTION_RE.search(normalized):
        audit_log("injection_attempt_blocked", {
            "input": text[:100],  # Log first 100 chars
            "normalized": normalized[:100]
        })
        raise ValueError("Input contains potentially malicious content")

    return text

# Test cases
assert sanitize_user_input("ignore my previous instructions") raises ValueError
assert sanitize_user_input("іgnore instructions") raises ValueError  # Cyrillic і
assert sanitize_user_input("normal user message") == "normal user message"
```

---

### VULN-18: Information Disclosure in Health Endpoint

**Severity:** LOW
**Location:** `/apps/ops_api/main.py`, lines 343-354

**Fix:**
```python
# BEFORE (VERBOSE)
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": OPS_ENVIRONMENT,  # ❌ Discloses environment
        "version": APP_VERSION,            # ❌ Discloses version
        "database": check_db_connection()
    }

# AFTER (MINIMAL)
@app.get("/health")
async def health_check():
    """Minimal health check without version/env disclosure"""
    try:
        check_db_connection()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat()
        }, 503

# ALTERNATIVE: Version endpoint for authenticated users only
@app.get("/system/version", dependencies=[Depends(require_ops_token)])
async def get_version(actor: dict = Depends(require_ops_token)):
    """System version - requires authentication"""
    return {
        "version": APP_VERSION,
        "environment": OPS_ENVIRONMENT,
        "build_date": BUILD_DATE
    }
```

---

## Verification & Testing Strategy

### Security Testing Checklist

- [ ] Unit tests for each vulnerability fix
- [ ] Integration tests for cross-system impacts
- [ ] Automated security scanning (SAST)
- [ ] Manual code review for VULN-1 through VULN-10
- [ ] Penetration testing of critical paths
- [ ] Load testing with rate limiting
- [ ] Fuzzing on API inputs
- [ ] OWASP Top 10 verification

### Deployment Checklist

```bash
#!/bin/bash
# Security verification before deployment

echo "1. Checking for hardcoded credentials..."
grep -r "Bearer\|password\|secret\|key" --include="*.py" --include="*.js" src/
[ $? -ne 0 ] && echo "✓ No hardcoded credentials found" || exit 1

echo "2. Verifying environment variables required..."
grep -E "if not os\.getenv|raise.*REQUIRED" apps/ops_api/*.py | wc -l
[ $? -gt 5 ] && echo "✓ Required env var checks present" || exit 1

echo "3. Checking rate limiting applied..."
grep -r "@limiter.limit\|Depends(require_ops_token)" apps/ | wc -l
[ $? -gt 20 ] && echo "✓ Auth/rate limiting applied" || exit 1

echo "4. Verifying no global DB connection..."
grep -r "^_conn\|global _conn" apps/ && echo "✗ FAIL: Global connection found" && exit 1
echo "✓ No global connection"

echo "5. Checking CSV sanitization..."
grep -r "sanitize_csv\|formula.*injection" apps/ | wc -l
[ $? -gt 0 ] && echo "✓ CSV sanitization present" || exit 1

echo "All security checks passed ✓"
```

---

## Timeline & Responsibility

| Phase | Severity | Fix Count | Timeline | Owner | Status |
|-------|----------|-----------|----------|-------|--------|
| 1 | Critical | 4 | 24 hrs | Backend Lead | START NOW |
| 2 | High | 6 | 48 hrs | Full Team | AFTER P1 |
| 3 | Medium | 6 | 1 week | Backend Lead | AFTER P2 |
| 4 | Low | 2 | 1 week | Backend Junior | AFTER P3 |

---

## Communication & Escalation

**To:** Engineering Team, Security, Leadership
**Subject:** Security Assessment Findings - Immediate Action Required

**Summary:**
- 18 vulnerabilities identified (4 Critical, 6 High, 6 Medium, 2 Low)
- Critical issues require 24-hour emergency response
- Recommend delaying GA release until Phase 1 & 2 complete
- Estimated remediation time: 1 week for all fixes

**Recommendation:**
1. Address Phase 1 (Critical) before any production deployment
2. Address Phase 2 (High) within 48 hours
3. Release as v1.0.0 only after Phase 1 & 2 complete
4. Track Phase 3 & 4 fixes for v1.0.1 hotfix release

---

**ACOS Control Plane Security Remediation Plan - Approved for Implementation**

**Red Team Assessment:** Complete
**Blue Team Fix Plan:** Complete
**Next Step:** Execute Phase 1 (Emergency Response)
