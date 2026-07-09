# apps/ops_api/models/run.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class RunStep(BaseModel):
    step: str
    status: str
    duration_ms: int
    error: Optional[str] = None


class RunTimeline(BaseModel):
    id: str
    workflow_id: str
    status: str
    started_at: datetime
    ended_at: datetime
    steps: List[RunStep]
    policy_decisions: Optional[List[dict]] = None


class RunListItem(BaseModel):
    id: str
    workflow_id: str
    tenant_id: str
    status: str
    started_at: datetime


class RunListResponse(BaseModel):
    runs: List[RunListItem]
