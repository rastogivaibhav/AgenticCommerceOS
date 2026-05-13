"""Job/task models for chat operations."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatJob(BaseModel):
    """A chat operation job."""

    id: str
    job_type: str  # e.g., "message", "thread_sync", "reaction_handler"
    status: str  # "pending", "running", "completed", "failed"
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None


class JobStatusResponse(BaseModel):
    """Response for job status queries."""

    job_id: str
    status: str
    job_type: str
    created_at: datetime
    updated_at: datetime
    result: Optional[dict] = None
    error: Optional[str] = None
