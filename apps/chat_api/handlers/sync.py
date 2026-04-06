"""Synchronous workflow handler for fast operations in the chat pipeline.

Executes workflows inline for operations that complete within 2 seconds.
Receives normalized chat messages from the Slack adapter and returns
results directly without background processing.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from apps.chat_api.models.chat import ChatMessage
from apps.chat_api.handlers.base import BaseHandler
from acosplatform.session.store import SessionStore
from acosplatform.session.models import MessageRole

logger = logging.getLogger(__name__)


class SyncHandler(BaseHandler):
    """Synchronous workflow handler for the chat pipeline.

    Executes workflows inline and returns results directly.
    Used for simple operations like lookups and status queries
    that complete within 2 seconds.

    Handles:
    - Message retrieval from SessionStore
    - Adding messages to conversation history
    - Workflow detection from message content
    - Workflow execution (inline)
    - Result serialization
    """

    def __init__(
        self,
        session_store: SessionStore,
        workflow_service: Any = None,  # Injected dependency
    ):
        """Initialize SyncHandler.

        Args:
            session_store: SessionStore instance for managing conversation state
            workflow_service: WorkflowService instance for workflow lookup.
                             If None, will be imported lazily.
        """
        super().__init__(session_store)
        self.workflow_service = workflow_service

    def execute(
        self,
        normalized_message: ChatMessage,
        session_id: str,
        request_id: str,
    ) -> Dict[str, Any]:
        """Execute workflow synchronously from a chat message.

        Flow:
        1. Get session from SessionStore
        2. Add normalized_message to conversation history
        3. Detect workflow_id from message
        4. Look up workflow definition from registry
        5. Execute workflow inline
        6. Return result dict

        Args:
            normalized_message: Normalized ChatMessage from SlackAdapter
            session_id: Conversation session ID
            request_id: Request tracking ID

        Returns:
            Dict with status, result, and execution metadata
        """
        start_time = time.time()

        try:
            logger.info(
                f"SyncHandler: Executing workflow from message in session {session_id}",
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

            # 5. Execute workflow inline
            timeout_seconds = workflow.get("timeout_seconds", 2)
            result = self._execute_workflow(
                workflow=workflow,
                message_text=normalized_message.text,
                session_context=session.context,
                timeout_seconds=timeout_seconds,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Sync execution completed in {elapsed_ms}ms",
                extra={
                    "session_id": session_id,
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "execution_time_ms": elapsed_ms,
                },
            )

            # 6. Return result
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "result": result,
                "execution_time_ms": elapsed_ms,
                "request_id": request_id,
                "executed_at": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Sync execution failed: {str(e)}",
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
                "execution_time_ms": elapsed_ms,
                "executed_at": datetime.now(UTC).isoformat(),
            }

    def _execute_workflow(
        self,
        workflow: Dict[str, Any],
        message_text: str,
        session_context: Dict[str, Any],
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        """Execute workflow steps synchronously.

        In the current implementation, this returns a mock result.
        In production, this would call actual agents via MCP.

        Args:
            workflow: Workflow definition from registry
            message_text: Original message text from user
            session_context: Session context data
            timeout_seconds: Execution timeout in seconds

        Returns:
            Workflow execution result dict
        """
        workflow_id = workflow.get("workflow_id", "unknown")
        steps = workflow.get("steps", [])

        logger.debug(
            f"Executing {len(steps)} steps for workflow {workflow_id}",
            extra={"workflow_id": workflow_id, "timeout_seconds": timeout_seconds},
        )

        results = {}

        # Execute each step in sequence
        for step in steps:
            step_id = step.get("step_id", "step_unknown")
            agent = step.get("agent", "unknown_agent")

            logger.debug(
                f"Executing step {step_id} with agent {agent}",
                extra={"workflow_id": workflow_id, "step_id": step_id},
            )

            # In production, dispatch to actual agent via MCP
            # For now, return mock result
            step_result = {
                "agent": agent,
                "status": "completed",
                "output": {
                    "message": f"Executed {agent} with message: {message_text}",
                    "context": session_context,
                },
            }

            results[step_id] = step_result

        return {
            "workflow_steps": results,
            "total_steps": len(steps),
            "message": f"Workflow {workflow_id} completed successfully",
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
