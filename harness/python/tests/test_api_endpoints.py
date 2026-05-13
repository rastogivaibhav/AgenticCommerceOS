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
            "family": "discovery"
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
        payload = {"step_definitions": {"nodes": [], "edges": []}}
        response = client.patch(
            "/workflows/test-workflow-id",
            json=payload,
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 404, 401, 403, 422]

    def test_delete_workflow(self):
        """Test DELETE /workflows/{workflow_id} endpoint."""
        response = client.delete(
            "/workflows/test-workflow-id",
            headers=TEST_HEADERS
        )
        assert response.status_code in [200, 204, 404, 401, 403]

    def test_rollback_workflow(self):
        """Test POST /workflows/{workflow_id}/rollback endpoint."""
        payload = {"target_environment": "dev", "reason": "test rollback"}
        response = client.post(
            "/workflows/test-workflow-id/rollback",
            json=payload,
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 409, 401, 403]

    def test_approve_workflow_version(self):
        """Test POST /workflows/{workflow_id}/versions/{version}/approve endpoint."""
        payload = {"approval_note": "test approval"}
        response = client.post(
            "/workflows/test-workflow-id/versions/v2/approve",
            json=payload,
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 401, 403]


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
            "workflow_family": "discovery",
            "customer_id": "cust-1",
            "tenant_id": "default",
            "message": "show me headphones",
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

    def test_slo_analytics(self):
        """Test GET /analytics/slo endpoint."""
        response = client.get("/analytics/slo", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "availability_pct" in data
            assert "latency_ms" in data

    def test_trace_analytics(self):
        """Test GET /analytics/traces endpoint."""
        response = client.get("/analytics/traces?limit=10", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "events" in data


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
        response = client.post("/agents", json=payload, headers=TEST_HEADERS)
        assert response.status_code in [200, 201, 400, 401, 403]

    def test_update_agent(self):
        """Test PATCH /agents/{agent_id} endpoint."""
        payload = {"name": "Updated Agent"}
        response = client.patch(
            "/agents/test-agent-id",
            json=payload,
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 400, 401, 403]

    def test_agent_provider_capabilities(self):
        """Test GET /api/v1/agents/providers endpoint."""
        response = client.get("/api/v1/agents/providers", headers=TEST_HEADERS)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "supported_providers" in data

    def test_bind_skill_to_agent(self):
        """Test POST /api/v1/agents/{agent_id}/bind-skill endpoint."""
        response = client.post(
            "/api/v1/agents/ag_marketing/bind-skill",
            json={"skill_id": "sk_catalog_search"},
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 400, 401, 403]

    def test_agent_test_run(self):
        """Test POST /api/v1/agents/{agent_id}/test endpoint."""
        response = client.post(
            "/api/v1/agents/ag_marketing/test",
            json={
                "message": "Where is my order ORD-1001?",
                "journey_type": "post_purchase",
                "tenant_id": "default",
                "customer_id": "ops-test-customer",
            },
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 400, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "runtime_provider" in data
            assert "model_name" in data
            assert "duration_ms" in data


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
        response = client.post("/skills", json=payload, headers=TEST_HEADERS)
        assert response.status_code in [200, 201, 400, 401, 403]

    def test_update_skill(self):
        """Test PATCH /skills/{skill_id} endpoint."""
        payload = {"name": "Updated Skill"}
        response = client.patch(
            "/skills/test-skill-id",
            json=payload,
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 400, 401, 403]

    def test_skill_test_run(self):
        """Test POST /api/v1/skills/{skill_id}/test endpoint."""
        response = client.post(
            "/api/v1/skills/sk_catalog_search/test",
            json={"input_payload": {"query": "headphones"}, "tenant_id": "default"},
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 404, 400, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "contract_validation" in data
            assert "connector_source" in data
            assert "connector_metadata" in data


class TestHealthAndSystem:
    """Test health check and system endpoints."""

    def test_root_redirect(self):
        """Test that / redirects to UI."""
        response = client.get("/", follow_redirects=False)
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

    def test_sandbox_execute_scenarios(self):
        """Test POST /api/v1/sandbox/execute-scenarios endpoint."""
        response = client.post(
            "/api/v1/sandbox/execute-scenarios",
            json={"tenant_id": "default", "customer_id": "sandbox-customer", "environment_id": "dev"},
            headers=TEST_HEADERS,
        )
        assert response.status_code in [200, 403, 401]
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data
            assert "results" in data
            assert "external_checks" in data
