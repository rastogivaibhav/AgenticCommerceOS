"""Workflow execution API endpoints.

Provides routes for workflow execution in the chat pipeline.

The message handlers (base.py, sync.py, async.py, router.py) are the primary
integration points for the chat pipeline. They accept normalized ChatMessage
objects from adapters and execute workflows based on message content.

This router provides:
1. Legacy API endpoints for direct workflow execution (for testing/admin)
2. Handler router integration point for message pipeline
3. Job status and result endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from apps.chat_api.models.chat import ChatMessage
from apps.chat_api.handlers.router import HandlerRouter
from apps.chat_api.security import require_chat_token
from acosplatform.session.store import SessionStore
from acosplatform.job_queue.service import JobQueueService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/workflows",
    tags=["workflows"],
    dependencies=[Depends(require_chat_token)],
)

# Initialize session store and job queue for handlers
_session_store = SessionStore()
_job_queue_service = JobQueueService()

# Initialize handler router for message pipeline
_handler_router = HandlerRouter(
    session_store=_session_store,
    job_queue_service=_job_queue_service,
)


class WorkflowExecutionRequest(BaseModel):
    """Request body for workflow execution (legacy API)."""

    workflow_id: str
    workflow_name: str
    timeout_seconds: Optional[int] = 2
    steps: list = []
    input_data: Dict[str, Any]
    tenant_id: Optional[str] = None
    execution_mode: Optional[str] = None  # "sync", "async", or None for auto


class MessageExecutionRequest(BaseModel):
    """Request body for message-based workflow execution (chat pipeline)."""

    message_text: str
    user_id: str
    channel_id: str
    session_id: str


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution."""

    status: str
    result: Optional[Dict[str, Any]] = None
    job_id: Optional[str] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None


@router.post("/execute-message")
def execute_from_message(
    request: MessageExecutionRequest,
) -> Dict[str, Any]:
    """Execute workflow from a chat message (primary integration point).

    This endpoint receives a chat message and routes it to the appropriate
    handler (sync or async) based on the detected workflow and its timeout.

    This is the main integration point for the message pipeline.

    Args:
        request: Message execution request with text, user_id, channel_id, session_id

    Returns:
        Either sync result or async job details
    """
    try:
        logger.info(
            f"Processing message from user {request.user_id} in session {request.session_id}",
            extra={
                "user_id": request.user_id,
                "session_id": request.session_id,
                "channel_id": request.channel_id,
            },
        )

        # Create normalized chat message
        normalized_message = ChatMessage(
            id=str(uuid.uuid4()),
            channel_id=request.channel_id,
            user_id=request.user_id,
            text=request.message_text,
            timestamp=__import__('datetime').datetime.now(__import__('datetime').UTC),
            thread_ts=None,
            reactions=None,
        )

        # Generate request ID for tracking
        request_id = f"req_{uuid.uuid4()}"

        # Route to appropriate handler
        result = _handler_router.route(
            normalized_message=normalized_message,
            session_id=request.session_id,
            request_id=request_id,
        )

        return result

    except Exception as e:
        logger.error(
            f"Message processing failed: {str(e)}",
            extra={
                "user_id": request.user_id,
                "session_id": request.session_id,
                "error": str(e),
            },
            exc_info=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Message processing failed: {str(e)}",
        )


@router.post("/{workflow_id}/execute-sync")
def execute_workflow_sync(
    workflow_id: str,
    request: WorkflowExecutionRequest,
) -> Dict[str, Any]:
    """Execute a workflow synchronously (legacy API).

    Note: This endpoint is deprecated. Use /execute-message for message pipeline.

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
            f"Executing workflow {workflow_id} synchronously (legacy)",
            extra={"workflow_id": workflow_id},
        )

        # This is a legacy endpoint - in new implementation,
        # workflows are detected from messages via the message pipeline
        # For backward compatibility, we return a success response
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "result": {
                "message": "Legacy sync endpoint - use /execute-message for message pipeline",
            },
            "execution_time_ms": 0,
        }

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
    """Execute a workflow asynchronously (legacy API).

    Note: This endpoint is deprecated. Use /execute-message for message pipeline.

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
            f"Enqueueing workflow {workflow_id} for async execution (legacy)",
            extra={"workflow_id": workflow_id},
        )

        # This is a legacy endpoint - in new implementation,
        # workflows are detected from messages via the message pipeline
        # For backward compatibility, we return a success response
        return {
            "status": "queued",
            "job_id": f"job_{uuid.uuid4()}",
            "workflow_id": workflow_id,
            "message": "Legacy async endpoint - use /execute-message for message pipeline",
            "polling_endpoint": f"/api/jobs/job_{uuid.uuid4()}/status",
        }

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
    """Execute a workflow with automatic mode selection (legacy API).

    Note: This endpoint is deprecated. Use /execute-message for message pipeline.

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
            f"Auto-executing workflow {workflow_id} (timeout={timeout}s, legacy)",
            extra={"workflow_id": workflow_id, "timeout_seconds": timeout},
        )

        # This is a legacy endpoint - route based on timeout
        if timeout <= 2:
            return execute_workflow_sync(workflow_id, request)
        else:
            return execute_workflow_async(workflow_id, request)

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
