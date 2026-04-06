"""Jobs router for async job status and result polling."""

import logging
from fastapi import APIRouter, HTTPException, status
from apps.chat_api.models.job import ChatJob, JobStatusResponse
from acosplatform.job_queue.service import JobQueueService
from acosplatform.job_queue.models import JobStatus
from datetime import datetime

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

logger = logging.getLogger(__name__)

# Initialize services
_job_queue_service = None


def get_job_queue_service() -> JobQueueService:
    """Get or initialize JobQueueService."""
    global _job_queue_service
    if _job_queue_service is None:
        _job_queue_service = JobQueueService()
    return _job_queue_service


@router.post("")
def create_job(payload: dict):
    """Create a new async job.

    This is a legacy endpoint. New jobs should be created via POST /api/chat/message.
    """
    logger.warning("Direct job creation via POST /api/jobs is deprecated")
    job_queue_service = get_job_queue_service()

    try:
        job = job_queue_service.create_job(
            workflow_id=payload.get("workflow_id", "unknown"),
            workflow_name=payload.get("workflow_name", "unknown"),
            payload=payload.get("payload", {}),
            tenant_id=payload.get("tenant_id"),
        )

        return {
            "status": "created",
            "job_id": job.id,
            "message": "Job queued for processing",
        }

    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job",
        )


@router.get("/{job_id}/status")
def get_job_status(job_id: str):
    """Get status of an async job.

    Returns current job status and progress information.

    Response when processing:
    {
        "status": "processing",
        "current_step": 2,
        "total_steps": 4,
        "step_name": "Filtering by price",
        "eta_seconds": 3
    }

    Response when queued/completed:
    {
        "status": "queued|completed|failed",
        "job_id": "...",
        "created_at": "2026-04-06T...",
        "updated_at": "2026-04-06T..."
    }

    Returns 404 if job not found.
    """
    logger.debug(f"Getting status for job {job_id}")

    job_queue_service = get_job_queue_service()
    job = job_queue_service.get_job(job_id)

    if job is None:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    logger.debug(
        f"Job {job_id} status: {job.status}",
        extra={"job_id": job_id, "status": job.status},
    )

    # Build response
    response = {
        "job_id": job.id,
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat() if job.updated_at else job.created_at.isoformat(),
    }

    # Add optional fields if available
    if job.started_at:
        response["started_at"] = job.started_at.isoformat()

    if job.completed_at:
        response["completed_at"] = job.completed_at.isoformat()

    if job.error:
        response["error"] = job.error

    # For processing jobs, optionally include progress info (future enhancement)
    if job.status == JobStatus.PROCESSING:
        # TODO: Add progress tracking to Job model
        response["current_step"] = 2
        response["total_steps"] = 4

    return response


@router.get("/{job_id}/result")
async def get_job_result(job_id: str):
    """Get final result of an async job.

    Returns final result when job is completed:
    {
        "status": "completed",
        "result": "Found 5 dresses: ...",
        "execution_time_ms": 8234
    }

    Returns 202 Accepted if job is still processing:
    {
        "status": "processing",
        "polling_endpoint": "/api/jobs/{job_id}/status"
    }

    Returns 404 if job not found.
    """
    from fastapi.responses import JSONResponse

    logger.debug(f"Getting result for job {job_id}")

    job_queue_service = get_job_queue_service()
    job = job_queue_service.get_job(job_id)

    if job is None:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # If job is still processing, return 202 Accepted
    if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        logger.debug(f"Job {job_id} still processing, returning 202")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": job.status.value,
                "polling_endpoint": f"/api/jobs/{job_id}/status",
            },
        )

    # If job is completed, return result
    if job.status == JobStatus.COMPLETED:
        logger.info(
            f"Job {job_id} completed",
            extra={"job_id": job_id},
        )

        # Calculate execution time
        execution_time_ms = None
        if job.started_at and job.completed_at:
            execution_time_ms = int(
                (job.completed_at - job.started_at).total_seconds() * 1000
            )

        response = {
            "status": "completed",
            "result": job.result,
        }

        if execution_time_ms is not None:
            response["execution_time_ms"] = execution_time_ms

        return response

    # If job failed, return error
    if job.status == JobStatus.FAILED:
        logger.error(
            f"Job {job_id} failed: {job.error}",
            extra={"job_id": job_id, "error": job.error},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "failed",
                "error": job.error,
            },
        )

    # Unknown status
    logger.warning(f"Unknown job status: {job.status}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unknown job status",
    )
