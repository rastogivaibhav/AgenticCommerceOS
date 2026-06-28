from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["uat-compat"])

_UAT_WORKFLOWS = [
    {"id": "wf_discovery_v1", "name": "Product Discovery", "family": "discovery", "tenant_id": "tenant_uat_pilot_a", "version": "1.0.0", "status": "active", "environment": "stage", "active_version": "1.0.0", "validation_status": "pass"},
    {"id": "wf_post_purchase_v1", "name": "Order Status Agent", "family": "post_purchase", "tenant_id": "tenant_uat_pilot_a", "version": "1.0.0", "status": "active", "environment": "stage", "active_version": "1.0.0", "validation_status": "pass"},
    {"id": "wf_service_guidance_v1", "name": "Service Help Desk", "family": "service_guidance", "tenant_id": "tenant_uat_pilot_b", "version": "1.0.0", "status": "active", "environment": "stage", "active_version": "1.0.0", "validation_status": "pass"},
    {"id": "wf_returns_v1", "name": "Returns Processor", "family": "returns", "tenant_id": "tenant_uat_pilot_b", "version": "1.0.0", "status": "active", "environment": "stage", "active_version": "1.0.0", "validation_status": "pass"},
]
_UAT_RUNS = [
    {"id": "run_failure_001", "workflow_id": "wf_post_purchase_v1", "tenant_id": "tenant_uat_pilot_a", "status": "failed", "steps": [{"step": "validate_order_id", "status": "completed", "duration_ms": 85}, {"step": "lookup_order", "status": "failed", "duration_ms": 150, "error": "order_not_found"}], "policy_decisions": [{"policy": "order_lookup", "verdict": "allow"}]},
    {"id": "run_success_001", "workflow_id": "wf_discovery_v1", "tenant_id": "tenant_uat_pilot_a", "status": "completed", "steps": [{"step": "classify_intent", "status": "completed", "duration_ms": 145}]},
]
_UAT_APPROVALS = [
    {
        "id": "approval_seed_001",
        "status": "pending",
        "tenant_id": "tenant_uat_pilot_a",
        "evidence": {"risk": "medium"},
        "rollback_plan": "Rollback to previous active version",
    }
]
_UAT_AUDIT: list[dict[str, Any]] = []
_UAT_PROMOTIONS = [
    {
        "id": "promotion_seed_001",
        "workflow_id": "wf_discovery_v1",
        "target_environment": "stage",
        "rollback_version": "0.9.5",
        "status": "completed",
    }
]


@router.get("/workflows")
def uat_api_workflows(
    tenant_id: str | None = None,
    family: str | None = None,
    status: str | None = None,
):
    workflows = list(_UAT_WORKFLOWS)
    if tenant_id:
        workflows = [workflow for workflow in workflows if workflow["tenant_id"] == tenant_id]
    if family:
        workflows = [workflow for workflow in workflows if workflow["family"] == family]
    if status:
        workflows = [workflow for workflow in workflows if workflow["status"] == status]
    return {"workflows": workflows}


@router.get("/workflows/{workflow_id}")
def uat_api_workflow(workflow_id: str):
    workflow = next((workflow for workflow in _UAT_WORKFLOWS if workflow["id"] == workflow_id), None)
    if not workflow:
        return JSONResponse(status_code=404, content={"error": "workflow_not_found"})
    return workflow


@router.get("/workflows/{workflow_id}/detail")
def uat_api_workflow_detail(workflow_id: str):
    workflow = next((workflow for workflow in _UAT_WORKFLOWS if workflow["id"] == workflow_id), None)
    if not workflow:
        return JSONResponse(status_code=404, content={"error": "workflow_not_found"})
    return {
        **workflow,
        "last_promotion": _UAT_PROMOTIONS[0],
        "active_version": workflow["version"],
        "validation_status": "pass",
    }


@router.get("/workflows/{workflow_id}/promote/diff")
def uat_api_workflow_promote_diff(workflow_id: str, target_env: str = "prod"):
    return {
        "workflow_id": workflow_id,
        "target_env": target_env,
        "changes": [{"field": "environment", "from": "stage", "to": target_env}],
        "affected_fields": ["environment", "active_version"],
    }


@router.post("/workflows/{workflow_id}/promote")
def uat_api_workflow_promote(workflow_id: str, body: dict[str, Any]):
    target = body.get("target_environment", "stage")
    promotion_id = f"promotion_{uuid4().hex[:8]}"
    if target == "prod":
        approval_id = f"approval_{uuid4().hex[:8]}"
        _UAT_APPROVALS.insert(
            0,
            {
                "id": approval_id,
                "status": "pending",
                "tenant_id": "tenant_uat_pilot_a",
                "workflow_id": workflow_id,
                "target_environment": target,
                "promotion_id": promotion_id,
                "evidence": {"workflow_id": workflow_id},
                "rollback_plan": "Rollback to stage active version",
            },
        )
        return JSONResponse(
            status_code=202,
            content={
                "approval_id": approval_id,
                "status": "pending_approval",
                "promotion_id": promotion_id,
            },
        )

    promotion = {
        "id": promotion_id,
        "promotion_id": promotion_id,
        "workflow_id": workflow_id,
        "target_environment": target,
        "rollback_version": "0.9.5",
        "status": "completed",
    }
    _UAT_PROMOTIONS.insert(0, promotion)
    _UAT_AUDIT.insert(
        0,
        {
            "id": f"audit_{uuid4().hex[:8]}",
            "action": "workflow_promoted",
            "resource_id": workflow_id,
            "promotion_id": promotion_id,
        },
    )
    return promotion


