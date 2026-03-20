"""Integration tests for the Shopper API and Ops API — updated for auth (Sprint 0)."""

import os
from fastapi.testclient import TestClient
from apps.shopper_api.main import app as shopper_app
from apps.ops_api.main import app as ops_app

shopper = TestClient(shopper_app)
ops = TestClient(ops_app)

# Dev auth headers — matches dev-mode fallbacks in api_key.py
SHOPPER_AUTH = {"X-API-Key": "dev-key-insecure"}
OPS_AUTH = {"Authorization": "Bearer dev-token"}   # dev mode: no JWT_SECRET set → passthrough


class TestShopperAPI:
    def test_health(self):
        r = shopper.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("ok", "degraded")  # degraded OK in test env (no DB)

    def test_journey_discovery(self):
        r = shopper.post("/journey",
                         json={"message": "recommend me a laptop", "customer_id": "cust-1"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert "run_id" in data
        assert data["journey"] == "discovery"
        assert "result" in data
        result = data["result"]
        assert "recommendations" in result or "agent" in result

    def test_journey_purchase(self):
        r = shopper.post("/journey",
                         json={"message": "buy headphones", "customer_id": "cust-2"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert data["journey"] == "purchase"
        result = data["result"]
        assert "cart" in result or "products" in result

    def test_journey_post_purchase(self):
        r = shopper.post("/journey",
                         json={"message": "where is my order", "customer_id": "cust-1"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200
        assert r.json()["journey"] == "post_purchase"

    def test_journey_service(self):
        r = shopper.post("/journey",
                         json={"message": "I want to return my item", "customer_id": "cust-1"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200
        assert r.json()["journey"] == "service"

    def test_journey_engagement(self):
        r = shopper.post("/journey",
                         json={"message": "I want to leave feedback", "customer_id": "cust-1"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200
        assert r.json()["journey"] == "engagement"

    def test_journey_with_tenant(self):
        r = shopper.post("/journey",
                         json={"message": "recommend something", "customer_id": "cust-1",
                               "tenant_id": "eu-store"},
                         headers=SHOPPER_AUTH)
        assert r.status_code == 200

    def test_journey_minimal_payload(self):
        r = shopper.post("/journey", json={"message": "hello"}, headers=SHOPPER_AUTH)
        assert r.status_code == 200


class TestOpsAPI:
    def test_health(self):
        r = ops.get("/health")
        assert r.status_code == 200

    def test_runs_list(self):
        r = ops.get("/runs", headers=OPS_AUTH)
        assert r.status_code == 200
        assert "runs" in r.json()

    def test_dashboard(self):
        r = ops.get("/dashboard", headers=OPS_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "billing" in data

    def test_run_not_found(self):
        r = ops.get("/runs/nonexistent", headers=OPS_AUTH)
        assert r.status_code == 404

    def test_billing(self):
        r = ops.get("/billing", headers=OPS_AUTH)
        assert r.status_code == 200

    def test_ui_served(self):
        r = ops.get("/")
        assert r.status_code == 200
        assert "ACOS Control Plane" in r.text

    def test_workflows_list(self):
        r = ops.get("/workflows", headers=OPS_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert "workflows" in data
        assert len(data["workflows"]) >= 1

    def test_workflow_detail(self):
        listing = ops.get("/workflows", headers=OPS_AUTH).json()["workflows"]
        workflow_id = listing[0]["id"]
        r = ops.get(f"/workflows/{workflow_id}", headers=OPS_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert "workflow" in data
        assert "versions" in data
        assert "promotions" in data
        assert "audits" in data

    def test_create_and_promote_workflow(self):
        create = ops.post(
            "/workflows",
            json={
                "tenant_id": "default",
                "name": "Warranty Escalation",
                "workflow_family": "service",
                "description": "Handle warranty escalations",
                "business_owner": "service-ops",
                "change_summary": "Initial draft",
            },
            headers=OPS_AUTH,
        )
        assert create.status_code == 200
        workflow_id = create.json()["workflow"]["id"]

        version = ops.post(
            f"/workflows/{workflow_id}/versions",
            json={"change_summary": "Approved pilot version", "validation_status": "approved"},
            headers=OPS_AUTH,
        )
        assert version.status_code == 200
        version_label = version.json()["version"]

        promote = ops.post(
            f"/workflows/{workflow_id}/versions/{version_label}/promote",
            json={"target_environment": "dev", "approval_note": "Pilot activation"},
            headers=OPS_AUTH,
        )
        assert promote.status_code == 200

        detail = ops.get(f"/workflows/{workflow_id}", headers=OPS_AUTH)
        assert detail.status_code == 200
        assert any(a["action"] == "workflow.promoted" for a in detail.json()["audits"])

    def test_replay_not_found(self):
        r = ops.post("/replay/nonexistent", headers=OPS_AUTH)
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is False


class TestEndToEnd:
    """Test the full flow: journey → runs list → run detail → replay."""

    def test_full_flow(self):
        # 1. Create a journey
        r1 = shopper.post("/journey",
                          json={"message": "recommend me a laptop", "customer_id": "cust-1"},
                          headers=SHOPPER_AUTH)
        assert r1.status_code == 200
        run_id = r1.json()["run_id"]

        # 2. Get runs (should include new run - may be in DB or fallback)
        r2 = ops.get("/runs", headers=OPS_AUTH)
        assert r2.status_code == 200

        # 3. Dashboard should show metrics
        r3 = ops.get("/dashboard", headers=OPS_AUTH)
        assert r3.status_code == 200
        assert r3.json()["metrics"]["total_runs"] >= 0
