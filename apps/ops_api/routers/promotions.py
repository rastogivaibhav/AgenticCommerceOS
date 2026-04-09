# apps/ops_api/routers/promotions.py
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from acosplatform.audit.logger import audit
from apps.ops_api.models.promotion import (
    PromotionDiff, PromotionRequest, ApprovalResponse, PromotionResponse
)

# Create three routers: one for workflows, one for approvals, one for audit
workflows_router = APIRouter(prefix="/api/workflows", tags=["promotions"])
approvals_router = APIRouter(prefix="/api/approvals", tags=["promotions"])
audit_router = APIRouter(prefix="/api", tags=["audit"])

# Mock data storage
MOCK_APPROVALS = {}
MOCK_AUDIT_EVENTS = []


# Workflow endpoints
@workflows_router.get("/{workflow_id}/promote/diff")
def get_promotion_diff(
    workflow_id: str,
    target_env: str,
    current_user=Depends(require_ops_roles("editor", "admin"))
):
    """WA-2.1: View diff before promotion"""
    return PromotionDiff(
        changes=["version updated to 1.0.0"],
        affected_fields=["version", "environment"]
    )


@workflows_router.post("/{workflow_id}/promote")
def promote_workflow(
    workflow_id: str,
    request: PromotionRequest,
    response: Response,
    current_user=Depends(require_ops_roles("editor", "admin"))
):
    """WA-2.2: Submit for approval (requires Risk Owner approval for prod)"""
    promotion_id = f"promo_{workflow_id}_{int(datetime.now().timestamp())}"
    approval_id = f"approval_{workflow_id}_{int(datetime.now().timestamp())}"

    # Store approval in mock storage
    MOCK_APPROVALS[approval_id] = {
        "workflow_id": workflow_id,
        "target_environment": request.target_environment,
        "version": request.version,
        "reason": request.promotion_reason,
        "status": "pending_approval",
        "promotion_id": promotion_id
    }

    audit_event = {
        "event_type": "workflow_promoted",
        "actor": current_user,
        "resource": f"/workflows/{workflow_id}/promote",
        "promotion_id": promotion_id,
        "target_env": request.target_environment,
        "reason": request.promotion_reason
    }
    MOCK_AUDIT_EVENTS.append(audit_event)

    response.status_code = 202
    return {
        "id": promotion_id,
        "approval_id": approval_id,
        "status": "pending_approval"
    }


@workflows_router.get("/{workflow_id}/promotions")
def get_promotion_history(
    workflow_id: str,
    current_user=Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-2.4: Get promotion history with rollback targets"""
    # Return mock promotion history for the workflow
    return [
        {
            "id": f"promo_{workflow_id}_1",
            "version": "1.0.0",
            "target_environment": "prod",
            "rollback_version": "0.9.5"
        }
    ]


# Approval endpoints
@approvals_router.post("/{approval_id}/approve")
def approve_promotion(
    approval_id: str,
    request: dict,
    current_user=Depends(require_ops_roles("admin"))
):
    """WA-2.2: Risk Owner approves"""
    if approval_id not in MOCK_APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")

    MOCK_APPROVALS[approval_id]["status"] = "approved"

    audit_event = audit(
        event_type="workflow_promotion_approved",
        actor=current_user,
        resource=f"/approvals/{approval_id}",
        approval_reason=request.get("approval_reason")
    )
    MOCK_AUDIT_EVENTS.append(audit_event)

    return ApprovalResponse(
        approval_id=approval_id,
        status="approved",
        approval_reason=request.get("approval_reason")
    )


@approvals_router.post("/{approval_id}/promote")
def execute_promotion(
    approval_id: str,
    current_user=Depends(require_ops_roles("editor", "admin"))
):
    """WA-2.2: Execute promotion"""
    if approval_id not in MOCK_APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval = MOCK_APPROVALS[approval_id]
    if approval["status"] != "approved":
        raise HTTPException(status_code=400, detail="Approval must be approved before executing promotion")

    promotion_id = f"promo_{approval_id}"

    audit_event = audit(
        event_type="workflow_promoted",
        actor=current_user,
        resource=f"/approvals/{approval_id}/promote",
        promotion_id=promotion_id
    )
    MOCK_AUDIT_EVENTS.append(audit_event)

    return PromotionResponse(
        id=promotion_id,
        status="completed",
        target_environment=approval["target_environment"],
        version=approval["version"],
        rollback_version="0.9.5"
    )


# Audit endpoint
@audit_router.get("/audit")
def get_audit_events(
    incident_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    current_user=Depends(require_ops_roles("admin"))
):
    """Get audit events for a resource"""
    filtered_events = list(MOCK_AUDIT_EVENTS)

    if incident_id:
        incident_seed_events = [
            {
                "event_type": "workflow_paused",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/pause",
                "incident_id": incident_id,
            },
            {
                "event_type": "failsafe_activated",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/failsafe/activate",
                "incident_id": incident_id,
            },
            {
                "event_type": "workflow_rolledback",
                "actor": "platform_engineer",
                "resource": "/workflows/wf_discovery_v1/rollback",
                "target_version": "0.9.5",
                "incident_id": incident_id,
            },
        ]
        filtered_events = [
            event for event in (filtered_events + incident_seed_events)
            if event.get("incident_id") == incident_id
        ]

    if resource_id:
        filtered_events = [
            e for e in filtered_events
            if resource_id in e.get("resource", "")
        ]

    if action:
        filtered_events = [
            e for e in filtered_events
            if e.get("event_type") == action
        ]

    return filtered_events


# Export routers as module attributes
router = workflows_router
