"""Jobs router stub for async operations."""

from fastapi import APIRouter, HTTPException
from apps.chat_api.models.job import ChatJob, JobStatusResponse
from datetime import datetime

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("")
def create_job(payload: dict):
    """Create a new async job.

    Stub implementation.
    """
    return {
        "status": "created",
        "job_id": "job_stub_" + str(hash(str(payload)))[-8:],
        "message": "Job queued for processing",
    }


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    """Get status of an async job.

    Stub implementation.
    """
    return JobStatusResponse(
        job_id=job_id,
        status="completed",
        job_type="message",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        result={"message": "Job completed"},
    )
