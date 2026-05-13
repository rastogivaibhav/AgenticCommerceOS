# apps/ops_api/routers/runs.py
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.audit.logger import audit
from apps.ops_api.models.run import RunListResponse, RunTimeline, RunStep, RunListItem

router = APIRouter(prefix="/api/runs", tags=["runs"])

# Mock data
MOCK_CREATED_AT = datetime(2026, 3, 1, 10, 0, 0)
MOCK_RUNS = [
    RunListItem(
        id="run_failure_001",
        workflow_id="wf_post_purchase_v1",
        tenant_id="tenant_uat_pilot_a",
        status="failed",
        started_at=MOCK_CREATED_AT
    )
]


@router.get("", response_model=RunListResponse)
def list_runs(
    tenant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10),
    current_user=Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """OL-3.1: List failed runs with filters"""
    filtered_runs = MOCK_RUNS

    if tenant_id:
        filtered_runs = [r for r in filtered_runs if r.tenant_id == tenant_id]

    if status:
        filtered_runs = [r for r in filtered_runs if r.status == status]

    return RunListResponse(runs=filtered_runs[:limit])


@router.get("/{run_id}/timeline")
def get_run_timeline(
    run_id: str,
    include_policy: bool = Query(False),
    current_user=Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """OL-3.2: Get run timeline with step details"""
    # Find the run or return mock data
    run = next((r for r in MOCK_RUNS if r.id == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunTimeline(
        id=run_id,
        workflow_id=run.workflow_id,
        status=run.status,
        started_at=run.started_at,
        ended_at=MOCK_CREATED_AT,
        steps=[
            RunStep(step="validate_order_id", status="completed", duration_ms=85),
            RunStep(step="lookup_order", status="failed", duration_ms=150, error="order_not_found")
        ],
        policy_decisions=[] if include_policy else None
    )


@router.post("/{run_id}/replay", status_code=202)
def replay_run(
    run_id: str,
    request: dict = {},
    current_user=Depends(require_ops_roles("editor", "admin"))
):
    """OL-3.4: Trigger replay of failed run"""
    # Verify run exists
    run = next((r for r in MOCK_RUNS if r.id == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    replay_id = f"replay_{run_id}_{int(datetime.now().timestamp())}"

    audit_event = {
        "event_type": "run_replayed",
        "actor": current_user,
        "resource": f"/runs/{run_id}/replay",
        "replay_id": replay_id
    }

    return {
        "replay_id": replay_id,
        "status": "replaying",
        "original_run_id": run_id
    }


@router.post("/{run_id}/escalate")
def escalate_run(
    run_id: str,
    request: dict = {},
    current_user=Depends(require_ops_roles("editor", "admin"))
):
    """OL-3.5: Escalate run to human handling"""
    # Verify run exists
    run = next((r for r in MOCK_RUNS if r.id == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    audit_event = {
        "event_type": "run_escalated",
        "actor": current_user,
        "resource": f"/runs/{run_id}/escalate",
        "assigned_to": request.get("assigned_to")
    }

    return {
        "status": "escalated",
        "run_id": run_id,
        "assigned_to": request.get("assigned_to")
    }
