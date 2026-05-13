# apps/ops_api/models/approval.py
from pydantic import BaseModel
from typing import List, Optional


class ApprovalQueueItem(BaseModel):
    id: str
    workflow_id: str
    tenant_id: str
    status: str
    request_type: str


class ApprovalQueueResponse(BaseModel):
    approvals: List[ApprovalQueueItem]


class ApprovalDetail(BaseModel):
    id: str
    status: str
    evidence: dict
    rollback_plan: dict
