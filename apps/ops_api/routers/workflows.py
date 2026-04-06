# apps/ops_api/routers/workflows.py
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from apps.ops_api.models.workflow import WorkflowListResponse, WorkflowListItem, WorkflowDetail, PromotionSummary

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

# Fixed timestamp for consistent mock data
MOCK_CREATED_AT = datetime(2026, 3, 1, 10, 0, 0)

# Map tenant IDs to their workflows with environment information
TENANT_WORKFLOWS = {
    PILOT_TENANT_A["id"]: [
        {**WORKFLOW_DISCOVERY, "environment": "dev"},
        {**WORKFLOW_POST_PURCHASE, "environment": "dev"}
    ],
    PILOT_TENANT_B["id"]: [
        {**WORKFLOW_SERVICE_GUIDANCE, "environment": "dev"},
        {**WORKFLOW_RETURNS, "environment": "dev"}
    ],
}

# Fixture map for lookup by workflow_id
ALL_WORKFLOWS_BY_ID = {}
for tenant_workflows in TENANT_WORKFLOWS.values():
    for wf in tenant_workflows:
        ALL_WORKFLOWS_BY_ID[wf["id"]] = wf

def _get_mock_workflows(tenant_id: str, family=None, status=None, environment=None):
    """Get filtered list of mock workflows"""
    tenant_workflows = TENANT_WORKFLOWS.get(tenant_id, [])
    filtered = [
        w for w in tenant_workflows
        if (family is None or w.get("family") == family)
        and (status is None or w.get("status") == status)
        and (environment is None or w.get("environment") == environment)
    ]
    return filtered

@router.get("", response_model=WorkflowListResponse)
def list_workflows_endpoint(
    tenant_id: str = Query(...),
    family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    current_user = Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-1.1: List workflows with filtering"""
    # Get and filter workflows for the tenant
    filtered_workflows = _get_mock_workflows(tenant_id, family, status, environment)

    # Convert to response items
    workflows = [
        WorkflowListItem(
            id=wf["id"],
            name=wf["name"],
            family=wf["family"],
            version=wf.get("version", "1.0.0"),
            status=wf.get("status", "active"),
            environment=wf.get("environment", "dev"),
            tenant_id=tenant_id,
            created_at=MOCK_CREATED_AT
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
    # Find workflow by ID from fixture data
    workflow = ALL_WORKFLOWS_BY_ID.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowDetail(
        id=workflow["id"],
        name=workflow.get("name", "Untitled Workflow"),
        family=workflow.get("family", "unknown"),
        version=workflow.get("version", "1.0.0"),
        status=workflow.get("status", "active"),
        environment=workflow.get("environment", "dev"),
        tenant_id=workflow.get("tenant_id", "unknown"),
        created_at=MOCK_CREATED_AT,
        last_promotion=None,
        active_version=workflow.get("version", "1.0.0"),
        validation_status="ready"
    )

@router.get("/{workflow_id}/detail", response_model=WorkflowDetail)
def get_workflow_detail_endpoint(
    workflow_id: str,
    current_user = Depends(require_ops_roles("viewer", "editor", "admin"))
):
    """WA-1.5: Workflow detail with promotion history"""
    # Find workflow by ID from fixture data
    workflow = ALL_WORKFLOWS_BY_ID.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowDetail(
        id=workflow["id"],
        name=workflow.get("name", "Untitled Workflow"),
        family=workflow.get("family", "unknown"),
        version=workflow.get("version", "1.0.0"),
        status=workflow.get("status", "active"),
        environment=workflow.get("environment", "dev"),
        tenant_id=workflow.get("tenant_id", "unknown"),
        created_at=MOCK_CREATED_AT,
        last_promotion=PromotionSummary(version="1.0.0", environment="stage"),
        active_version=workflow.get("version", "1.0.0"),
        validation_status="ready"
    )
