"""Tests for workflow execution handlers (Task 5).

Tests the chat pipeline integration with message handlers.
Handlers receive normalized ChatMessage objects, session_id, and request_id.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, MagicMock, patch, call
import uuid

from apps.chat_api.handlers.base import BaseHandler
from apps.chat_api.handlers.sync import SyncHandler
from apps.chat_api.handlers.async_handler import AsyncHandler
from apps.chat_api.handlers.router import HandlerRouter
from apps.chat_api.models.chat import ChatMessage
from acosplatform.session.models import ChatSession, MessageRole
from acosplatform.job_queue.models import Job, JobStatus


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def normalized_message():
    """Normalized message from SlackAdapter."""
    return ChatMessage(
        id="1234567890.000001",
        channel_id="C123ABC",
        user_id="U456DEF",
        text="show me blue dresses",
        timestamp=datetime.now(UTC),
        thread_ts=None,
        reactions=None,
    )


@pytest.fixture
def session_id():
    """Session identifier."""
    return "sess_test_" + str(uuid.uuid4())


@pytest.fixture
def request_id():
    """Request tracking identifier."""
    return "req_test_" + str(uuid.uuid4())


@pytest.fixture
def mock_workflow():
    """Mock workflow from registry."""
    return {
        "workflow_id": "wf-discovery",
        "workflow_name": "Discovery Concierge",
        "timeout_seconds": 2,
        "steps": [
            {
                "step_id": "step_1",
                "agent": "search_agent",
                "input": {},
            }
        ],
    }


@pytest.fixture
def mock_workflow_long_running():
    """Mock long-running workflow."""
    return {
        "workflow_id": "wf-complex",
        "workflow_name": "Complex Analysis",
        "timeout_seconds": 30,
        "steps": [
            {
                "step_id": "step_1",
                "agent": "analysis_agent",
                "input": {},
            }
        ],
    }


@pytest.fixture
def mock_chat_session():
    """Mock chat session."""
    session = ChatSession(
        user_id="U456DEF",
    )
    return session


@pytest.fixture
def mock_session_store():
    """Mock SessionStore."""
    store = Mock()
    store.get_session = Mock()
    store.add_message = Mock()
    store.update_context = Mock()
    return store


@pytest.fixture
def mock_workflow_service():
    """Mock WorkflowService."""
    service = Mock()
    return service


@pytest.fixture
def mock_job_queue_service():
    """Mock JobQueueService."""
    return Mock()


# ============================================================================
# Test BaseHandler
# ============================================================================


class TestBaseHandler:
    """Test abstract base handler."""

    def test_base_handler_is_abstract(self):
        """BaseHandler should be abstract and not instantiable."""
        with pytest.raises(TypeError):
            BaseHandler(session_store=Mock())

    def test_base_handler_defines_execute_signature(self):
        """BaseHandler should define execute method signature."""
        # Verify the method exists in the class
        assert hasattr(BaseHandler, 'execute')


# ============================================================================
# Test SyncHandler
# ============================================================================


class TestSyncHandler:
    """Test synchronous workflow handler."""

    @pytest.fixture
    def sync_handler(self, mock_session_store, mock_workflow_service):
        """Create SyncHandler instance."""
        return SyncHandler(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
        )

    def test_sync_handler_init(self, sync_handler):
        """Test SyncHandler initialization."""
        assert sync_handler is not None
        assert sync_handler.session_store is not None
        assert sync_handler.workflow_service is not None

    def test_execute_requires_normalized_message(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute accepts normalized ChatMessage, session_id, request_id."""
        # Setup mocks
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # When calling execute with correct signature
        result = sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Then result should be dict
        assert isinstance(result, dict)
        assert "status" in result

    def test_execute_gets_session(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute retrieves session from SessionStore."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        mock_session_store.get_session.assert_called_with(session_id)

    def test_execute_adds_message_to_session(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute adds normalized_message to conversation history."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify message was added
        mock_session_store.add_message.assert_called_once()
        call_kwargs = mock_session_store.add_message.call_args.kwargs
        assert call_kwargs.get("session_id") == session_id

    def test_execute_detects_workflow_from_message(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute detects workflow_id from normalized_message."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify workflow was resolved
        sync_handler.workflow_service.resolve_execution_workflow.assert_called_once()

    def test_execute_returns_dict_with_status(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute returns dict with status field."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        result = sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ("success", "failed")

    def test_execute_includes_result_on_success(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute includes result in response on success."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        result = sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert "result" in result or "error" in result
        if result["status"] == "success":
            assert "result" in result

    def test_execute_includes_execution_time(
        self, sync_handler, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Execute includes execution time in result."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        sync_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute
        result = sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert "execution_time_ms" in result


# ============================================================================
# Test AsyncHandler
# ============================================================================


class TestAsyncHandler:
    """Test asynchronous workflow handler."""

    @pytest.fixture
    def async_handler(self, mock_session_store, mock_workflow_service, mock_job_queue_service):
        """Create AsyncHandler instance."""
        return AsyncHandler(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
            job_queue_service=mock_job_queue_service,
        )

    def test_async_handler_init(self, async_handler):
        """Test AsyncHandler initialization."""
        assert async_handler is not None
        assert async_handler.session_store is not None
        assert async_handler.workflow_service is not None
        assert async_handler.job_queue_service is not None

    def test_execute_requires_normalized_message(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute accepts normalized ChatMessage, session_id, request_id."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        result = async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert isinstance(result, dict)
        assert "status" in result

    def test_execute_gets_session(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute retrieves session from SessionStore."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        mock_session_store.get_session.assert_called_with(session_id)

    def test_execute_adds_message_to_session(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute adds normalized_message to conversation history."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        mock_session_store.add_message.assert_called_once()

    def test_execute_returns_job_id(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute returns dict with job_id."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_abc_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        result = async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert "job_id" in result
        assert result["job_id"] == "job_abc_123"

    def test_execute_returns_status_queued(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute returns status: queued for async operations."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        result = async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert result["status"] == "queued"

    def test_execute_includes_polling_endpoint(
        self, async_handler, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store, mock_job_queue_service
    ):
        """Execute includes polling endpoint in response."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session
        async_handler.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_job = Mock(spec=Job)
        mock_job.id = "job_test_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Execute
        result = async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify
        assert "polling_endpoint" in result


# ============================================================================
# Test HandlerRouter
# ============================================================================


class TestHandlerRouter:
    """Test routing logic between sync and async handlers."""

    @pytest.fixture
    def router(self, mock_session_store, mock_workflow_service, mock_job_queue_service):
        """Create HandlerRouter instance."""
        return HandlerRouter(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
            job_queue_service=mock_job_queue_service,
        )

    def test_router_init(self, router):
        """Test HandlerRouter initialization."""
        assert router is not None
        assert router.sync_handler is not None
        assert router.async_handler is not None

    def test_router_uses_sync_for_fast_workflows(
        self, router, normalized_message, session_id, request_id, mock_workflow, mock_chat_session, mock_session_store
    ):
        """Router uses SyncHandler for workflows with timeout <= 2 seconds."""
        # Setup: fast workflow (timeout = 2)
        mock_session_store.get_session.return_value = mock_chat_session
        router.workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Router should use sync handler
        with patch.object(router.sync_handler, 'execute', return_value={"status": "success"}) as mock_sync:
            router.route(
                normalized_message=normalized_message,
                session_id=session_id,
                request_id=request_id,
            )
            mock_sync.assert_called_once()

    def test_router_uses_async_for_slow_workflows(
        self, router, normalized_message, session_id, request_id, mock_workflow_long_running, mock_chat_session, mock_session_store
    ):
        """Router uses AsyncHandler for workflows with timeout > 2 seconds."""
        # Setup: slow workflow (timeout = 30)
        mock_session_store.get_session.return_value = mock_chat_session
        router.workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running

        # Router should use async handler
        with patch.object(router.async_handler, 'execute', return_value={"status": "queued", "job_id": "job_123"}) as mock_async:
            router.route(
                normalized_message=normalized_message,
                session_id=session_id,
                request_id=request_id,
            )
            mock_async.assert_called_once()

    def test_router_threshold_is_2_seconds(self, router):
        """Router threshold for sync vs async is 2 seconds."""
        assert hasattr(router, 'SYNC_THRESHOLD_SECONDS')
        assert router.SYNC_THRESHOLD_SECONDS == 2

    def test_router_respects_workflow_timeout(
        self, router, normalized_message, session_id, request_id, mock_chat_session, mock_session_store
    ):
        """Router respects timeout_seconds from workflow definition."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session

        # Test with exactly 2 seconds (should use sync)
        workflow_2s = {
            "workflow_id": "wf-test",
            "workflow_name": "Test",
            "timeout_seconds": 2,
            "steps": [],
        }
        router.workflow_service.resolve_execution_workflow.return_value = workflow_2s

        with patch.object(router.sync_handler, 'execute', return_value={"status": "success"}) as mock_sync:
            router.route(
                normalized_message=normalized_message,
                session_id=session_id,
                request_id=request_id,
            )
            mock_sync.assert_called_once()


# ============================================================================
# Integration Tests
# ============================================================================


class TestHandlerIntegration:
    """Integration tests for handlers working together."""

    def test_sync_and_async_handlers_both_accept_message_signature(
        self, mock_session_store, mock_workflow_service, mock_job_queue_service, normalized_message, session_id, request_id, mock_workflow, mock_workflow_long_running, mock_chat_session
    ):
        """Both handlers accept (normalized_message, session_id, request_id) signature."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session

        sync_handler = SyncHandler(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
        )
        async_handler = AsyncHandler(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
            job_queue_service=mock_job_queue_service,
        )

        # Setup workflow service
        mock_workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Mock job service
        mock_job = Mock(spec=Job)
        mock_job.id = "job_123"
        mock_job_queue_service.create_job.return_value = mock_job

        # Both should accept the same signature
        sync_result = sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Reset mocks
        mock_session_store.reset_mock()
        mock_workflow_service.resolve_execution_workflow.return_value = mock_workflow_long_running
        mock_session_store.get_session.return_value = mock_chat_session

        async_result = async_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        assert isinstance(sync_result, dict)
        assert isinstance(async_result, dict)

    def test_handler_workflow_detection_from_message_content(
        self, mock_session_store, mock_workflow_service, normalized_message, session_id, request_id, mock_workflow, mock_chat_session
    ):
        """Handlers detect workflow from message content or intent."""
        # Setup
        mock_session_store.get_session.return_value = mock_chat_session

        sync_handler = SyncHandler(
            session_store=mock_session_store,
            workflow_service=mock_workflow_service,
        )

        mock_workflow_service.resolve_execution_workflow.return_value = mock_workflow

        # Execute with normalized message
        sync_handler.execute(
            normalized_message=normalized_message,
            session_id=session_id,
            request_id=request_id,
        )

        # Verify workflow service was called to resolve workflow
        mock_workflow_service.resolve_execution_workflow.assert_called()
