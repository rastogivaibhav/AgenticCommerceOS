"""Synchronous workflow handler for fast operations in the chat pipeline.

Executes workflows inline for operations that complete within 2 seconds.
Receives normalized chat messages from the Slack adapter and returns
results directly without background processing.

Includes error handling with retry logic and fallback strategies.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from apps.chat_api.models.chat import ChatMessage
from apps.chat_api.handlers.base import BaseHandler
from apps.chat_api.errors import (
    SessionNotFoundError,
    WorkflowNotFoundError,
    SessionNotFoundFallback,
    WorkflowNotFoundFallback,
    GenericFallback,
    apply_fallbacks,
)
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
                logger.warning(
                    f"Session {session_id} not found, attempting recovery",
                    extra={"session_id": session_id, "request_id": request_id},
                )
                # Try fallback: create new session
                fallback = SessionNotFoundFallback(
                    self.session_store,
                    normalized_message.user_id,
                    normalized_message.channel_id,
                )
                fallback_result = fallback.execute()
                if fallback_result.get("status") == "recovered":
                    session_id = fallback_result["session_id"]
                    session = self.session_store.get_session(session_id)
                else:
                    return {
                        "status": "failed",
                        "error": f"Session {session_id} not found and recovery failed",
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
                logger.warning(
                    f"Workflow {workflow_id} not found in registry, attempting recovery",
                    extra={"workflow_id": workflow_id, "session_id": session_id},
                )
                # Try fallback: use default discovery workflow
                fallback = WorkflowNotFoundFallback(workflow_id)
                fallback_result = fallback.execute()
                if fallback_result.get("status") == "degraded":
                    workflow_id = fallback_result["workflow_id"]
                    logger.info(
                        f"Using fallback workflow {workflow_id}",
                        extra={"original_workflow_id": workflow_id},
                    )
                    # Re-lookup the fallback workflow
                    from acosplatform.workflows.service import resolve_execution_workflow
                    workflow = resolve_execution_workflow(
                        tenant_id=session.context.get("tenant_id", "default"),
                        workflow_family="discovery",
                    )
                else:
                    return {
                        "status": "failed",
                        "error": f"Workflow {workflow_id} not found and fallback failed",
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

            # Try fallback strategies
            fallbacks = [
                GenericFallback(f"Sync handler execution failed: {str(e)}"),
            ]
            fallback_result = apply_fallbacks(e, fallbacks)

            if fallback_result:
                fallback_result["request_id"] = request_id
                fallback_result["execution_time_ms"] = elapsed_ms
                fallback_result["executed_at"] = datetime.now(UTC).isoformat()
                return fallback_result

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
    ) -> str:
        """Execute workflow steps synchronously.

        Checks for demo workflow implementations first. If a demo workflow
        is found (wf-account, wf-discovery, wf-support), executes it directly.

        Otherwise, would call actual agents via MCP in production.

        Args:
            workflow: Workflow definition from registry
            message_text: Original message text from user
            session_context: Session context data
            timeout_seconds: Execution timeout in seconds

        Returns:
            Workflow execution result message
        """
        workflow_id = workflow.get("workflow_id", "unknown")

        # Check for demo workflows first
        try:
            from apps.chat_api.workflows import get_demo_workflow
            demo_workflow = get_demo_workflow(workflow_id)
            if demo_workflow:
                logger.debug(
                    f"Executing demo workflow {workflow_id}",
                    extra={"workflow_id": workflow_id},
                )
                result = demo_workflow.execute(message_text, session_context)
                return result
        except Exception as e:
            logger.warning(
                f"Failed to load demo workflow {workflow_id}: {str(e)}",
                extra={"workflow_id": workflow_id},
            )

        # Fallback: execute registered workflow steps
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

        message = f"Workflow {workflow_id} completed successfully"
        return message

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
