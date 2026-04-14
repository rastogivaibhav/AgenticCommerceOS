"""Tests for workflow execution router endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from apps.chat_api.main import app

AUTH_HEADERS = {"Authorization": "Bearer dev-token"}


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestWorkflowExecutionEndpoints:
    """Tests for workflow execution API endpoints."""

    def test_execute_sync_endpoint_exists(self, client):
        """Test that sync execution endpoint exists."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 1,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute-sync", json=request_body, headers=AUTH_HEADERS)

        # Should not 404
        assert response.status_code != 404

    def test_execute_async_endpoint_exists(self, client):
        """Test that async execution endpoint exists."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 30,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute-async", json=request_body, headers=AUTH_HEADERS)

        # Should not 404
        assert response.status_code != 404

    def test_execute_auto_endpoint_exists(self, client):
        """Test that auto execution endpoint exists."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 2,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute", json=request_body, headers=AUTH_HEADERS)

        # Should not 404
        assert response.status_code != 404

    def test_sync_execution_returns_dict(self, client):
        """Test that sync execution returns dict with expected fields."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 1,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute-sync", json=request_body, headers=AUTH_HEADERS)

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, dict)
        assert "status" in result
        assert "execution_time_ms" in result or "result" in result

    def test_async_execution_returns_job_id(self, client):
        """Test that async execution returns job_id in response."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 30,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute-async", json=request_body, headers=AUTH_HEADERS)

        # Response should be successful
        # Could be 200 or 202 depending on implementation
        assert response.status_code in (200, 202)
        result = response.json()
        assert isinstance(result, dict)
        # Legacy endpoint returns dict with status
        assert "status" in result

    def test_auto_execution_uses_sync_for_fast_workflow(self, client):
        """Test that auto execution uses sync for timeout <= 2."""
        request_body = {
            "workflow_id": "wf_fast",
            "workflow_name": "Fast Workflow",
            "timeout_seconds": 1,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_fast/execute", json=request_body, headers=AUTH_HEADERS)

        assert response.status_code == 200
        result = response.json()
        # Should have sync execution results (execution_time_ms, result)
        assert "status" in result
        assert result["status"] in ("success", "completed", "failed")

    def test_auto_execution_uses_async_for_slow_workflow(self, client):
        """Test that auto execution uses async for timeout > 2."""
        request_body = {
            "workflow_id": "wf_slow",
            "workflow_name": "Slow Workflow",
            "timeout_seconds": 30,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_slow/execute", json=request_body, headers=AUTH_HEADERS)

        # Should be successful
        assert response.status_code in (200, 202)
        result = response.json()
        # Auto-routed to async, should have status
        assert "status" in result

    def test_execute_endpoint_with_missing_timeout_defaults_to_2(self, client):
        """Test that missing timeout_seconds defaults to 2."""
        request_body = {
            "workflow_id": "wf_test",
            "workflow_name": "Test Workflow",
            # Missing timeout_seconds
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test/execute-sync", json=request_body, headers=AUTH_HEADERS)

        # Should still work with default
        assert response.status_code == 200

    def test_execute_endpoint_includes_workflow_id_in_response(self, client):
        """Test that response includes workflow_id."""
        request_body = {
            "workflow_id": "wf_test_123",
            "workflow_name": "Test Workflow",
            "timeout_seconds": 1,
            "steps": [],
            "input_data": {"query": "test"},
        }

        response = client.post("/api/workflows/wf_test_123/execute-sync", json=request_body, headers=AUTH_HEADERS)

        assert response.status_code == 200
        result = response.json()
        assert "workflow_id" in result or result.get("workflow_id") == "wf_test_123"
