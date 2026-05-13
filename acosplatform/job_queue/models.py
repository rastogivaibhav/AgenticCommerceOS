# acosplatform/job_queue/models.py
"""
Data models for job queue service.

Defines Job model and JobStatus enums for async workflow execution.
"""

from enum import Enum
from datetime import datetime, UTC
from typing import Optional, Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    """Job status states."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """
    Job model for async workflow execution.

    Attributes:
        id: Unique job identifier
        workflow_id: Reference to the workflow being executed
        workflow_name: Name of the workflow
        tenant_id: Optional tenant identifier for multi-tenancy
        payload: Input data for the workflow
        status: Current job status
        result: Output data when completed (optional)
        error: Error message if failed (optional)
        created_at: Job creation timestamp
        started_at: When job processing started (optional)
        completed_at: When job processing completed (optional)
        current_step: Current step number being executed (1-indexed) (optional)
        total_steps: Total number of steps in workflow (optional)
        step_name: Name of current step being executed (optional)
        eta_seconds: Estimated seconds remaining to completion (optional)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    workflow_name: str
    tenant_id: Optional[str] = None
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    step_name: Optional[str] = None
    eta_seconds: Optional[int] = None

    model_config = ConfigDict(use_enum_values=False)
