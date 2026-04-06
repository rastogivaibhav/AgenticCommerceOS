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


class TestOperatorJourney2WorkflowPromotion:
    """Operator Journey 2: Promote A Workflow Version"""

    @pytest.mark.integration
    def test_workflow_admin_view_promotion_diff(self, client):
        """WA-2.1: Workflow Admin can view diff before promotion"""
        response = client.get(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}/promote/diff?target_env=prod",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        diff = response.json()
        assert "changes" in diff
        assert "affected_fields" in diff

    @pytest.mark.integration
    def test_promotion_requires_approval_for_prod(self, client):
        """WA-2.2: Production promotion requires Risk Owner approval"""
        # Step 1: Workflow Admin submits for approval
        promote_request = {
            "target_environment": "prod",
            "version": "1.0.0",
            "promotion_reason": "Validated in stage, ready for production"
        }
        response = client.post(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}/promote",
            json=promote_request,
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 202
        approval_request = response.json()
        approval_id = approval_request["approval_id"]
        assert approval_request["status"] == "pending_approval"

        # Step 2: Risk Owner approves
        response = client.post(
            f"/api/approvals/{approval_id}/approve",
            json={"approval_reason": "Compliance check passed"},
            headers={"Authorization": "Bearer risk_owner_token"}
        )
        assert response.status_code == 200
        approval = response.json()
        assert approval["status"] == "approved"

        # Step 3: Promotion completes
        response = client.post(
            f"/api/approvals/{approval_id}/promote",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        promotion = response.json()
        assert promotion["status"] == "completed"
        assert promotion["target_environment"] == "prod"

    @pytest.mark.integration
    def test_promotion_creates_audit_event(self, client):
        """WA-2.3: Promotion creates audit event"""
        # Perform promotion (assuming it passes)
        response = client.post(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}/promote",
            json={
                "target_environment": "stage",
                "version": "1.0.0",
                "promotion_reason": "Stage validation"
            },
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code in [200, 202]
        promotion_id = response.json().get("id") or response.json().get("promotion_id")

        # Verify audit entry
        response = client.get(
            f"/api/audit?resource_id={WORKFLOW_DISCOVERY['id']}&action=workflow_promoted",
            headers={"Authorization": "Bearer admin_token"}
        )
        assert response.status_code == 200
        audit_events = response.json()
        assert len(audit_events) > 0
        assert any(e["promotion_id"] == promotion_id for e in audit_events if "promotion_id" in e)

    @pytest.mark.integration
    def test_promotion_records_rollback_target(self, client):
        """WA-2.4: Promotion records rollback target version"""
        response = client.get(
            f"/api/workflows/{WORKFLOW_DISCOVERY['id']}/promotions",
            headers={"Authorization": "Bearer workflow_admin_token"}
        )
        assert response.status_code == 200
        promotions = response.json()
        assert len(promotions) > 0
        latest = promotions[0]
        assert "rollback_version" in latest
        assert latest["rollback_version"] is not None


class TestOperatorJourney3RunInvestigation:
    """Operator Journey 3: Investigate A Failed Run"""

    @pytest.mark.integration
    def test_ops_lead_list_failed_runs(self, client):
        """OL-3.1: Ops Lead can list failed runs with filters"""
        response = client.get(
            f"/api/runs?tenant_id={PILOT_TENANT_A['id']}&status=failed",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert all(r["status"] == "failed" for r in data["runs"])

    @pytest.mark.integration
    def test_ops_lead_view_run_timeline(self, client):
        """OL-3.2: Ops Lead can view run timeline with step details"""
        # First get a failed run
        response = client.get(
            f"/api/runs?tenant_id={PILOT_TENANT_A['id']}&status=failed&limit=1",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 200
        runs = response.json()["runs"]
        assert len(runs) > 0
        run_id = runs[0]["id"]

        # Get run timeline
        response = client.get(
            f"/api/runs/{run_id}/timeline",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 200
        timeline = response.json()
        assert "steps" in timeline
        assert all(s["step"] for s in timeline["steps"])
        assert all("status" in s for s in timeline["steps"])
        assert all("duration_ms" in s for s in timeline["steps"])

    @pytest.mark.integration
    def test_ops_lead_view_policy_decisions(self, client):
        """OL-3.3: Ops Lead can see policy decisions in timeline"""
        response = client.get(
            f"/api/runs?tenant_id={PILOT_TENANT_A['id']}&status=failed&limit=1",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        runs = response.json()["runs"]
        run_id = runs[0]["id"]

        response = client.get(
            f"/api/runs/{run_id}/timeline?include_policy=true",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 200
        timeline = response.json()
        # Check for policy decisions in steps or separate section
        assert "policy_decisions" in timeline or any("policy" in str(s) for s in timeline.get("steps", []))

    @pytest.mark.integration
    def test_ops_lead_can_replay_run(self, client):
        """OL-3.4: Ops Lead can trigger replay of failed run"""
        response = client.get(
            f"/api/runs?tenant_id={PILOT_TENANT_A['id']}&status=failed&limit=1",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        runs = response.json()["runs"]
        run_id = runs[0]["id"]

        response = client.post(
            f"/api/runs/{run_id}/replay",
            json={"reason": "Customer escalation - retry failed order lookup"},
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 202
        replay = response.json()
        assert replay["status"] == "replaying"
        assert "replay_id" in replay

    @pytest.mark.integration
    def test_ops_lead_escalate_run(self, client):
        """OL-3.5: Ops Lead can escalate run to human handling"""
        response = client.get(
            f"/api/runs?tenant_id={PILOT_TENANT_A['id']}&status=failed&limit=1",
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        runs = response.json()["runs"]
        run_id = runs[0]["id"]

        response = client.post(
            f"/api/runs/{run_id}/escalate",
            json={
                "escalation_reason": "Requires manual intervention",
                "assigned_to": "human_handler_team"
            },
            headers={"Authorization": "Bearer ops_lead_token"}
        )
        assert response.status_code == 200
        escalation = response.json()
        assert escalation["status"] == "escalated"
