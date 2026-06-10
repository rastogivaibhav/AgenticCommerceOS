# apps/ops_api/routers/workflows.py
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import datetime
from acosplatform.auth.api_key import require_ops_roles
from apps.ops_api.models.workflow import (
    WorkflowListResponse, WorkflowListItem, WorkflowDetail, PromotionSummary,
    CreateWorkflowRequest, UpdateWorkflowRequest, TestRunRequest, ExecuteRequest,
    TestRunResponse, ExecuteResponse
)

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

@router.post("", response_model=WorkflowDetail)
def create_workflow_endpoint(
    request: CreateWorkflowRequest,
    current_user = Depends(require_ops_roles("editor", "admin"))
):
    """Create a new workflow"""
    import uuid
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

    new_workflow = {
        "id": workflow_id,
        "name": request.name,
        "family": request.family,
        "version": "1.0.0",
        "status": request.status or "draft",
        "environment": request.environment or "dev",
        "tenant_id": current_user.get("tenant_id", "unknown") if hasattr(current_user, "get") else getattr(current_user, "tenant_id", "unknown"),
    }

    ALL_WORKFLOWS_BY_ID[workflow_id] = new_workflow

    return WorkflowDetail(
        id=new_workflow["id"],
        name=new_workflow["name"],
        family=new_workflow["family"],
        version=new_workflow["version"],
        status=new_workflow["status"],
        environment=new_workflow["environment"],
        tenant_id=new_workflow["tenant_id"],
        created_at=MOCK_CREATED_AT,
        last_promotion=None,
        active_version="1.0.0",
        validation_status="draft"
    )

@router.patch("/{workflow_id}", response_model=WorkflowDetail)
def update_workflow_endpoint(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    current_user = Depends(require_ops_roles("editor", "admin"))
):
    """Update an existing workflow"""
    workflow = ALL_WORKFLOWS_BY_ID.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Update fields
    if request.name is not None:
        workflow["name"] = request.name
    if request.family is not None:
        workflow["family"] = request.family
    if request.status is not None:
        workflow["status"] = request.status
    if request.environment is not None:
        workflow["environment"] = request.environment
    if request.step_definitions is not None:
        workflow["step_definitions"] = request.step_definitions
    if request.edges is not None:
        workflow["edges"] = request.edges

    return WorkflowDetail(
        id=workflow["id"],
        name=workflow.get("name", "Untitled Workflow"),
        family=workflow.get("family", "unknown"),
        version=workflow.get("version", "1.0.0"),
        status=workflow.get("status", "draft"),
        environment=workflow.get("environment", "dev"),
        tenant_id=workflow.get("tenant_id", "unknown"),
        created_at=MOCK_CREATED_AT,
        last_promotion=None,
        active_version=workflow.get("version", "1.0.0"),
        validation_status=workflow.get("status", "draft")
    )

@router.post("/{workflow_id}/test-run", response_model=TestRunResponse)
def test_workflow_endpoint(
    workflow_id: str,
    request: TestRunRequest,
    current_user = Depends(require_ops_roles("editor", "admin"))
):
    """Test run a workflow"""
    workflow = ALL_WORKFLOWS_BY_ID.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    import uuid
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    return TestRunResponse(
        run_id=run_id,
        status="completed",
        output_data={"message": "Test run completed successfully"},
        error=None
    )

@router.post("/{workflow_id}/execute", response_model=ExecuteResponse)
def execute_workflow_endpoint(
    workflow_id: str,
    request: ExecuteRequest,
    current_user = Depends(require_ops_roles("editor", "admin"))
):
    """Execute a workflow"""
    workflow = ALL_WORKFLOWS_BY_ID.get(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    import uuid
    run_id = f"exec_{uuid.uuid4().hex[:12]}"

    return ExecuteResponse(
        run_id=run_id,
        status="queued",
        output_data=None,
        error=None
    )
