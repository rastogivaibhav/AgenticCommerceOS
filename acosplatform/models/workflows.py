"""Pydantic models for workflow registry operations."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


WORKFLOW_FAMILIES = ("discovery", "purchase", "post_purchase", "service", "engagement")


class WorkflowCreateRequest(BaseModel):
    tenant_id: str = Field(default="default", max_length=64)
    name: str = Field(..., min_length=3, max_length=120)
    workflow_family: Literal["discovery", "purchase", "post_purchase", "service", "engagement"]
    description: str = Field(default="", max_length=500)
    business_owner: str = Field(default="acos-team", max_length=120)
    change_summary: str = Field(default="Initial workflow draft", max_length=240)


class WorkflowVersionCreateRequest(BaseModel):
    change_summary: str = Field(..., min_length=3, max_length=240)
    validation_status: Literal["draft", "validated", "approved"] = "draft"


class WorkflowPromotionRequest(BaseModel):
    target_environment: Literal["dev", "test", "stage", "prod"] = "dev"
    approval_note: str = Field(default="", max_length=240)
    source_environment: Optional[Literal["dev", "test", "stage", "prod"]] = None
