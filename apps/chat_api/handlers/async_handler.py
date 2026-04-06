"""Asynchronous workflow handler for complex operations in the chat pipeline.

Queues workflows for background execution for operations that take > 2 seconds.
Receives normalized chat messages from the Slack adapter and returns immediately
with a job ID for polling.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from apps.chat_api.models.chat import ChatMessage
from apps.chat_api.handlers.base import BaseHandler
from acosplatform.session.store import SessionStore
from acosplatform.session.models import MessageRole
from acosplatform.job_queue.service import JobQueueService

logger = logging.getLogger(__name__)


class AsyncHandler(BaseHandler):
    """Asynchronous workflow handler for the chat pipeline.

    Queues workflows for background execution and returns immediately
    with a job ID. Used for complex workflows that take > 2 seconds.

    Handles:
    - Message retrieval from SessionStore
    - Adding messages to conversation history
    - Workflow detection from message content
    - Job enqueuing via JobQueueService
    - Job ID and polling endpoint generation
    """

    def __init__(
        self,
        session_store: SessionStore,
        workflow_service: Any = None,  # Injected dependency
        job_queue_service: Optional[JobQueueService] = None,
    ):
        """Initialize AsyncHandler.

        Args:
            session_store: SessionStore instance for managing conversation state
            workflow_service: WorkflowService instance for workflow lookup.
                             If None, will be imported lazily.
            job_queue_service: JobQueueService instance for enqueuing jobs.
                              If None, creates a new one.
        """
        super().__init__(session_store)
        self.workflow_service = workflow_service
        if job_queue_service is None:
            self.job_queue_service = JobQueueService()
        else:
            self.job_queue_service = job_queue_service

    def execute(
        self,
        normalized_message: ChatMessage,
        session_id: str,
        request_id: str,
    ) -> Dict[str, Any]:
        """Execute workflow asynchronously from a chat message.

        Flow:
        1. Get session from SessionStore
        2. Add normalized_message to conversation history
        3. Detect workflow_id from message
        4. Look up workflow definition from registry
        5. Enqueue workflow for background execution
        6. Return job ID and polling endpoint

        Args:
            normalized_message: Normalized ChatMessage from SlackAdapter
            session_id: Conversation session ID
            request_id: Request tracking ID

        Returns:
            Dict with job_id, status (queued), and polling endpoint
        """
        try:
            logger.info(
                f"AsyncHandler: Enqueueing workflow from message in session {session_id}",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "user_id": normalized_message.user_id,
                },
            )

            # 1. Retrieve session from SessionStore
            session = self.session_store.get_session(session_id)
            if session is None:
                logger.error(
                    f"Session {session_id} not found",
                    extra={"session_id": session_id, "request_id": request_id},
                )
                return {
                    "status": "failed",
                    "error": f"Session {session_id} not found",
                    "request_id": request_id,
                }

            # 2. Add normalized message to conversation history
            self.session_store.add_message(
                session_id=session_id,
                role=MessageRole.USER,
                content=normalized_message.text,
            )

            logger.debug(
                f"Added user message to session {session_id}",
                extra={"session_id": session_id},
            )

            # 3. Detect workflow_id from message
            workflow_id = self._detect_workflow_id(normalized_message)

            logger.debug(
                f"Detected workflow {workflow_id} from message",
                extra={"workflow_id": workflow_id, "session_id": session_id},
            )

            # 4. Look up workflow from registry
            if self.workflow_service is None:
                from acosplatform.workflows.service import resolve_execution_workflow
                workflow = resolve_execution_workflow(
                    tenant_id=session.context.get("tenant_id", "default"),
                    workflow_family=self._family_from_workflow_id(workflow_id),
                )
            else:
                workflow = self.workflow_service.resolve_execution_workflow(
                    tenant_id=session.context.get("tenant_id", "default"),
                    workflow_family=self._family_from_workflow_id(workflow_id),
                )

            if workflow is None:
                logger.error(
                    f"Workflow {workflow_id} not found in registry",
                    extra={"workflow_id": workflow_id, "session_id": session_id},
                )
                return {
                    "status": "failed",
                    "error": f"Workflow {workflow_id} not found",
                    "request_id": request_id,
                }

            # 5. Enqueue workflow for background execution
            workflow_name = workflow.get("workflow_name", "Unknown")
            tenant_id = session.context.get("tenant_id", "default")

            job = self.job_queue_service.create_job(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                payload={
                    "message": normalized_message.text,
                    "session_id": session_id,
                    "request_id": request_id,
                    "user_id": normalized_message.user_id,
                    "context": session.context,
                },
                tenant_id=tenant_id,
            )

            logger.info(
                f"Workflow {workflow_name} enqueued as job {job.id}",
                extra={
                    "job_id": job.id,
                    "workflow_id": workflow_id,
                    "session_id": session_id,
                    "request_id": request_id,
                },
            )

            # 6. Return job details
            return {
                "status": "queued",
                "job_id": job.id,
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "request_id": request_id,
                "polling_endpoint": f"/api/jobs/{job.id}/status",
                "result_endpoint": f"/api/jobs/{job.id}/result",
                "created_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logger.error(
                f"Async execution failed: {str(e)}",
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
                "created_at": datetime.now(UTC).isoformat(),
            }

    @staticmethod
    def _family_from_workflow_id(workflow_id: str) -> str:
        """Extract workflow family from workflow_id.

        Workflow IDs follow pattern: wf-<family>-<name>
        Examples: wf-discovery, wf-purchase, wf-service

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow family (discovery, purchase, service, etc.)
        """
        parts = workflow_id.split("-")
        if len(parts) >= 2:
            return parts[1]
        return "discovery"
