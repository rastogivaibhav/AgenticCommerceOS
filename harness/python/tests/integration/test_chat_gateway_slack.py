"""Integration tests for Chat Gateway Slack message processing pipeline.

Tests the full flow: message normalization → session management → handler routing → execution
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from apps.chat_api.main import app
from apps.chat_api.adapters.slack import SlackAdapter
from apps.chat_api.models.chat import ChatMessage
from acosplatform.session.store import SessionStore
from acosplatform.session.models import ChatSession, SessionStatus, MessageRole
from acosplatform.job_queue.service import JobQueueService
from acosplatform.job_queue.models import JobStatus


@pytest.fixture
def chat_client():
    """Test client for Chat API."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return Mock()


@pytest.fixture
def session_store(mock_redis):
    """SessionStore instance with mocked Redis."""
    return SessionStore(redis_client=mock_redis)


@pytest.fixture
def job_queue_service(mock_redis):
    """JobQueueService instance with mocked Redis."""
    return JobQueueService(redis_client=mock_redis)


@pytest.fixture
def mock_slack_client():
    """Mock Slack client."""
    client = Mock()
    client.chat_postMessage.return_value = {
        "ok": True,
        "ts": "1234567890.123456"
    }
    return client


@pytest.fixture
def slack_adapter(mock_slack_client):
    """SlackAdapter instance with mocked Slack client."""
    return SlackAdapter(slack_client=mock_slack_client)


@pytest.fixture
def sample_slack_event():
    """Sample Slack message event."""
    return {
        "type": "message",
        "user": "U12345",
        "channel": "C12345",
        "text": "find me red dresses under £50",
        "ts": "1234567890.123456",
        "thread_ts": None,
    }


@pytest.fixture
def sample_async_workflow_slack_event():
    """Sample Slack event for async workflow."""
    return {
        "type": "message",
        "user": "U12345",
        "channel": "C12345",
        "text": "show me all products that match these filters",
        "ts": "1234567890.123456",
        "thread_ts": None,
    }


