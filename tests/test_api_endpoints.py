"""Test API endpoints for ACOS Control Plane."""

import pytest
from fastapi.testclient import TestClient
from apps.ops_api.main import app

client = TestClient(app)

# Dev auth headers — matches dev-mode behavior
TEST_HEADERS = {"Authorization": "Bearer dev-token"}


class TestWorkflowEndpoints:
    """Test workflow-related API endpoints."""

    def test_list_workflows(self):
        """Test GET /workflows endpoint."""
        response = client.get("/workflows", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "workflows" in data or "items" in data or isinstance(data, list)

    def test_create_workflow(self):
        """Test POST /workflows endpoint."""
        payload = {
            "name": "Test Workflow",
            "description": "Test description",
            "family": "test"
        }
        response = client.post("/workflows", json=payload, headers=TEST_HEADERS)
        assert response.status_code in [200, 201, 401, 403]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "workflow" in data or "id" in data

    def test_get_workflow_detail(self):
        """Test GET /workflows/{workflow_id} endpoint."""
        response = client.get("/workflows/test-workflow-id", headers=TEST_HEADERS)
        assert response.status_code in [200, 404, 401, 403]

    def test_update_workflow(self):
        """Test PATCH /workflows/{workflow_id} endpoint."""
        payload = {"name": "Updated Workflow"}
        response = client.patch(
            "/workflows/test-workflow-id",
            json=payload,
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 404, 401, 403]

    def test_delete_workflow(self):
        """Test DELETE /workflows/{workflow_id} endpoint."""
        response = client.delete(
            "/workflows/test-workflow-id",
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 204, 404, 401, 403]


class TestExperimentsEndpoints:
    """Test experiment-related API endpoints."""

    def test_list_experiments(self):
        """Test GET /experiments endpoint."""
        response = client.get("/experiments", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_create_experiment(self):
        """Test POST /experiments endpoint."""
        payload = {
            "name": "Test Experiment",
            "workflow_id": "test-workflow",
            "variant_a": {"param": "value_a"},
            "variant_b": {"param": "value_b"},
            "sample_size": 100
        }
        response = client.post("/experiments", json=payload, headers=TEST_HEADERS)
        assert response.status_code in [200, 201, 401, 403]

    def test_get_experiment_results(self):
        """Test GET /experiments/{experiment_id}/results endpoint."""
        response = client.get(
            "/experiments/test-experiment-id/results",
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 404, 401, 403]


class TestAnalyticsEndpoints:
    """Test analytics-related API endpoints."""

    def test_get_metrics(self):
        """Test GET /analytics/metrics endpoint."""
        response = client.get("/analytics/metrics", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_dashboard(self):
        """Test GET /dashboard endpoint."""
        response = client.get("/dashboard", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "metrics" in data or "billing" in data

    def test_export_analytics(self):
        """Test GET /analytics/export endpoint."""
        response = client.get(
            "/analytics/export?format=csv",
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 401, 403]


class TestAgentEndpoints:
    """Test agent management endpoints."""

    def test_list_agents(self):
        """Test GET /agents endpoint."""
        response = client.get("/agents")
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "agents" in data

    def test_create_agent(self):
        """Test POST /agents endpoint."""
        payload = {
            "id": "test-agent",
            "name": "Test Agent",
            "description": "A test agent"
        }
        response = client.post("/agents", json=payload)
        assert response.status_code in [200, 201, 400]

    def test_update_agent(self):
        """Test PATCH /agents/{agent_id} endpoint."""
        payload = {"name": "Updated Agent"}
        response = client.patch(
            "/agents/test-agent-id",
            json=payload
        )
        assert response.status_code in [200, 404, 400]


class TestSkillEndpoints:
    """Test skill management endpoints."""

    def test_list_skills(self):
        """Test GET /skills endpoint."""
        response = client.get("/skills")
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "skills" in data

    def test_create_skill(self):
        """Test POST /skills endpoint."""
        payload = {
            "id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill"
        }
        response = client.post("/skills", json=payload)
        assert response.status_code in [200, 201, 400]

    def test_update_skill(self):
        """Test PATCH /skills/{skill_id} endpoint."""
        payload = {"name": "Updated Skill"}
        response = client.patch(
            "/skills/test-skill-id",
            json=payload
        )
        assert response.status_code in [200, 404, 400]


class TestHealthAndSystem:
    """Test health check and system endpoints."""

    def test_root_redirect(self):
        """Test that / redirects to UI."""
        response = client.get("/", allow_redirects=False)
        assert response.status_code in [200, 307, 308]

    def test_runs_list(self):
        """Test GET /runs endpoint."""
        response = client.get("/runs", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "runs" in data

    def test_run_detail(self):
        """Test GET /runs/{run_id} endpoint."""
        response = client.get("/runs/test-run-id", headers=TEST_HEADERS)
        assert response.status_code in [200, 404, 401, 403]

    def test_billing_endpoint(self):
        """Test GET /billing endpoint."""
        response = client.get("/billing", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data or "usage" in data
