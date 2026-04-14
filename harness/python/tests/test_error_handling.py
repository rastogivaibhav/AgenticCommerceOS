"""Tests for error handling, retry logic, and fallback strategies."""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from apps.chat_api.errors import (
    ChatPipelineError,
    SessionNotFoundError,
    WorkflowNotFoundError,
    WorkflowExecutionError,
    JobQueueError,
    AdapterError,
    retry_with_exponential_backoff,
    SessionNotFoundFallback,
    WorkflowNotFoundFallback,
    TimeoutFallback,
    GenericFallback,
    apply_fallbacks,
    error_response,
)


class TestCustomExceptions:
    """Test custom exception types."""

    def test_session_not_found_error(self):
        """Test SessionNotFoundError."""
        with pytest.raises(SessionNotFoundError):
            raise SessionNotFoundError("Session not found")

    def test_workflow_not_found_error(self):
        """Test WorkflowNotFoundError."""
        with pytest.raises(WorkflowNotFoundError):
            raise WorkflowNotFoundError("Workflow not found")

    def test_workflow_execution_error(self):
        """Test WorkflowExecutionError."""
        with pytest.raises(WorkflowExecutionError):
            raise WorkflowExecutionError("Execution failed")

    def test_job_queue_error(self):
        """Test JobQueueError."""
        with pytest.raises(JobQueueError):
            raise JobQueueError("Queue error")

    def test_adapter_error(self):
        """Test AdapterError."""
        with pytest.raises(AdapterError):
            raise AdapterError("Adapter error")

    def test_all_inherit_from_base(self):
        """Test all custom exceptions inherit from ChatPipelineError."""
        assert issubclass(SessionNotFoundError, ChatPipelineError)
        assert issubclass(WorkflowNotFoundError, ChatPipelineError)
        assert issubclass(WorkflowExecutionError, ChatPipelineError)
        assert issubclass(JobQueueError, ChatPipelineError)
        assert issubclass(AdapterError, ChatPipelineError)


class TestRetryDecorator:
    """Test retry with exponential backoff decorator."""

    def test_success_on_first_try(self):
        """Test function succeeds on first attempt."""

        @retry_with_exponential_backoff(max_retries=2)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_retry_on_failure(self):
        """Test function retries on failure and succeeds."""
        call_count = 0

        @retry_with_exponential_backoff(
            max_retries=2,
            base_delay=0.01,
            retriable_exceptions=(ValueError,),
        )
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_max_retries_exceeded(self):
        """Test exception raised when max retries exceeded."""

        @retry_with_exponential_backoff(
            max_retries=1,
            base_delay=0.01,
            retriable_exceptions=(ValueError,),
        )
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_non_retriable_exception_not_retried(self):
        """Test non-retriable exceptions are not retried."""
        call_count = 0

        @retry_with_exponential_backoff(
            max_retries=2,
            base_delay=0.01,
            retriable_exceptions=(ValueError,),
        )
        def func_with_runtime_error():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Not retriable")

        with pytest.raises(RuntimeError):
            func_with_runtime_error()

        # Should only be called once (no retry)
        assert call_count == 1

    def test_exponential_backoff_timing(self):
        """Test exponential backoff delays increase."""
        call_count = 0
        call_times = []

        @retry_with_exponential_backoff(
            max_retries=2,
            base_delay=0.01,
            backoff_multiplier=2.0,
            retriable_exceptions=(ValueError,),
        )
        def timed_failures():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise ValueError("Retry")
            return "success"

        result = timed_failures()
        assert result == "success"
        assert len(call_times) == 3

        # Check delays increase (second delay > first delay)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 >= delay1  # Exponential backoff


class TestSessionNotFoundFallback:
    """Test SessionNotFoundFallback strategy."""

    def test_creates_new_session(self):
        """Test fallback creates a new session."""
        mock_store = Mock()
        mock_session = MagicMock()
        mock_session.id = "sess_new_123"
        mock_store.create_session.return_value = mock_session

        fallback = SessionNotFoundFallback(
            mock_store,
            user_id="U123",
            channel_id="C456",
        )

        result = fallback.execute()

        assert result["status"] == "recovered"
        assert result["session_id"] == "sess_new_123"
        assert result["recovery_action"] == "created_new_session"
        mock_store.create_session.assert_called_once()

    def test_applies_to_session_not_found(self):
        """Test fallback applies to SessionNotFoundError."""
        fallback = SessionNotFoundFallback(Mock(), "U123", "C456")
        assert fallback.should_apply(SessionNotFoundError("test"))

    def test_does_not_apply_to_other_errors(self):
        """Test fallback doesn't apply to other errors."""
        fallback = SessionNotFoundFallback(Mock(), "U123", "C456")
        assert not fallback.should_apply(WorkflowNotFoundError("test"))

    def test_handles_creation_failure(self):
        """Test fallback handles session creation failure."""
        mock_store = Mock()
        mock_store.create_session.side_effect = Exception("DB error")

        fallback = SessionNotFoundFallback(
            mock_store,
            user_id="U123",
            channel_id="C456",
        )

        result = fallback.execute()

        assert result["status"] == "failed"
        assert result["fallback_failed"] is True


