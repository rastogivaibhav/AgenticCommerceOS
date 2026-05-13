# apps/ops_api/models/promotion.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PromotionDiff(BaseModel):
    changes: List[str]
    affected_fields: List[str]


class PromotionRequest(BaseModel):
    target_environment: str
    version: str
    promotion_reason: str


class ApprovalResponse(BaseModel):
    approval_id: str
    status: str  # pending_approval, approved, rejected
    approval_reason: Optional[str] = None


class PromotionResponse(BaseModel):
    id: str
    status: str
    target_environment: str
    version: str
    rollback_version: str
