"""Asynchronous workflow execution handler.

Enqueues workflows for background processing using JobQueueService.
Returns job ID immediately and executes workflow asynchronously.
Used for complex workflows that take > 2 seconds.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from acosplatform.job_queue.service import JobQueueService

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Asynchronous workflow executor.

    Enqueues workflows for background execution using Celery + Redis.
    Returns job ID immediately without waiting for completion.

    Returns results as dicts (not Job objects).
    """

    def __init__(self, job_queue_service: Optional[JobQueueService] = None):
        """Initialize AsyncExecutor.

        Args:
            job_queue_service: JobQueueService instance. If None, creates a new one.
        """
        if job_queue_service is None:
            self.job_queue_service = JobQueueService()
        else:
            self.job_queue_service = job_queue_service

    def execute(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow asynchronously.

        Args:
            workflow: Workflow definition with workflow_id, workflow_name, timeout_seconds, steps
            input_data: Input data for the workflow
            tenant_id: Tenant identifier for multi-tenancy

        Returns:
            Dict with job_id, status (queued), and polling_endpoint
        """
        return self.enqueue(
            workflow=workflow,
            input_data=input_data,
            tenant_id=tenant_id,
        )

    def enqueue(
        self,
        workflow: Dict[str, Any],
        input_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enqueue a workflow for async execution.

        Uses JobQueueService.create_job() to queue the workflow.

        Args:
            workflow: Workflow definition
            input_data: Input data
            tenant_id: Optional tenant ID

        Returns:
            Dict with job_id, status, and polling_endpoint
        """
        workflow_id = workflow.get("workflow_id", "unknown")
        workflow_name = workflow.get("workflow_name", "Unknown")

        logger.info(
            f"Enqueueing async workflow {workflow_name} ({workflow_id})",
            extra={"workflow_id": workflow_id, "tenant_id": tenant_id},
        )

        try:
            # Create job using JobQueueService
            job = self.job_queue_service.create_job(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                payload=input_data,
                tenant_id=tenant_id,
            )

            logger.info(
                f"Workflow {workflow_name} enqueued as job {job.id}",
                extra={"job_id": job.id, "workflow_id": workflow_id},
            )

            # Return dict result (not Job object)
            return {
                "job_id": job.id,
                "status": "queued",
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "polling_endpoint": f"/api/jobs/{job.id}/status",
                "result_endpoint": f"/api/jobs/{job.id}/result",
                "created_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Failed to enqueue workflow {workflow_name}: {str(e)}",
                extra={"workflow_id": workflow_id, "error": str(e)},
                exc_info=True,
            )

            return {
                "status": "failed",
                "error": str(e),
                "workflow_id": workflow_id,
                "created_at": datetime.now(UTC).isoformat(),
            }

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of an async job.

        Args:
            job_id: Job identifier

        Returns:
            Dict with job_id, status, and other details
        """
        try:
            job = self.job_queue_service.get_job(job_id)

            if job is None:
                logger.warning(f"Job {job_id} not found")
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "error": "Job not found",
                }

            logger.debug(f"Retrieved status for job {job_id}: {job.status.value}")

            return {
                "job_id": job.id,
                "status": job.status.value,
                "workflow_id": job.workflow_id,
                "workflow_name": job.workflow_name,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error": job.error,
            }

        except Exception as e:
            logger.error(
                f"Failed to get status for job {job_id}: {str(e)}",
                extra={"job_id": job_id, "error": str(e)},
                exc_info=True,
            )

            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e),
            }

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get result of a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Dict with job_id, status, and result (if completed)
        """
        try:
            job = self.job_queue_service.get_job(job_id)

            if job is None:
                logger.warning(f"Job {job_id} not found")
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "error": "Job not found",
                }

            result_dict = {
                "job_id": job.id,
                "status": job.status.value,
                "workflow_id": job.workflow_id,
                "workflow_name": job.workflow_name,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }

            if job.result:
                result_dict["result"] = job.result

            if job.error:
                result_dict["error"] = job.error

            logger.debug(
                f"Retrieved result for job {job_id} with status {job.status.value}",
                extra={"job_id": job_id},
            )

            return result_dict

        except Exception as e:
            logger.error(
                f"Failed to get result for job {job_id}: {str(e)}",
                extra={"job_id": job_id, "error": str(e)},
                exc_info=True,
            )

            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e),
            }
