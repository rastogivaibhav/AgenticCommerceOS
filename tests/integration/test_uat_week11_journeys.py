# tests/integration/test_uat_week11_journeys.py
import pytest
import json
from tests.fixtures.uat_pilot_data import (
    PILOT_TENANT_A,
    PILOT_TENANT_B,
    WORKFLOW_DISCOVERY,
    WORKFLOW_POST_PURCHASE,
    WORKFLOW_SERVICE_GUIDANCE,
    WORKFLOW_RETURNS
)

class TestOperatorJourney1WorkflowInventory:
    """Operator Journey 1: Review Workflow Inventory"""

    @pytest.mark.integration
    def test_workflow_admin_list_all_workflows(self, client):
        """WA-1.1: Workflow Admin can list all workflows in assigned tenant"""
        response = client.get(
            f"/api/workflows?tenant_id={PILOT_TENANT_A['id']}",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) >= 1
        assert any(w["id"] == WORKFLOW_DISCOVERY["id"] for w in data["workflows"])

    @pytest.mark.integration
    def test_workflow_inventory_shows_version_and_status(self, client):
        """WA-1.2: Inventory shows version and environment badges"""
        response = client.get(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        workflow = response.json()
        assert "version" in workflow
        assert "status" in workflow
        assert "environment" in workflow
        assert workflow["version"] == "1.0.0"

    @pytest.mark.integration
    def test_workflow_inventory_filter_by_family(self, client):
        """WA-1.3: Workflow Admin can filter by workflow family"""
        response = client.get(
            f"/api/workflows?tenant_id={PILOT_TENANT_A['id']}&family=discovery",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(w["family"] == "discovery" for w in data["workflows"])

    @pytest.mark.integration
    def test_workflow_inventory_filter_by_status(self, client):
        """WA-1.4: Workflow Admin can filter by status"""
        response = client.get(
            f"/api/workflows?tenant_id={PILOT_TENANT_A['id']}&status=active",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(w["status"] == "active" for w in data["workflows"])

    @pytest.mark.integration
    def test_workflow_quick_drill_in(self, client):
        """WA-1.5: Workflow Admin can quickly drill into workflow detail"""
        response = client.get(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}/detail",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        detail = response.json()
        assert detail["id"] == WORKFLOW_DISCOVERY["id"]
        assert "last_promotion" in detail
        assert "active_version" in detail
        assert "validation_status" in detail
