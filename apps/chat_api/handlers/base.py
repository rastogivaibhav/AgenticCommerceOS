"""Abstract base handler for workflow execution in the chat pipeline.

Handlers are message processors that receive normalized chat messages from
the Slack adapter and execute appropriate workflows based on the message content.

Handlers must implement the execute method with the signature:
    execute(normalized_message: ChatMessage, session_id: str, request_id: str) -> Dict[str, Any]
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from apps.chat_api.models.chat import ChatMessage
from acosplatform.session.store import SessionStore

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Abstract base class for workflow handlers in the chat pipeline.

    Handlers are responsible for:
    1. Receiving normalized ChatMessage objects from the Slack adapter
    2. Retrieving conversation context from SessionStore
    3. Adding messages to conversation history
    4. Detecting workflow_id from message content
    5. Executing the appropriate workflow (sync or async)
    6. Returning results as dicts (not Job objects)
    """

    def __init__(self, session_store: SessionStore):
        """Initialize BaseHandler.

        Args:
            session_store: SessionStore instance for managing conversation state
        """
        self.session_store = session_store

    @abstractmethod
    def execute(
        self,
        normalized_message: ChatMessage,
        session_id: str,
        request_id: str,
    ) -> Dict[str, Any]:
        """Execute workflow based on normalized chat message.

        This is the main entry point for the handler. It:
        1. Retrieves session from SessionStore using session_id
        2. Adds the normalized_message to conversation history
        3. Detects workflow_id from message content
        4. Looks up workflow definition from registry
        5. Executes the workflow
        6. Returns result as dict

        Args:
            normalized_message: Normalized ChatMessage from adapter (e.g., SlackAdapter)
            session_id: Conversation session identifier (format: sess_<uuid>)
            request_id: Request tracking identifier (format: req_<uuid>)

        Returns:
            Dict with status, result/job_id, and metadata.
            - Sync result: {"status": "success", "result": {...}, "execution_time_ms": ...}
            - Async result: {"status": "queued", "job_id": "...", "polling_endpoint": "..."}
            - Error: {"status": "failed", "error": "...", "request_id": "..."}
        """
        pass

    def _detect_workflow_id(self, normalized_message: ChatMessage) -> str:
        """Detect workflow_id from message content.

        This is a hook method that subclasses can override to implement
        custom workflow detection logic.

        Default implementation extracts workflow family from message text
        and returns a workflow_id. In production, this could use NLU/intent
        detection.

        Args:
            normalized_message: Normalized chat message

        Returns:
            Workflow identifier (e.g., "wf-discovery", "wf-purchase")
        """
        # Default: extract from message text or use discovery as default
        text = normalized_message.text.lower()

        # Simple keyword-based detection
        # Account workflows
        if any(word in text for word in ["balance", "account", "loyalty", "points", "settings", "password"]):
            return "wf-account"
        # Support workflows (covers returns, issues, shipping, damaged items)
        elif any(word in text for word in ["return", "refund", "exchange", "issue", "problem", "help", "damaged", "broken", "shipping", "delivery"]):
            return "wf-support"
        # Purchase workflows
        elif any(word in text for word in ["buy", "purchase", "checkout", "cart"]):
            return "wf-purchase"
        # Post-purchase workflows
        elif any(word in text for word in ["order", "status", "tracking", "shipped"]):
            return "wf-post-purchase"
        # Engagement workflows
        elif any(word in text for word in ["feedback", "review", "rate", "referral", "recommend"]):
            return "wf-engagement"
        else:
            # Default to discovery
            return "wf-discovery"
