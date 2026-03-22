from fastapi import APIRouter, Depends
from acosplatform.auth.api_key import require_ops_token
from acosplatform.workflows.service import create_workflow_draft, get_workflow_detail, list_workflows_with_state
import uuid

router = APIRouter(prefix="/workflows", tags=["workflows"])

@router.get("")
async def list_workflows(_token: dict = Depends(require_ops_token)):
    return list_workflows_with_state()

@router.post("")
async def create_workflow(req: dict, _token: dict = Depends(require_ops_token)):
    workflow_id = str(uuid.uuid4())
    return create_workflow_draft(workflow_id, req['name'], req.get('description', ''), req.get('family', 'default'))

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, _token: dict = Depends(require_ops_token)):
    return get_workflow_detail(workflow_id)

@router.patch("/{workflow_id}")
async def update_workflow(workflow_id: str, updates: dict, _token: dict = Depends(require_ops_token)):
    # Save workflow draft
    return {"id": workflow_id, "status": "draft", **updates}
