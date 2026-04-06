"""Ops API for ACOS control-plane operations."""

import json
import logging
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi.errors import RateLimitExceeded

from acosplatform.audit.logger import audit
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.config.startup_validation import validate_auth_configuration
from acosplatform.billing.engine import get_cost_summary, get_usage
from acosplatform.db.connection import ensure_schema, check_connection
from acosplatform.db.repository import (
    get_events,
    get_orders_for_customer,
    get_product_by_id,
    get_products,
    get_run,
    get_runs,
    get_runs_by_workflow,
    get_agents,
    get_skills,
    save_audit_event,
)
from acosplatform.evaluation.scorer import get_experiment_results
from acosplatform.middleware.rate_limit import REPLAY_LIMIT, limiter, rate_limit_error_handler
from acosplatform.models.workflows import (
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowPromotionRequest,
    WorkflowRollbackRequest,
    WorkflowVersionCreateRequest,
)
from acosplatform.observability.metrics import metrics_endpoint, record_api_error
from acosplatform.replay.replay_engine import replay
from acosplatform.workflows.service import (
    approve_workflow_version,
    archive_workflow,
    create_workflow_draft,
    create_workflow_version,
    ensure_default_workflow_registry,
    get_workflow_detail,
    list_workflows_with_state,
    promote_workflow_version,
    rollback_workflow_version,
)
from apps.ops_api.routers import experiments, analytics, workflows, promotions, runs, approvals, incidents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
OPS_ENVIRONMENT = os.environ.get("OPS_ENVIRONMENT", "dev")
EMBEDDED_UI_DIR = Path("apps/ops_api/ui")
LOCAL_UI_DIR = Path("apps/ops_ui_v2/dist")
UI_DIR = EMBEDDED_UI_DIR if (EMBEDDED_UI_DIR / "index.html").exists() else LOCAL_UI_DIR

