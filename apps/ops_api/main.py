"""Ops API for ACOS control-plane operations."""

import logging
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from acosplatform.auth.api_key import require_ops_token
from acosplatform.billing.engine import get_cost_summary, get_usage
from acosplatform.db.connection import ensure_schema, get_connection
from acosplatform.db.repository import get_events, get_run, get_runs, get_runs_by_workflow
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
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


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


@app.get("/workflows")
def list_workflows(
    tenant_id: str = None,
    environment: str = OPS_ENVIRONMENT,
    _token: dict = Depends(require_ops_token),
):
    return {
        "environment": environment,
        "workflows": list_workflows_with_state(tenant_id=tenant_id, environment=environment),
    }


@app.get("/workflows/{workflow_id}")
def workflow_detail(
    workflow_id: str,
    environment: str = OPS_ENVIRONMENT,
    _token: dict = Depends(require_ops_token),
):
    detail = get_workflow_detail(workflow_id, environment=environment)
    if not detail:
        return JSONResponse(status_code=404, content={"error": "Workflow not found"})
    return detail


@app.get("/workflows/{workflow_id}/runs")
def workflow_runs(
    workflow_id: str,
    limit: int = 100,
    _token: dict = Depends(require_ops_token),
):
    if limit > 500:
        limit = 500
    return {"runs": get_runs_by_workflow(workflow_id, limit=limit)}


@app.post("/workflows")
def workflow_create(
    payload: WorkflowCreateRequest,
    token: dict = Depends(require_ops_token),
):
    try:
        return create_workflow_draft(payload, actor=_actor(token), environment=OPS_ENVIRONMENT)
    except ValueError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


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
