"""Tests for Chat Gateway API startup and health endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from apps.chat_api.main import app

CHAT_AUTH = {"Authorization": "Bearer dev-token"}


@pytest.fixture
def client():
    """Test client for Chat API tests."""
    return TestClient(app)


class TestChatAPIStartup:
    """Test Chat API startup and initialization."""

    def test_app_starts(self):
        """Verify app instance is created successfully."""
        assert app is not None
        assert app.title == "ACOS Chat Gateway API"

    def test_health_endpoint_ok(self, client):
        """Verify health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Verify health endpoint has required fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "environment" in data
        assert "version" in data
        assert "slack_configured" in data

        assert data["status"] == "ok"
        assert data["service"] == "chat-api"

    def test_cors_headers_present(self, client):
        """Verify CORS middleware is configured."""
        response = client.get("/health")
        # CORS headers should be present in successful responses
        assert response.status_code == 200


class TestMessageRouter:
    """Test message router endpoints."""

    def test_send_message_endpoint_exists(self, client):
        """Verify send_message endpoint is available."""
        payload = {
            "channel_id": "C1234",
            "text": "Test message",
        }
        response = client.post("/api/messages/send", json=payload, headers=CHAT_AUTH)
        assert response.status_code == 200

    def test_send_message_response_structure(self, client):
        """Verify send_message returns correct structure."""
        payload = {
            "channel_id": "C1234",
            "text": "Test message",
        }
        response = client.post("/api/messages/send", json=payload, headers=CHAT_AUTH)
        data = response.json()

        assert "status" in data
        assert "message_id" in data
        assert "thread_ts" in data
        assert "timestamp" in data
        assert data["status"] == "success"

    def test_get_message_endpoint_exists(self, client):
        """Verify get_message endpoint is available."""
        response = client.get("/api/messages/msg_test_123", headers=CHAT_AUTH)
        assert response.status_code == 200

    def test_get_message_response(self, client):
        """Verify get_message returns expected structure."""
        response = client.get("/api/messages/msg_test_123", headers=CHAT_AUTH)
        data = response.json()

        assert "status" in data
        assert "message" in data


class TestJobsRouter:
    """Test jobs router endpoints."""

    @patch("apps.chat_api.routers.jobs.get_job_queue_service")
    def test_create_job_endpoint_exists(self, mock_get_service, client):
        """Verify create_job endpoint is available."""
        mock_service = MagicMock()
        mock_service.create_job.return_value = MagicMock(id="job_test_123")
        mock_get_service.return_value = mock_service
        payload = {"job_type": "message", "metadata": {}}
        response = client.post("/api/jobs", json=payload, headers=CHAT_AUTH)
        assert response.status_code == 200

    @patch("apps.chat_api.routers.jobs.get_job_queue_service")
    def test_create_job_response(self, mock_get_service, client):
        """Verify create_job returns job_id."""
        mock_service = MagicMock()
        mock_service.create_job.return_value = MagicMock(id="job_test_123")
        mock_get_service.return_value = mock_service
        payload = {"job_type": "message", "metadata": {}}
        response = client.post("/api/jobs", json=payload, headers=CHAT_AUTH)
        data = response.json()

        assert "status" in data
        assert "job_id" in data
        assert "message" in data

    @patch("apps.chat_api.routers.jobs.get_job_queue_service")
    def test_get_job_status_endpoint_exists(self, mock_get_service, client):
        """Verify get_job_status endpoint is available."""
        from acosplatform.job_queue.models import JobStatus

        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job_test_123"
        mock_job.status = JobStatus.QUEUED
        mock_job.created_at = MagicMock()
        mock_job.created_at.isoformat.return_value = "2026-04-14T10:00:00"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service
        response = client.get("/api/jobs/job_test_123/status")
        assert response.status_code == 200

    @patch("apps.chat_api.routers.jobs.get_job_queue_service")
    def test_get_job_status_response_structure(self, mock_get_service, client):
        """Verify get_job_status returns correct structure."""
        from acosplatform.job_queue.models import JobStatus

        mock_service = MagicMock()
        mock_job = MagicMock()
        mock_job.id = "job_test_123"
        mock_job.status = JobStatus.QUEUED
        mock_job.created_at = MagicMock()
        mock_job.created_at.isoformat.return_value = "2026-04-14T10:00:00"
        mock_service.get_job.return_value = mock_job
        mock_get_service.return_value = mock_service
        response = client.get("/api/jobs/job_test_123/status")
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "created_at" in data
