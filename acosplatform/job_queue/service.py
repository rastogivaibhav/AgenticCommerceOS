# acosplatform/job_queue/service.py
"""
Job queue service for managing async workflow execution.

Provides methods to create, track, and manage job lifecycle using Redis cache
and Celery for task execution.
"""

import json
import logging
from datetime import datetime, UTC
from typing import Optional, Any, Dict

import redis

from .models import Job, JobStatus

logger = logging.getLogger(__name__)


class JobQueueService:
    """
    Service for managing async job execution.

    Uses Redis for fast status lookups and caching, with 24-hour TTL.
    Integrates with Celery for actual task execution.
    """

    # Job TTL in seconds (24 hours)
    JOB_TTL = 86400

    # Redis key prefixes
    JOB_PREFIX = "job:"
    STATUS_PREFIX = "job_status:"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize JobQueueService.

        Args:
            redis_client: Redis client instance. If None, creates a new connection
                         to localhost:6379/0
        """
        if redis_client is None:
            self.redis = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True,
            )
        else:
            self.redis = redis_client

    def create_job(
        self,
        workflow_id: str,
        workflow_name: str,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Job:
        """
        Create a new job in QUEUED status.

        Args:
            workflow_id: Reference to the workflow definition
            workflow_name: Name of the workflow
            payload: Input data for the workflow
            tenant_id: Optional tenant identifier for multi-tenancy

        Returns:
            Created Job object with status QUEUED
        """
        job = Job(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            payload=payload,
            tenant_id=tenant_id,
            status=JobStatus.QUEUED,
        )

        # Store job data in Redis
        job_key = f"{self.JOB_PREFIX}{job.id}"
        job_json = job.model_dump_json()
        self.redis.setex(job_key, self.JOB_TTL, job_json)

        # Cache status separately for fast lookups
        status_key = f"{self.STATUS_PREFIX}{job.id}"
        self.redis.setex(status_key, self.JOB_TTL, JobStatus.QUEUED.value)

        logger.info(
            f"Created job {job.id} for workflow {workflow_name}",
            extra={"job_id": job.id, "workflow_id": workflow_id},
        )

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job by ID.

        Args:
            job_id: The job identifier

        Returns:
            Job object if found, None otherwise
        """
        job_key = f"{self.JOB_PREFIX}{job_id}"
        job_json = self.redis.get(job_key)

        if job_json is None:
            logger.debug(f"Job {job_id} not found")
            return None

        try:
            # Handle both bytes and str (for Redis vs fakeredis)
            if isinstance(job_json, bytes):
                job_json = job_json.decode("utf-8")
            job_data = json.loads(job_json)
            return Job(**job_data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to deserialize job {job_id}: {e}")
            return None

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get the current status of a job.

        Uses Redis cache for fast lookups (O(1) instead of deserializing full job).

        Args:
            job_id: The job identifier

        Returns:
            JobStatus if found, None otherwise
        """
        status_key = f"{self.STATUS_PREFIX}{job_id}"
        status_value = self.redis.get(status_key)

        if status_value is None:
            logger.debug(f"Job status not found for {job_id}")
            return None

        try:
            # Handle both bytes and str (for Redis vs fakeredis)
            if isinstance(status_value, bytes):
                status_value = status_value.decode("utf-8")
            return JobStatus(status_value)
        except ValueError as e:
            logger.error(f"Invalid job status for {job_id}: {status_value} ({e})")
            return None

    def mark_job_processing(self, job_id: str) -> bool:
        """
        Mark a job as currently processing.

        Args:
            job_id: The job identifier

        Returns:
            True if successful, False otherwise
        """
        job = self.get_job(job_id)
        if job is None:
            logger.warning(f"Cannot mark job {job_id} as processing: job not found")
            return False

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(UTC)

        # Update both job data and status cache
        job_key = f"{self.JOB_PREFIX}{job_id}"
        status_key = f"{self.STATUS_PREFIX}{job_id}"

        job_json = job.model_dump_json()
        self.redis.setex(job_key, self.JOB_TTL, job_json)
        self.redis.setex(status_key, self.JOB_TTL, JobStatus.PROCESSING.value)

        logger.info(f"Job {job_id} marked as processing")
        return True

    def mark_job_completed(
        self, job_id: str, result: Dict[str, Any]
    ) -> bool:
        """
        Mark a job as completed with result data.

        Args:
            job_id: The job identifier
            result: Result data from job execution

        Returns:
            True if successful, False otherwise
        """
        job = self.get_job(job_id)
        if job is None:
            logger.warning(f"Cannot mark job {job_id} as completed: job not found")
            return False

        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.now(UTC)

        # Update both job data and status cache
        job_key = f"{self.JOB_PREFIX}{job_id}"
        status_key = f"{self.STATUS_PREFIX}{job_id}"

        job_json = job.model_dump_json()
        self.redis.setex(job_key, self.JOB_TTL, job_json)
        self.redis.setex(status_key, self.JOB_TTL, JobStatus.COMPLETED.value)

        logger.info(f"Job {job_id} marked as completed")
        return True

    def mark_job_failed(self, job_id: str, error: str) -> bool:
        """
        Mark a job as failed with error message.

        Args:
            job_id: The job identifier
            error: Error message describing the failure

        Returns:
            True if successful, False otherwise
        """
        job = self.get_job(job_id)
        if job is None:
            logger.warning(f"Cannot mark job {job_id} as failed: job not found")
            return False

        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.now(UTC)

        # Update both job data and status cache
        job_key = f"{self.JOB_PREFIX}{job_id}"
        status_key = f"{self.STATUS_PREFIX}{job_id}"

        job_json = job.model_dump_json()
        self.redis.setex(job_key, self.JOB_TTL, job_json)
        self.redis.setex(status_key, self.JOB_TTL, JobStatus.FAILED.value)

        logger.error(f"Job {job_id} marked as failed: {error}")
        return True
