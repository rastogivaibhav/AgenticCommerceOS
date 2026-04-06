"""Workflow execution API endpoints.

Provides routes for synchronous and asynchronous workflow execution.
Routes requests to appropriate executor based on workflow timeout.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional

from apps.chat_api.handlers.sync_executor import SyncExecutor
from apps.chat_api.handlers.async_executor import AsyncExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Initialize executors
_sync_executor = SyncExecutor()
_async_executor = AsyncExecutor()


class WorkflowExecutionRequest(BaseModel):
    """Request body for workflow execution."""

    workflow_id: str
    workflow_name: str
    timeout_seconds: Optional[int] = 2
    steps: list = []
    input_data: Dict[str, Any]
    tenant_id: Optional[str] = None
    execution_mode: Optional[str] = None  # "sync", "async", or None for auto


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution."""

    status: str
    result: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


@router.post("/{workflow_id}/execute-sync")
def execute_workflow_sync(
    workflow_id: str,
    request: WorkflowExecutionRequest,
) -> Dict[str, Any]:
    """Execute a workflow synchronously.

    Executes the workflow inline and returns the result directly.
    Use for fast workflows that complete within 2 seconds.

    Args:
        workflow_id: Workflow identifier from URL
        request: Workflow execution request with input_data and steps

    Returns:
        Dict with status, result, and execution_time_ms
    """
    try:
        logger.info(
            f"Executing workflow {workflow_id} synchronously",
            extra={"workflow_id": workflow_id},
        )

        workflow = {
            "workflow_id": workflow_id,
            "workflow_name": request.workflow_name,
            "timeout_seconds": request.timeout_seconds or 2,
            "steps": request.steps,
        }

        result = _sync_executor.execute(
            workflow=workflow,
            input_data=request.input_data,
        )

        return result

    except Exception as e:
        logger.error(
            f"Sync execution failed for workflow {workflow_id}: {str(e)}",
            extra={"workflow_id": workflow_id, "error": str(e)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}",
        )


@router.post("/{workflow_id}/execute-async")
def execute_workflow_async(
    workflow_id: str,
    request: WorkflowExecutionRequest,
) -> Dict[str, Any]:
    """Execute a workflow asynchronously.

    Queues the workflow for background execution and returns immediately
    with a job ID. Use for complex workflows that take > 2 seconds.

    Args:
        workflow_id: Workflow identifier from URL
        request: Workflow execution request with input_data and steps

    Returns:
        Dict with job_id, status (queued), and polling_endpoint
    """
    try:
        logger.info(
            f"Enqueueing workflow {workflow_id} for async execution",
            extra={"workflow_id": workflow_id},
        )

        workflow = {
            "workflow_id": workflow_id,
            "workflow_name": request.workflow_name,
            "timeout_seconds": request.timeout_seconds or 2,
            "steps": request.steps,
        }

        result = _async_executor.execute(
            workflow=workflow,
            input_data=request.input_data,
            tenant_id=request.tenant_id,
        )

        # Return 202 Accepted for async operations
        return result

    except Exception as e:
        logger.error(
            f"Async execution failed for workflow {workflow_id}: {str(e)}",
            extra={"workflow_id": workflow_id, "error": str(e)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Workflow enqueuing failed: {str(e)}",
        )


@router.post("/{workflow_id}/execute")
def execute_workflow_auto(
    workflow_id: str,
    request: WorkflowExecutionRequest,
) -> Dict[str, Any]:
    """Execute a workflow with automatic mode selection.

    Automatically routes to sync or async executor based on timeout_seconds:
    - If timeout_seconds <= 2: Use sync execution (inline)
    - If timeout_seconds > 2: Use async execution (background job)

    Args:
        workflow_id: Workflow identifier from URL
        request: Workflow execution request

    Returns:
        Either sync result or async job details depending on timeout
    """
    try:
        timeout = request.timeout_seconds or 2

        logger.info(
            f"Auto-executing workflow {workflow_id} (timeout={timeout}s)",
            extra={"workflow_id": workflow_id, "timeout_seconds": timeout},
        )

        # Route based on timeout
        if timeout <= 2:
            # Use sync execution for fast workflows
            result = execute_workflow_sync(workflow_id, request)
        else:
            # Use async execution for slow workflows
            result = execute_workflow_async(workflow_id, request)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Auto execution failed for workflow {workflow_id}: {str(e)}",
            extra={"workflow_id": workflow_id, "error": str(e)},
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}",
        )
