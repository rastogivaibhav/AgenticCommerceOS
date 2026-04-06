# apps/ops_api/routers/approvals.py
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from acosplatform.auth.api_key import require_ops_roles
from apps.ops_api.models.approval import ApprovalQueueResponse, ApprovalDetail, ApprovalQueueItem

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

# Mock data
MOCK_APPROVALS = {
    "approval_wf_discovery_v1_1": ApprovalQueueItem(
        id="approval_wf_discovery_v1_1",
        workflow_id="wf_discovery_v1",
        tenant_id="tenant_uat_pilot_a",
        status="pending",
        request_type="workflow_promotion"
    )
}


@router.get("", response_model=ApprovalQueueResponse)
def get_approval_queue(
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    current_user=Depends(require_ops_roles("admin"))
):
    """RO-4.1: Risk Owner view approval queue"""
    filtered = list(MOCK_APPROVALS.values())

    if status:
        filtered = [a for a in filtered if a.status == status]

    if tenant_id:
        filtered = [a for a in filtered if a.tenant_id == tenant_id]

    return ApprovalQueueResponse(approvals=filtered)


@router.get("/{approval_id}")
def get_approval_detail(
    approval_id: str,
    current_user=Depends(require_ops_roles("admin"))
):
    """RO-4.2: Risk Owner review approval evidence"""
    if approval_id not in MOCK_APPROVALS:
        raise HTTPException(status_code=404, detail="Approval not found")

    return ApprovalDetail(
        id=approval_id,
        status="pending",
        evidence={"changes": [], "risk_level": "medium"},
        rollback_plan={"strategy": "revert_version", "target": "1.0.0"}
    )
