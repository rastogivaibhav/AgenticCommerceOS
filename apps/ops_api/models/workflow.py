# apps/ops_api/models/workflow.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    last_promotion: Optional[dict]
    active_version: str
    validation_status: str

class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowListItem]
    total: int
    filtered_by: Optional[dict]
