"""Error handling, retry logic, and fallback strategies for the chat pipeline.

Provides:
1. Custom exception types for chat operations
2. Retry decorator with exponential backoff
3. Fallback strategies for different failure scenarios
4. Error response formatting
"""

import logging
import time
from typing import Callable, Any, Dict, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


# Custom Exceptions
class ChatPipelineError(Exception):
    """Base exception for chat pipeline errors."""

    pass


class SessionNotFoundError(ChatPipelineError):
    """Raised when a session cannot be found or created."""

    pass


class WorkflowNotFoundError(ChatPipelineError):
    """Raised when a workflow definition cannot be found."""

    pass


class WorkflowExecutionError(ChatPipelineError):
    """Raised when workflow execution fails."""

    pass


class JobQueueError(ChatPipelineError):
    """Raised when job queue operation fails."""

    pass


class AdapterError(ChatPipelineError):
    """Raised when message adapter fails."""

    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_multiplier: float = 2.0,
    retriable_exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds (cap for exponential backoff)
        backoff_multiplier: Multiplier for exponential backoff
        retriable_exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay}s: {str(e)}"
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_multiplier, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {str(e)}"
                        )
                        raise

            # Should not reach here, but in case
            raise last_exception or Exception("Unknown error in retry wrapper")

        return wrapper

    return decorator


class FallbackStrategy:
    """Base class for fallback strategies."""

    def should_apply(self, error: Exception) -> bool:
        """Determine if this fallback should be applied."""
        return True

    def execute(self) -> Dict[str, Any]:
        """Execute the fallback and return a response."""
        raise NotImplementedError


class SessionNotFoundFallback(FallbackStrategy):
    """Fallback for missing sessions - create a new one."""

    def __init__(self, session_store: Any, user_id: str, channel_id: str):
        """Initialize fallback.

        Args:
            session_store: SessionStore instance
            user_id: User ID
            channel_id: Channel ID
        """
        self.session_store = session_store
        self.user_id = user_id
        self.channel_id = channel_id

    def should_apply(self, error: Exception) -> bool:
        """Apply when session not found."""
        return isinstance(error, SessionNotFoundError)

    def execute(self) -> Dict[str, Any]:
        """Create new session as fallback."""
        try:
            logger.info(
                f"Creating new session for user {self.user_id} in channel {self.channel_id}"
            )
            session = self.session_store.create_session(
                user_id=self.user_id,
                channel_id=self.channel_id,
            )
            return {
                "status": "recovered",
                "session_id": session.id,
                "recovery_action": "created_new_session",
            }
        except Exception as e:
            logger.error(f"Failed to create fallback session: {str(e)}")
            return {
                "status": "failed",
                "error": "Could not create session",
                "fallback_failed": True,
            }


class WorkflowNotFoundFallback(FallbackStrategy):
    """Fallback for missing workflows - use default discovery workflow."""

    def __init__(self, workflow_id: str):
        """Initialize fallback.

        Args:
            workflow_id: Workflow ID that was not found
        """
        self.workflow_id = workflow_id

    def should_apply(self, error: Exception) -> bool:
        """Apply when workflow not found."""
        return isinstance(error, WorkflowNotFoundError)

    def execute(self) -> Dict[str, Any]:
        """Use default discovery workflow as fallback."""
        logger.warning(f"Workflow {self.workflow_id} not found, using default discovery workflow")
        return {
            "status": "degraded",
            "workflow_id": "wf-discovery",
            "recovery_action": "used_default_workflow",
            "message": "Using default discovery workflow as fallback",
        }


class TimeoutFallback(FallbackStrategy):
    """Fallback for workflow timeout - return partial result."""

    def __init__(self, timeout_seconds: int, partial_result: Optional[str] = None):
        """Initialize fallback.

        Args:
            timeout_seconds: Timeout that was exceeded
            partial_result: Any partial result we had before timeout
        """
        self.timeout_seconds = timeout_seconds
        self.partial_result = partial_result

    def should_apply(self, error: Exception) -> bool:
        """Apply on timeout exceptions."""
        return "timeout" in str(error).lower()

    def execute(self) -> Dict[str, Any]:
        """Return partial result or generic response."""
        logger.warning(f"Workflow timeout after {self.timeout_seconds}s")
        return {
            "status": "timeout",
            "timeout_seconds": self.timeout_seconds,
            "recovery_action": "returned_partial_result",
            "message": self.partial_result
            or "Request took too long. Please try again or simplify your query.",
        }


class GenericFallback(FallbackStrategy):
    """Generic fallback for unexpected errors."""

    def __init__(self, error_context: str = ""):
        """Initialize fallback.

        Args:
            error_context: Context about what was being executed
        """
        self.error_context = error_context

    def should_apply(self, error: Exception) -> bool:
        """Apply on any error."""
        return True

    def execute(self) -> Dict[str, Any]:
        """Return generic error response with guidance."""
        logger.error(f"Generic fallback triggered for: {self.error_context}")
        return {
            "status": "error",
            "recovery_action": "generic_fallback",
            "message": "We encountered an issue processing your request. Please try again or contact support if the problem persists.",
        }


def apply_fallbacks(
    error: Exception,
    fallbacks: list[FallbackStrategy],
) -> Optional[Dict[str, Any]]:
    """Apply fallback strategies in order until one succeeds.

    Args:
        error: The exception that was raised
        fallbacks: List of fallback strategies to try

    Returns:
        Result from first applicable fallback, or None if no fallback applies
    """
    for fallback in fallbacks:
        if fallback.should_apply(error):
            try:
                logger.info(f"Applying fallback: {fallback.__class__.__name__}")
                return fallback.execute()
            except Exception as e:
                logger.error(f"Fallback {fallback.__class__.__name__} failed: {str(e)}")
                continue

    return None


def error_response(
    status: str,
    error: str,
    request_id: Optional[str] = None,
    recovery_suggestions: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """Format an error response.

    Args:
        status: Status code (e.g., "failed", "error")
        error: Error message
        request_id: Request tracking ID
        recovery_suggestions: List of suggested recovery actions

    Returns:
        Formatted error response dict
    """
    response = {
        "status": status,
        "error": error,
    }

    if request_id:
        response["request_id"] = request_id

    if recovery_suggestions:
        response["recovery_suggestions"] = recovery_suggestions

    return response