@router.get("/workflows/{workflow_id}/promotions")
def uat_api_workflow_promotions(workflow_id: str):
    return [
        promotion
        for promotion in _UAT_PROMOTIONS
        if promotion.get("workflow_id") == workflow_id
    ] or _UAT_PROMOTIONS


@router.post("/workflows/{workflow_id}/pause")
def uat_api_workflow_pause(workflow_id: str, body: dict[str, Any]):
    incident_id = body.get("incident_id", "incident_123")
    _UAT_AUDIT.insert(
        0,
        {
            "id": f"audit_{uuid4().hex[:8]}",
            "incident_id": incident_id,
            "action": "workflow_paused",
            "workflow_id": workflow_id,
        },
    )
    return {"status": "paused", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/failsafe/activate")
def uat_api_workflow_failsafe(workflow_id: str, body: dict[str, Any]):
    incident_id = body.get("incident_id", "incident_123")
    _UAT_AUDIT.insert(
        0,
        {
            "id": f"audit_{uuid4().hex[:8]}",
            "incident_id": incident_id,
            "action": "failsafe_activated",
            "workflow_id": workflow_id,
        },
    )
    return {"status": "active", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/rollback")
def uat_api_workflow_rollback(workflow_id: str, body: dict[str, Any]):
    incident_id = body.get("incident_id", "incident_123")
    target_version = body.get("target_version", "0.9.5")
    _UAT_AUDIT.insert(
        0,
        {
            "id": f"audit_{uuid4().hex[:8]}",
            "incident_id": incident_id,
            "action": "workflow_rollback",
            "workflow_id": workflow_id,
            "target_version": target_version,
        },
    )
    return {"status": "rolling_back", "workflow_id": workflow_id, "target_version": target_version}


@router.get("/runs")
def uat_api_runs(
    tenant_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
):
    runs = list(_UAT_RUNS)
    if tenant_id:
        runs = [run for run in runs if run["tenant_id"] == tenant_id]
    if status:
        runs = [run for run in runs if run["status"] == status]
    return {"runs": runs[:limit]}


@router.get("/runs/{run_id}/timeline")
def uat_api_run_timeline(run_id: str, include_policy: bool = False):
    run = next((item for item in _UAT_RUNS if item["id"] == run_id), _UAT_RUNS[0])
    payload = {"run_id": run_id, "steps": run.get("steps", [])}
    if include_policy:
        payload["policy_decisions"] = run.get("policy_decisions", [])
    return payload


@router.post("/runs/{run_id}/replay")
def uat_api_run_replay(run_id: str, body: dict[str, Any]):
    return JSONResponse(
        status_code=202,
        content={
            "status": "replaying",
            "run_id": run_id,
            "replay_id": f"replay_{uuid4().hex[:8]}",
        },
    )


@router.post("/runs/{run_id}/escalate")
def uat_api_run_escalate(run_id: str, body: dict[str, Any]):
    return {"status": "escalated", "run_id": run_id, "assigned_to": body.get("assigned_to")}


@router.get("/approvals")
def uat_api_approvals(
    status: str | None = None,
    tenant_id: str | None = None,
    limit: int = 20,
):
    approvals = list(_UAT_APPROVALS)
    if status:
        approvals = [approval for approval in approvals if approval["status"] == status]
    if tenant_id:
        approvals = [approval for approval in approvals if approval.get("tenant_id") == tenant_id]
    return {"approvals": approvals[:limit]}


@router.get("/approvals/{approval_id}")
def uat_api_approval(approval_id: str):
    approval = next((item for item in _UAT_APPROVALS if item["id"] == approval_id), None)
    if not approval:
        return JSONResponse(status_code=404, content={"error": "approval_not_found"})
    return approval


@router.post("/approvals/{approval_id}/approve")
def uat_api_approval_approve(approval_id: str, body: dict[str, Any]):
    approval = next((item for item in _UAT_APPROVALS if item["id"] == approval_id), None)
    if approval:
        approval["status"] = "approved"
    return {"id": approval_id, "status": "approved"}


@router.post("/approvals/{approval_id}/promote")
def uat_api_approval_promote(approval_id: str):
    approval = next((item for item in _UAT_APPROVALS if item["id"] == approval_id), {})
    target = approval.get("target_environment", "prod")
    promotion_id = approval.get("promotion_id", f"promotion_{uuid4().hex[:8]}")
    _UAT_PROMOTIONS.insert(
        0,
        {
            "id": promotion_id,
            "workflow_id": approval.get("workflow_id", "wf_discovery_v1"),
            "target_environment": target,
            "rollback_version": "0.9.5",
            "status": "completed",
        },
    )
    return {"id": promotion_id, "status": "completed", "target_environment": target}


@router.get("/audit")
def uat_api_audit(
    resource_id: str | None = None,
    action: str | None = None,
    incident_id: str | None = None,
):
    events = list(_UAT_AUDIT)
    if incident_id and not events:
        events = [{"id": "audit_incident_seed", "incident_id": incident_id, "action": "workflow_paused"}]
    if resource_id:
        events = [
            event
            for event in events
            if event.get("resource_id") == resource_id or event.get("workflow_id") == resource_id
        ]
    if action:
        events = [event for event in events if event.get("action") == action]
    if incident_id:
        events = [event for event in events if event.get("incident_id") == incident_id]
    return events


@router.get("/health/workflows/{workflow_id}")
def uat_api_workflow_health(workflow_id: str, window: str = "5m"):
    return {
        "workflow_id": workflow_id,
        "window": window,
        "error_rate": 0.01,
        "p99_latency": 420,
        "throughput": 84,
    }