class TestWorkflowNotFoundFallback:
    """Test WorkflowNotFoundFallback strategy."""

    def test_uses_default_discovery_workflow(self):
        """Test fallback uses default discovery workflow."""
        fallback = WorkflowNotFoundFallback("wf-unknown")
        result = fallback.execute()

        assert result["status"] == "degraded"
        assert result["workflow_id"] == "wf-discovery"
        assert result["recovery_action"] == "used_default_workflow"

    def test_applies_to_workflow_not_found(self):
        """Test fallback applies to WorkflowNotFoundError."""
        fallback = WorkflowNotFoundFallback("wf-test")
        assert fallback.should_apply(WorkflowNotFoundError("test"))

    def test_does_not_apply_to_other_errors(self):
        """Test fallback doesn't apply to other errors."""
        fallback = WorkflowNotFoundFallback("wf-test")
        assert not fallback.should_apply(SessionNotFoundError("test"))


class TestTimeoutFallback:
    """Test TimeoutFallback strategy."""

    def test_returns_partial_result(self):
        """Test fallback returns partial result on timeout."""
        fallback = TimeoutFallback(
            timeout_seconds=5,
            partial_result="Found 3 items before timeout",
        )

        result = fallback.execute()

        assert result["status"] == "timeout"
        assert result["timeout_seconds"] == 5
        assert "Found 3 items before timeout" in result["message"]

    def test_returns_generic_message_if_no_partial(self):
        """Test fallback returns generic message if no partial result."""
        fallback = TimeoutFallback(timeout_seconds=5)
        result = fallback.execute()

        assert result["status"] == "timeout"
        assert "took too long" in result["message"].lower()

    def test_applies_to_timeout_errors(self):
        """Test fallback applies to timeout exceptions."""
        fallback = TimeoutFallback(5)
        assert fallback.should_apply(Exception("Request timeout"))
        assert fallback.should_apply(Exception("Operation timeout"))


class TestGenericFallback:
    """Test GenericFallback strategy."""

    def test_applies_to_any_error(self):
        """Test generic fallback applies to any error."""
        fallback = GenericFallback("Context message")
        assert fallback.should_apply(Exception("Any error"))
        assert fallback.should_apply(ValueError("Another error"))

    def test_returns_generic_message(self):
        """Test fallback returns helpful generic message."""
        fallback = GenericFallback("Executing workflow")
        result = fallback.execute()

        assert result["status"] == "error"
        assert result["recovery_action"] == "generic_fallback"
        assert "contact support" in result["message"].lower()


class TestApplyFallbacks:
    """Test apply_fallbacks function."""

    def test_applies_first_matching_fallback(self):
        """Test apply_fallbacks uses first matching fallback."""
        fallback1 = WorkflowNotFoundFallback("wf-test")
        fallback2 = GenericFallback()

        error = WorkflowNotFoundError("test")
        result = apply_fallbacks(error, [fallback1, fallback2])

        assert result["status"] == "degraded"
        assert result["workflow_id"] == "wf-discovery"

    def test_tries_next_fallback_if_first_fails(self):
        """Test apply_fallbacks tries next fallback if first fails."""

        class FailingFallback:
            def should_apply(self, error):
                return True

            def execute(self):
                raise Exception("Fallback failed")

        fallback1 = FailingFallback()
        fallback2 = GenericFallback()

        result = apply_fallbacks(Exception("test"), [fallback1, fallback2])

        # Should use second fallback since first raised exception
        assert result["status"] == "error"

    def test_returns_none_if_no_applicable_fallback(self):
        """Test apply_fallbacks returns None if no applicable fallback."""

        class NeverApplies:
            def should_apply(self, error):
                return False

            def execute(self):
                return {"status": "never"}

        result = apply_fallbacks(Exception("test"), [NeverApplies()])
        assert result is None


class TestErrorResponse:
    """Test error_response helper function."""

    def test_basic_error_response(self):
        """Test basic error response."""
        response = error_response("failed", "Something went wrong")

        assert response["status"] == "failed"
        assert response["error"] == "Something went wrong"
        assert "request_id" not in response

    def test_error_response_with_request_id(self):
        """Test error response with request ID."""
        response = error_response(
            "failed",
            "Error occurred",
            request_id="req_123",
        )

        assert response["request_id"] == "req_123"

    def test_error_response_with_suggestions(self):
        """Test error response with recovery suggestions."""
        suggestions = [
            "Retry the operation",
            "Contact support",
        ]
        response = error_response(
            "failed",
            "Error",
            recovery_suggestions=suggestions,
        )

        assert response["recovery_suggestions"] == suggestions
