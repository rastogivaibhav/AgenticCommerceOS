# apps/ops_api/models/workflow.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PromotionSummary(BaseModel):
    version: str
    environment: str

class WorkflowListItem(BaseModel):
    id: str
    name: str
    family: str
    version: str
    status: str
    environment: str
    tenant_id: str
    created_at: datetime

class WorkflowDetail(BaseModel):
    id: str
    name: str
    family: str
    version: str
    status: str
    environment: str
    tenant_id: str
    created_at: datetime
    last_promotion: Optional[PromotionSummary]
    active_version: str
    validation_status: str

class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowListItem]
    total: int
    filtered_by: Optional[dict]

class CreateWorkflowRequest(BaseModel):
    name: str
    family: str
    status: Optional[str] = "draft"
    environment: Optional[str] = "dev"

class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    family: Optional[str] = None
    status: Optional[str] = None
    environment: Optional[str] = None
    step_definitions: Optional[dict] = None
    edges: Optional[list] = None

class TestRunRequest(BaseModel):
    input_data: Optional[dict] = None
    step_definitions: Optional[dict] = None
    edges: Optional[list] = None

class ExecuteRequest(BaseModel):
    input_data: Optional[dict] = None

class TestRunResponse(BaseModel):
    run_id: str
    status: str
    output_data: Optional[dict] = None
    error: Optional[str] = None

class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    output_data: Optional[dict] = None
    error: Optional[str] = None