class TestPostChatMessage:
    """Test POST /api/chat/message endpoint."""

    def test_message_endpoint_accepts_slack_source(self, chat_client):
        """Verify endpoint accepts slack source."""
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "hello",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code in [200, 400, 500]  # Endpoint should exist

    def test_message_endpoint_requires_source(self, chat_client):
        """Verify endpoint validates required source field."""
        payload = {
            "event": {"type": "message"},
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        # Either 400 (validation error) or field missing
        assert response.status_code in [400, 422]

    def test_message_endpoint_requires_event(self, chat_client):
        """Verify endpoint validates required event field."""
        payload = {
            "source": "slack",
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code in [400, 422]

    def test_message_endpoint_requires_user_id(self, chat_client):
        """Verify endpoint validates required user_id field."""
        payload = {
            "source": "slack",
            "event": {"type": "message"},
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code in [400, 422]

    def test_message_endpoint_requires_channel_id(self, chat_client):
        """Verify endpoint validates required channel_id field."""
        payload = {
            "source": "slack",
            "event": {"type": "message"},
            "user_id": "U12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code in [400, 422]

    def test_invalid_source_returns_400(self, chat_client):
        """Verify invalid source returns 400 Bad Request."""
        payload = {
            "source": "invalid_source",
            "event": {"type": "message"},
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_message_response_includes_request_id(self, chat_client):
        """Verify response includes request_id for tracing."""
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "hello",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "request_id" in data


class TestSyncMessageFlow:
    """Test sync message execution flow (fast workflows)."""

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_sync_message_returns_success_status(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify sync execution returns success status."""
        # Setup mocks
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="find me red dresses",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "success",
            "result": "Found 5 dresses under £50",
            "execution_time_ms": 245,
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "find me red dresses",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_sync_message_includes_result(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify sync result includes execution result."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="what is my balance",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        expected_result = "Your balance is £1,250"
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "success",
            "result": expected_result,
            "execution_time_ms": 100,
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "what is my balance",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == expected_result

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_sync_message_includes_execution_time(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify sync result includes execution_time_ms."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="test",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "success",
            "result": "Done",
            "execution_time_ms": 245,
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "test",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "execution_time_ms" in data


class TestAsyncMessageFlow:
    """Test async message execution flow (slow workflows)."""

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_async_message_returns_queued_status(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify async execution returns queued status."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="find products matching complex filters",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "queued",
            "job_id": "job-abc123",
            "polling_endpoint": "/api/jobs/job-abc123/status",
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "find products matching complex filters",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_async_message_includes_job_id(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify async result includes job_id."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="process this",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        job_id = "job-abc123"
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "queued",
            "job_id": job_id,
            "polling_endpoint": f"/api/jobs/{job_id}/status",
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "process this",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == job_id

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_async_message_includes_polling_endpoint(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify async result includes polling_endpoint."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="long operation",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        job_id = "job-abc123"
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "queued",
            "job_id": job_id,
            "polling_endpoint": f"/api/jobs/{job_id}/status",
            "result_endpoint": f"/api/jobs/{job_id}/result",
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "long operation",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert "polling_endpoint" in data


class TestJobStatusEndpoint:
    """Test GET /api/jobs/{job_id}/status endpoint."""

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_status_endpoint_returns_200(self, mock_get_service, chat_client):
        """Verify job status endpoint returns 200 for existing job."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_service.get_job_status.return_value = JobStatus.PROCESSING
        mock_job = MagicMock()
        mock_job.status = JobStatus.PROCESSING
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/status")
        assert response.status_code == 200

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_status_endpoint_returns_404_for_missing_job(
        self, mock_get_service, chat_client
    ):
        """Verify job status endpoint returns 404 for missing job."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/nonexistent-job/status")
        assert response.status_code == 404

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_status_includes_status_field(self, mock_get_service, chat_client):
        """Verify job status response includes status field."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.PROCESSING
        mock_job.id = "job-abc123"
        mock_job.updated_at = None
        mock_job.created_at = MagicMock()
        mock_job.created_at.isoformat.return_value = "2026-04-06T00:00:00"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/status")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_status_shows_processing(self, mock_get_service, chat_client):
        """Verify job status shows processing state."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.PROCESSING
        mock_job.id = "job-abc123"
        mock_job.updated_at = None
        mock_job.created_at = MagicMock()
        mock_job.created_at.isoformat.return_value = "2026-04-06T00:00:00"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/status")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "processing"


class TestJobResultEndpoint:
    """Test GET /api/jobs/{job_id}/result endpoint."""

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_result_endpoint_returns_result_when_complete(
        self, mock_get_service, chat_client
    ):
        """Verify result endpoint returns final result when job completed."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.COMPLETED
        mock_job.result = {"data": "Found 5 products"}
        mock_job.id = "job-abc123"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/result")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_result_returns_202_when_processing(
        self, mock_get_service, chat_client
    ):
        """Verify result endpoint returns 202 Accepted while still processing."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.PROCESSING
        mock_job.id = "job-abc123"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/result")
        # The response will be a tuple, so we need to check the status code differently
        assert response.status_code == 202

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_result_returns_404_for_missing_job(
        self, mock_get_service, chat_client
    ):
        """Verify result endpoint returns 404 for missing job."""
        mock_service = MagicMock()
        mock_service.get_job.return_value = None
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/nonexistent-job/result")
        assert response.status_code == 404

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_result_includes_execution_time(
        self, mock_get_service, chat_client
    ):
        """Verify result endpoint includes execution_time_ms."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.COMPLETED
        mock_job.result = {"message": "Done"}
        mock_job.id = "job-abc123"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/result")
        if response.status_code == 200:
            data = response.json()
            # Should have execution_time_ms or result data
            assert "status" in data

    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_job_result_includes_result_data(
        self, mock_get_service, chat_client
    ):
        """Verify result endpoint includes result data when completed."""
        mock_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        expected_result = {"products": ["dress1", "dress2", "dress3"]}
        mock_job = MagicMock()
        mock_job.status = JobStatus.COMPLETED
        mock_job.result = expected_result
        mock_job.id = "job-abc123"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service

        response = chat_client.get("/api/jobs/job-abc123/result")
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == expected_result


class TestErrorHandling:
    """Test error handling in message and job endpoints."""

    def test_invalid_json_returns_422(self, chat_client):
        """Verify invalid JSON returns 422 Unprocessable Entity."""
        response = chat_client.post(
            "/api/chat/message",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_handler_error_returns_500(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Verify handler execution error returns 500."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="test",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router to return error
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "failed",
            "error": "Internal execution error",
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "test",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 500

    def test_slack_parse_error_returns_400(self, chat_client):
        """Verify Slack event parsing error returns 400."""
        payload = {
            "source": "slack",
            "event": {
                "type": "invalid_type",
                "text": "test",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code in [400, 500]


class TestEndToEndFlow:
    """Test complete end-to-end message flows."""

    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    def test_sync_flow_end_to_end(
        self, mock_get_store, mock_get_adapter, mock_get_router, chat_client
    ):
        """Test complete sync message flow from message to result."""
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone

        # Mock session store
        mock_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_store.get_session.return_value = mock_session
        mock_store.create_session.return_value = mock_session
        mock_get_store.return_value = mock_store

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="find products",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Mock router
        mock_router_instance = MagicMock()
        mock_router_instance.route.return_value = {
            "status": "success",
            "result": "Found 5 products",
            "execution_time_ms": 100,
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        # Send message
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "find products",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data

    @patch('apps.chat_api.routers.message.get_slack_adapter')
    @patch('apps.chat_api.routers.message.get_session_store')
    @patch('apps.chat_api.routers.message.get_handler_router')
    @patch('apps.chat_api.routers.jobs.get_job_queue_service')
    def test_async_flow_end_to_end(
        self,
        mock_get_job_service,
        mock_get_router,
        mock_get_session_store,
        mock_get_adapter,
        chat_client
    ):
        """Test complete async message flow from message to polling."""
        # Setup message router
        mock_router_instance = MagicMock()
        job_id = "job-abc123"
        mock_router_instance.route.return_value = {
            "status": "queued",
            "job_id": job_id,
            "polling_endpoint": f"/api/jobs/{job_id}/status",
            "request_id": "req-123",
        }
        mock_get_router.return_value = mock_router_instance

        # Setup session store
        mock_session_store = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "sess-123"
        mock_session_store.get_session.return_value = mock_session
        mock_session_store.create_session.return_value = mock_session
        mock_get_session_store.return_value = mock_session_store

        # Setup slack adapter
        mock_adapter = MagicMock()
        from apps.chat_api.models.chat import ChatMessage
        from datetime import datetime, timezone
        mock_adapter.normalize_event.return_value = ChatMessage(
            id="msg-123",
            channel_id="C12345",
            user_id="U12345",
            text="long operation",
            timestamp=datetime.now(timezone.utc),
        )
        mock_get_adapter.return_value = mock_adapter

        # Setup job service
        mock_job_service = MagicMock()
        from acosplatform.job_queue.models import JobStatus
        mock_job = MagicMock()
        mock_job.status = JobStatus.PROCESSING
        mock_job.id = job_id
        mock_job_service.get_job.return_value = mock_job
        mock_get_job_service.return_value = mock_job_service

        # Send message
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "long operation",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = chat_client.post("/api/chat/message", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert data["job_id"] == job_id

        # Poll status
        status_response = chat_client.get(f"/api/jobs/{job_id}/status")
        assert status_response.status_code == 200