app = FastAPI(
    title="ACOS Ops API",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
app.mount("/ui", StaticFiles(directory=UI_DIR, html=True, check_dir=False), name="ui")

_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(experiments.router)
app.include_router(analytics.router)
app.include_router(workflows.router)
app.include_router(promotions.router)
app.include_router(promotions.approvals_router)
app.include_router(promotions.audit_router)
app.include_router(runs.router)
app.include_router(approvals.router)
app.include_router(incidents.router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    record_api_error(exc.__class__.__name__, request.url.path)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.on_event("startup")
def startup():
    logger.info("Ops API starting up...")
    validate_auth_configuration(service="ops-api", environment=OPS_ENVIRONMENT)
    ensure_schema()
    ensure_default_workflow_registry(environment=OPS_ENVIRONMENT)
    logger.info("Ops API ready")


def _actor(token: dict) -> str:
    return token.get("sub") or token.get("email") or "ops-user"


READ_ACCESS = require_ops_roles("admin", "ops", "analyst")
OPERATE_ACCESS = require_ops_roles("admin", "ops")
ADMIN_ACCESS = require_ops_roles("admin")


class CanvasSaveRequest(BaseModel):
    step_definitions: dict


@app.get("/runs")
def list_runs(
    tenant_id: str = None,
    limit: int = 100,
    _claims: dict = Depends(READ_ACCESS),
):
    if limit > 1000:
        limit = 1000
    return {"runs": get_runs(tenant_id=tenant_id, limit=limit)}


@app.get("/runs/{run_id}")
def get_run_detail(
    run_id: str,
    _claims: dict = Depends(READ_ACCESS),
):
    run = get_run(run_id)
    if not run:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"run": run, "events": get_events(run_id)}


@app.post("/replay/{run_id}")
@app.post("/v1/replay/{run_id}")
@limiter.limit(REPLAY_LIMIT)
def replay_run(
    request: Request,
    run_id: str,
    _claims: dict = Depends(OPERATE_ACCESS),
):
    return replay(run_id)


@app.get("/products")
def list_products(request: Request, _claims: dict = Depends(READ_ACCESS)):
    category = request.query_params.get("category")
    return {"products": get_products(category=category)}


@app.get("/products/{product_id}")
def get_product(product_id: str, _claims: dict = Depends(READ_ACCESS)):
    product = get_product_by_id(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return product


@app.get("/orders/{customer_id}")
def list_orders(customer_id: str, _claims: dict = Depends(READ_ACCESS)):
    return {"orders": get_orders_for_customer(customer_id)}


@app.get("/dashboard")
def dashboard(_claims: dict = Depends(READ_ACCESS)):
    from acosplatform.db.repository import get_dashboard

    return {
        "metrics": get_dashboard(),
        "billing": get_cost_summary(),
        "experiments": get_experiment_results(),
    }


@app.get("/billing")
def billing(tenant_id: str = None, _claims: dict = Depends(READ_ACCESS)):
    if tenant_id:
        return {"usage": get_usage(tenant_id)}
    return {"summary": get_cost_summary(), "by_tenant": get_usage()}


@app.get("/api/v1/agents")
@app.get("/agents")
def list_agents(_claims: dict = Depends(READ_ACCESS)):
    return {"agents": get_agents()}


@app.post("/api/v1/agents")
@app.post("/agents")
def create_agent(agent: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    from acosplatform.db.repository import save_agent
    save_agent(agent)
    return {"status": "success", "agent": agent}


@app.patch("/api/v1/agents/{agent_id}")
@app.patch("/agents/{agent_id}")
def update_agent(agent_id: str, updates: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    from acosplatform.db.repository import get_agents, save_agent
    agents = get_agents()
    target = next((a for a in agents if a.get("id") == agent_id), None)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Agent not found"})
    target.update(updates)
    save_agent(target)
    return {"status": "success", "agent": target}


@app.get("/api/v1/skills")
@app.get("/skills")
def list_skills(_claims: dict = Depends(READ_ACCESS)):
    return {"skills": get_skills()}


@app.post("/api/v1/skills")
@app.post("/skills")
def create_skill(skill: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    from acosplatform.db.repository import save_skill
    save_skill(skill)
    return {"status": "success", "skill": skill}


@app.patch("/api/v1/skills/{skill_id}")
@app.patch("/skills/{skill_id}")
def update_skill(skill_id: str, updates: dict, _claims: dict = Depends(OPERATE_ACCESS)):
    from acosplatform.db.repository import get_skills, save_skill
    skills = get_skills()
    target = next((s for s in skills if s.get("id") == skill_id), None)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Skill not found"})
    target.update(updates)
    save_skill(target)
    return {"status": "success", "skill": target}


@app.get("/api/v1/tenants")
@app.get("/tenants")
def list_tenants_endpoint(_claims: dict = Depends(READ_ACCESS)):
    from acosplatform.tenancy.manager import list_tenants
    return {"tenants": list_tenants()}


@app.post("/api/v1/tenants")
@app.post("/tenants")
def create_tenant(tenant: dict, token: dict = Depends(ADMIN_ACCESS)):
    from acosplatform.tenancy.manager import add_tenant
    try:
        record = add_tenant(tenant["id"], {k: v for k, v in tenant.items() if k != "id"})
    except (ValueError, KeyError) as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})
    actor = _actor(token)
    audit("tenant.created", actor=actor, resource=f"/tenants/{record['id']}")
    save_audit_event(actor, "tenant.created", "tenant", record["id"], payload=record)
    return {"status": "success", "tenant": record}


@app.patch("/api/v1/tenants/{tenant_id}")
@app.patch("/tenants/{tenant_id}")
def update_tenant_endpoint(tenant_id: str, updates: dict, token: dict = Depends(ADMIN_ACCESS)):
    from acosplatform.tenancy.manager import update_tenant
    record = update_tenant(tenant_id, updates)
    actor = _actor(token)
    audit("tenant.updated", actor=actor, resource=f"/tenants/{tenant_id}")
    save_audit_event(actor, "tenant.updated", "tenant", tenant_id, payload=updates)
    return {"status": "success", "tenant": record}


@app.get("/api/v1/workflows")
@app.get("/workflows")
def list_workflows(
    tenant_id: str = None,
    environment: str = OPS_ENVIRONMENT,
    _claims: dict = Depends(READ_ACCESS),
):
    return {
        "environment": environment,
        "workflows": list_workflows_with_state(tenant_id=tenant_id, environment=environment),
    }


@app.get("/api/v1/workflows/{workflow_id}")
@app.get("/workflows/{workflow_id}")
def workflow_detail(
    workflow_id: str,
    environment: str = OPS_ENVIRONMENT,
    _claims: dict = Depends(READ_ACCESS),
):
    detail = get_workflow_detail(workflow_id, environment=environment)
    if not detail:
        return JSONResponse(status_code=404, content={"error": "Workflow not found"})
    return detail


@app.patch("/api/v1/workflows/{workflow_id}")
@app.patch("/workflows/{workflow_id}")
def workflow_update(
    workflow_id: str,
    payload: CanvasSaveRequest,
    token: dict = Depends(OPERATE_ACCESS),
    environment: str = OPS_ENVIRONMENT,
):
    version_payload = WorkflowVersionCreateRequest(
        change_summary="Canvas save",
        validation_status="draft",
        step_definitions=[payload.step_definitions],
    )
    try:
        version = create_workflow_version(
            workflow_id=workflow_id,
            payload=version_payload,
            actor=_actor(token),
            environment=environment,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    return {"version": version}


@app.get("/api/v1/workflows/{workflow_id}/runs")
@app.get("/workflows/{workflow_id}/runs")
def workflow_runs(
    workflow_id: str,
    limit: int = 100,
    _claims: dict = Depends(READ_ACCESS),
):
    if limit > 500:
        limit = 500
    return {"runs": get_runs_by_workflow(workflow_id, limit=limit)}


@app.post("/api/v1/workflows")
@app.post("/workflows")
def workflow_create(
    payload: WorkflowCreateRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return create_workflow_draft(payload, actor=_actor(token), environment=OPS_ENVIRONMENT)
    except ValueError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions")
@app.post("/workflows/{workflow_id}/versions")
def workflow_version_create(
    workflow_id: str,
    payload: WorkflowVersionCreateRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return create_workflow_version(
            workflow_id=workflow_id,
            payload=payload,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions/{version}/approve")
@app.post("/workflows/{workflow_id}/versions/{version}/approve")
def workflow_version_approve(
    workflow_id: str,
    version: str,
    payload: WorkflowApprovalRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return approve_workflow_version(
            workflow_id=workflow_id,
            version=version,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
            approval_note=payload.approval_note,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/versions/{version}/promote")
@app.post("/workflows/{workflow_id}/versions/{version}/promote")
def workflow_version_promote(
    workflow_id: str,
    version: str,
    payload: WorkflowPromotionRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return promote_workflow_version(
            workflow_id=workflow_id,
            version=version,
            target_environment=payload.target_environment,
            actor=_actor(token),
            approval_note=payload.approval_note,
            source_environment=payload.source_environment,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    except RuntimeError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.post("/api/v1/workflows/{workflow_id}/rollback")
@app.post("/workflows/{workflow_id}/rollback")
def workflow_rollback(
    workflow_id: str,
    payload: WorkflowRollbackRequest,
    token: dict = Depends(OPERATE_ACCESS),
):
    try:
        return rollback_workflow_version(
            workflow_id=workflow_id,
            target_environment=payload.target_environment,
            actor=_actor(token),
            to_version=payload.to_version,
            reason=payload.reason,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})
    except RuntimeError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.delete("/api/v1/workflows/{workflow_id}")
@app.delete("/workflows/{workflow_id}")
def workflow_delete(
    workflow_id: str,
    token: dict = Depends(OPERATE_ACCESS),
    reason: str = "",
):
    try:
        return archive_workflow(
            workflow_id=workflow_id,
            actor=_actor(token),
            environment=OPS_ENVIRONMENT,
            reason=reason,
        )
    except ValueError as exc:
        return JSONResponse(status_code=404, content={"error": str(exc)})


@app.get("/analytics/export")
def export_analytics(
    format: str = "csv",
    _claims: dict = Depends(READ_ACCESS),
):
    """Export analytics data in CSV or JSON format."""
    import csv
    import io
    from datetime import datetime

    if format not in ["csv", "json"]:
        return JSONResponse(status_code=400, content={"error": "Invalid format. Use 'csv' or 'json'"})

    runs = get_runs(limit=10000)

    if format == "csv":
        output = io.StringIO()
        if runs:
            writer = csv.DictWriter(
                output,
                fieldnames=['id', 'journey', 'score', 'cost', 'created_at']
            )
            writer.writeheader()
            for run in runs:
                writer.writerow({
                    'id': run.get('id', ''),
                    'journey': run.get('journey', ''),
                    'score': run.get('score', 0),
                    'cost': run.get('cost', 0),
                    'created_at': run.get('created_at', ''),
                })
        return {
            "content": output.getvalue(),
            "filename": f"analytics-{datetime.now().strftime('%Y-%m-%d')}.csv"
        }

    return {
        "content": runs,
        "filename": f"analytics-{datetime.now().strftime('%Y-%m-%d')}.json"
    }


@app.get("/loyalty/{customer_id}")
def get_loyalty(customer_id: str, _claims: dict = Depends(READ_ACCESS)):
    from acosplatform.plugins.loyalty import get_status
    return get_status(customer_id)


@app.get("/metrics")
def ops_metrics(_claims: dict = Depends(READ_ACCESS)):
    return metrics_endpoint()


@app.get("/health")
def health():
    db_ok = check_connection()
    ui_ready = (UI_DIR / "index.html").exists()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
        "ui": "built" if ui_ready else "missing",
        "service": "ops-api",
        "environment": OPS_ENVIRONMENT,
        "version": APP_VERSION,
    }


@app.get("/dev/auth/bootstrap", response_class=HTMLResponse)
def dev_auth_bootstrap(token: str, redirect: str = "/ui/agents"):
    """Dev-only helper: writes ops token into browser localStorage and redirects."""
    env = OPS_ENVIRONMENT.strip().lower()
    if env not in {"dev", "development", "local", "test", "testing"}:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    safe_redirect = redirect if redirect.startswith("/ui/") else "/ui/"
    token_json = json.dumps(token)
    redirect_json = json.dumps(safe_redirect)

    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>ACOS Dev Auth Bootstrap</title>
          <style>
            body {{
              font-family: Segoe UI, Arial, sans-serif;
              background: #0b1220;
              color: #e5e7eb;
              display: grid;
              place-items: center;
              min-height: 100vh;
              margin: 0;
            }}
            .card {{
              border: 1px solid #334155;
              background: #111827;
              border-radius: 12px;
              padding: 20px;
              max-width: 540px;
              width: calc(100% - 32px);
            }}
            code {{
              background: #1f2937;
              padding: 2px 6px;
              border-radius: 6px;
            }}
          </style>
        </head>
        <body>
          <div class="card">
            <h1>Switching Role Token...</h1>
            <p>Setting <code>ops_token</code> and redirecting to UI.</p>
          </div>
          <script>
            localStorage.setItem("ops_token", {token_json});
            window.location.replace({redirect_json});
          </script>
        </body>
        </html>
        """
    )


@app.get("/", response_class=HTMLResponse)
def serve_ui_root():
    if (UI_DIR / "index.html").exists():
        return RedirectResponse(url="/ui/", status_code=307)
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>ACOS Control Plane</title>
          <style>
            body { font-family: Segoe UI, Arial, sans-serif; padding: 40px; background: #f6f7fb; color: #1f2937; }
            .card { max-width: 720px; margin: 40px auto; background: white; border: 1px solid #d8dee9; border-radius: 16px; padding: 24px; }
            h1 { margin-top: 0; }
            code { background: #eef2ff; padding: 2px 6px; border-radius: 6px; }
          </style>
        </head>
        <body>
          <div class="card">
            <h1>ACOS Control Plane</h1>
            <p>The React UI has not been built yet.</p>
            <p>Build it from <code>apps/ops_ui_v2</code> and refresh this page.</p>
          </div>
        </body>
        </html>
        """
    )
