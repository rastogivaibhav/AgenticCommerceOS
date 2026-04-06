"""Handler router for the chat pipeline.

Routes messages to appropriate handler (sync or async) based on
workflow execution timeout threshold.
"""

import logging
from typing import Dict, Any, Optional

from apps.chat_api.models.chat import ChatMessage
from apps.chat_api.handlers.sync import SyncHandler
from apps.chat_api.handlers.async_handler import AsyncHandler
from acosplatform.session.store import SessionStore
from acosplatform.job_queue.service import JobQueueService

logger = logging.getLogger(__name__)


class HandlerRouter:
    """Routes workflow execution requests to appropriate handler.

    Routing logic:
    - Workflows with timeout_seconds <= 2: Use SyncHandler (inline execution)
    - Workflows with timeout_seconds > 2: Use AsyncHandler (background job)

    This ensures fast operations complete inline while slow operations
    don't block the message handler.
    """

    # Threshold for sync vs async execution (in seconds)
    SYNC_THRESHOLD_SECONDS = 2

    def __init__(
        self,
        session_store: SessionStore,
        workflow_service: Any = None,
        job_queue_service: Optional[JobQueueService] = None,
    ):
        """Initialize HandlerRouter.

        Args:
            session_store: SessionStore instance for conversation state
            workflow_service: WorkflowService for workflow lookup
            job_queue_service: JobQueueService for async job enqueuing
        """
        self.session_store = session_store
        self.workflow_service = workflow_service

        # Initialize both handlers
        self.sync_handler = SyncHandler(
            session_store=session_store,
            workflow_service=workflow_service,
        )

        self.async_handler = AsyncHandler(
            session_store=session_store,
            workflow_service=workflow_service,
            job_queue_service=job_queue_service,
        )

    def route(
        self,
        normalized_message: ChatMessage,
        session_id: str,
        request_id: str,
    ) -> Dict[str, Any]:
        """Route message to appropriate handler based on workflow timeout.

        Flow:
        1. Detect workflow from message
        2. Look up workflow definition
        3. Check timeout_seconds
        4. Route to SyncHandler if timeout <= 2s
        5. Route to AsyncHandler if timeout > 2s

        Args:
            normalized_message: Normalized ChatMessage from adapter
            session_id: Conversation session ID
            request_id: Request tracking ID

        Returns:
            Handler result (sync or async)
        """
        try:
            logger.debug(
                f"HandlerRouter: Routing message in session {session_id}",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                },
            )

            # Get session to access context
            session = self.session_store.get_session(session_id)
            if session is None:
                logger.error(
                    f"Session {session_id} not found",
                    extra={"session_id": session_id},
                )
                return {
                    "status": "failed",
                    "error": f"Session {session_id} not found",
                    "request_id": request_id,
                }

            # Detect workflow_id from message
            workflow_id = self.sync_handler._detect_workflow_id(normalized_message)

            # Look up workflow
            if self.workflow_service is None:
                from acosplatform.workflows.service import resolve_execution_workflow
                workflow = resolve_execution_workflow(
                    tenant_id=session.context.get("tenant_id", "default"),
                    workflow_family=self.sync_handler._family_from_workflow_id(workflow_id),
                )
            else:
                workflow = self.workflow_service.resolve_execution_workflow(
                    tenant_id=session.context.get("tenant_id", "default"),
                    workflow_family=self.sync_handler._family_from_workflow_id(workflow_id),
                )

            if workflow is None:
                logger.error(
                    f"Workflow {workflow_id} not found",
                    extra={"workflow_id": workflow_id},
                )
                return {
                    "status": "failed",
                    "error": f"Workflow {workflow_id} not found",
                    "request_id": request_id,
                }

            # Get timeout from workflow
            timeout_seconds = workflow.get("timeout_seconds", self.SYNC_THRESHOLD_SECONDS)

            logger.debug(
                f"Routing to {'SyncHandler' if timeout_seconds <= self.SYNC_THRESHOLD_SECONDS else 'AsyncHandler'} (timeout={timeout_seconds}s)",
                extra={
                    "workflow_id": workflow_id,
                    "timeout_seconds": timeout_seconds,
                    "threshold": self.SYNC_THRESHOLD_SECONDS,
                },
            )

            # Route based on timeout threshold
            if timeout_seconds <= self.SYNC_THRESHOLD_SECONDS:
                # Use sync handler for fast workflows
                return self.sync_handler.execute(
                    normalized_message=normalized_message,
                    session_id=session_id,
                    request_id=request_id,
                )
            else:
                # Use async handler for slow workflows
                return self.async_handler.execute(
                    normalized_message=normalized_message,
                    session_id=session_id,
                    request_id=request_id,
                )

        except Exception as e:
            logger.error(
                f"HandlerRouter error: {str(e)}",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "error": str(e),
                },
                exc_info=True,
            )

            return {
                "status": "failed",
                "error": str(e),
                "request_id": request_id,
            }
