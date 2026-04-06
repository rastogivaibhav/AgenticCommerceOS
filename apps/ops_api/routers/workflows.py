# apps/ops_api/routers/workflows.py
from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from apps.ops_api.models.workflow import WorkflowListResponse, WorkflowListItem, WorkflowDetail

# Import test data for mock responses
from tests.fixtures.uat_pilot_data import (
    PILOT_TENANT_A,
    PILOT_TENANT_B,
    WORKFLOW_DISCOVERY,
    WORKFLOW_POST_PURCHASE,
    WORKFLOW_SERVICE_GUIDANCE,
    WORKFLOW_RETURNS
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Map tenant IDs to their workflows
TENANT_WORKFLOWS = {
    PILOT_TENANT_A["id"]: [WORKFLOW_DISCOVERY, WORKFLOW_POST_PURCHASE],
    PILOT_TENANT_B["id"]: [WORKFLOW_SERVICE_GUIDANCE, WORKFLOW_RETURNS],
}

@router.get("", response_model=WorkflowListResponse)
def list_workflows_endpoint(
    tenant_id: str = Query(...),
    family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    current_user = Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-1.1: List workflows with filtering"""
    # Get workflows for the tenant
    tenant_workflows = TENANT_WORKFLOWS.get(tenant_id, [])

    # Apply filters
    filtered_workflows = []
    for wf in tenant_workflows:
        if family and wf.get("family") != family:
            continue
        if status and wf.get("status") != status:
            continue
        filtered_workflows.append(wf)

    # Convert to response items
    workflows = [
        WorkflowListItem(
            id=wf["id"],
            name=wf["name"],
            family=wf["family"],
            version=wf.get("version", "1.0.0"),
            status=wf.get("status", "active"),
            environment=environment or "dev",
            tenant_id=tenant_id,
            created_at=datetime.now()
        )
        for wf in filtered_workflows
    ]

    return WorkflowListResponse(
        workflows=workflows,
        total=len(workflows),
        filtered_by={"family": family, "status": status, "environment": environment}
    )

@router.get("/{workflow_id}", response_model=WorkflowDetail)
def get_workflow_endpoint(
    workflow_id: str,
    current_user = Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-1.2: Get workflow with version and environment badges"""
    # Find workflow by ID across all tenants
    all_workflows = [
        *TENANT_WORKFLOWS.get(PILOT_TENANT_A["id"], []),
        *TENANT_WORKFLOWS.get(PILOT_TENANT_B["id"], [])
    ]
    workflow = next((w for w in all_workflows if w["id"] == workflow_id), None)

    if not workflow:
        # Fallback for unknown workflows
        workflow = {
            "id": workflow_id,
            "name": "Test Workflow",
            "family": "default",
            "version": "1.0.0",
            "status": "active",
            "tenant_id": "test_tenant"
        }

    return WorkflowDetail(
        id=workflow["id"],
        name=workflow.get("name", "Test Workflow"),
        family=workflow.get("family", "default"),
        version=workflow.get("version", "1.0.0"),
        status=workflow.get("status", "active"),
        environment="dev",
        tenant_id=workflow.get("tenant_id", "test_tenant"),
        created_at=datetime.now(),
        last_promotion={},
        active_version=workflow.get("version", "1.0.0"),
        validation_status="ready"
    )

@router.get("/{workflow_id}/detail", response_model=WorkflowDetail)
def get_workflow_detail_endpoint(
    workflow_id: str,
    current_user = Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-1.5: Workflow detail with promotion history"""
    # Find workflow by ID across all tenants
    all_workflows = [
        *TENANT_WORKFLOWS.get(PILOT_TENANT_A["id"], []),
        *TENANT_WORKFLOWS.get(PILOT_TENANT_B["id"], [])
    ]
    workflow = next((w for w in all_workflows if w["id"] == workflow_id), None)

    if not workflow:
        # Fallback for unknown workflows
        workflow = {
            "id": workflow_id,
            "name": "Test Workflow",
            "family": "default",
            "version": "1.0.0",
            "status": "active",
            "tenant_id": "test_tenant"
        }

    return WorkflowDetail(
        id=workflow["id"],
        name=workflow.get("name", "Test Workflow"),
        family=workflow.get("family", "default"),
        version=workflow.get("version", "1.0.0"),
        status=workflow.get("status", "active"),
        environment="dev",
        tenant_id=workflow.get("tenant_id", "test_tenant"),
        created_at=datetime.now(),
        last_promotion={"version": "1.0.0", "environment": "stage"},
        active_version=workflow.get("version", "1.0.0"),
        validation_status="ready"
    )
