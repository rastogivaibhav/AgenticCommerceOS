"""Ops API for ACOS control-plane operations."""

import logging
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from acosplatform.auth.api_key import require_ops_token
from acosplatform.billing.engine import get_cost_summary, get_usage
from acosplatform.db.connection import ensure_schema, get_connection
from acosplatform.db.repository import (
    get_events,
    get_run,
    get_runs,
    get_runs_by_workflow,
    get_agents,
    get_skills,
    get_graph_runs,
    get_workflow_versions,
    save_graph_run,
)
from acosplatform.temporal.client import get_run_status, start_graph_run
from pydantic import BaseModel
from acosplatform.evaluation.scorer import get_experiment_results
from acosplatform.middleware.rate_limit import REPLAY_LIMIT, limiter, rate_limit_error_handler
from acosplatform.models.workflows import (
    WorkflowCreateRequest,
    WorkflowPromotionRequest,
    WorkflowVersionCreateRequest,
)
from acosplatform.observability.metrics import metrics_endpoint
from acosplatform.replay.replay_engine import replay
from acosplatform.workflows.service import (
    create_workflow_draft,
    create_workflow_version,
    ensure_default_workflow_registry,
    get_workflow_detail,
    list_workflows_with_state,
    promote_workflow_version,
)
from apps.ops_api.routers import workflows, experiments, analytics

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
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(workflows.router)
app.include_router(experiments.router)
app.include_router(analytics.router)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.on_event("startup")
def startup():
    logger.info("Ops API starting up...")
    ensure_schema()
    ensure_default_workflow_registry(environment=OPS_ENVIRONMENT)
    logger.info("Ops API ready")


def _actor(token: dict) -> str:
    return token.get("sub") or token.get("email") or "ops-user"


@app.get("/runs")
def list_runs(
    tenant_id: str = None,
    limit: int = 100,
    _token: dict = Depends(require_ops_token),
):
    if limit > 1000:
        limit = 1000
    return {"runs": get_runs(tenant_id=tenant_id, limit=limit)}


@app.get("/runs/{run_id}")
def get_run_detail(
    run_id: str,
    _token: dict = Depends(require_ops_token),
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
    _token: dict = Depends(require_ops_token),
):
    return replay(run_id)


@app.get("/dashboard")
def dashboard(_token: dict = Depends(require_ops_token)):
    from acosplatform.db.repository import get_dashboard

    return {
        "metrics": get_dashboard(),
        "billing": get_cost_summary(),
        "experiments": get_experiment_results(),
    }


@app.get("/billing")
def billing(tenant_id: str = None, _token: dict = Depends(require_ops_token)):
    if tenant_id:
        return {"usage": get_usage(tenant_id)}
    return {"summary": get_cost_summary(), "by_tenant": get_usage()}


@app.get("/api/v1/agents")
@app.get("/agents")
def list_agents():
    return {"agents": get_agents()}


@app.post("/api/v1/agents")
@app.post("/agents")
def create_agent(agent: dict):
    from acosplatform.db.repository import save_agent
    save_agent(agent)
    return {"status": "success", "agent": agent}


@app.patch("/api/v1/agents/{agent_id}")
@app.patch("/agents/{agent_id}")
def update_agent(agent_id: str, updates: dict):
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
def list_skills():
    return {"skills": get_skills()}


@app.post("/api/v1/skills")
@app.post("/skills")
def create_skill(skill: dict):
    from acosplatform.db.repository import save_skill
    save_skill(skill)
    return {"status": "success", "skill": skill}


@app.patch("/api/v1/skills/{skill_id}")
@app.patch("/skills/{skill_id}")
def update_skill(skill_id: str, updates: dict):
    from acosplatform.db.repository import get_skills, save_skill
    skills = get_skills()
    target = next((s for s in skills if s.get("id") == skill_id), None)
    if not target:
        return JSONResponse(status_code=404, content={"error": "Skill not found"})
    target.update(updates)
    save_skill(target)
    return {"status": "success", "skill": target}


@app.get("/api/v1/workflows")
@app.get("/workflows")
def list_workflows(
    tenant_id: str = None,
    environment: str = OPS_ENVIRONMENT,
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
):
    detail = get_workflow_detail(workflow_id, environment=environment)
    if not detail:
        return JSONResponse(status_code=404, content={"error": "Workflow not found"})
    return detail


@app.get("/api/v1/workflows/{workflow_id}/runs")
@app.get("/workflows/{workflow_id}/runs")
def workflow_runs(
    workflow_id: str,
    limit: int = 100,
    _token: dict = Depends(require_ops_token),
):
    if limit > 500:
        limit = 500
    return {"runs": get_runs_by_workflow(workflow_id, limit=limit)}


@app.post("/api/v1/workflows")
@app.post("/workflows")
def workflow_create(
    payload: WorkflowCreateRequest,
    token: dict = Depends(require_ops_token),
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
    token: dict = Depends(require_ops_token),
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


@app.post("/api/v1/workflows/{workflow_id}/versions/{version}/promote")
@app.post("/workflows/{workflow_id}/versions/{version}/promote")
def workflow_version_promote(
    workflow_id: str,
    version: str,
    payload: WorkflowPromotionRequest,
    token: dict = Depends(require_ops_token),
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


@app.get("/analytics/export")
def export_analytics(
    format: str = "csv",
    _token: dict = Depends(require_ops_token),
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


@app.get("/metrics")
def ops_metrics():
    return metrics_endpoint()


@app.get("/health")
def health():
    db_ok = get_connection() is not None
    ui_ready = (UI_DIR / "index.html").exists()
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
        "ui": "built" if ui_ready else "missing",
        "service": "ops-api",
        "environment": OPS_ENVIRONMENT,
        "version": APP_VERSION,
    }


class WorkflowRunRequest(BaseModel):
    ctx: dict = {}
    tenant_id: str = "default"


@app.post("/workflows/{workflow_id}/run", dependencies=[Depends(require_ops_token)])
async def trigger_workflow_run(workflow_id: str, body: WorkflowRunRequest):
    versions = get_workflow_versions(workflow_id)
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found")
    latest = sorted(versions, key=lambda v: v.get("created_at", ""))[-1]
    graph  = latest.get("step_definitions") or {}
    if not graph.get("nodes"):
        raise HTTPException(
            status_code=422,
            detail="No canvas graph saved — open the editor and click Save Workflow first."
        )
    run_meta = await start_graph_run(
        workflow_id=workflow_id,
        graph=graph,
        ctx={"tenant_id": body.tenant_id, **body.ctx},
    )
    save_graph_run(
        run_id=run_meta["run_id"], workflow_id=workflow_id,
        tenant_id=body.tenant_id, graph=graph, ctx=body.ctx,
    )
    return run_meta


@app.get("/workflows/{workflow_id}/runs", dependencies=[Depends(require_ops_token)])
async def list_workflow_runs(workflow_id: str, limit: int = 20):
    return {"runs": get_graph_runs(workflow_id, limit=limit)}


@app.get("/workflows/runs/{run_id}/status", dependencies=[Depends(require_ops_token)])
async def poll_run_status(run_id: str):
    return await get_run_status(run_id)


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
