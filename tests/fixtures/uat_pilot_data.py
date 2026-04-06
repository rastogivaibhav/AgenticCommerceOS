# tests/fixtures/uat_pilot_data.py
import pytest
from datetime import datetime, timezone
import json

# Pilot Tenant Configuration
PILOT_TENANT_A = {
    "id": "tenant_uat_pilot_a",
    "name": "Pilot Tenant A",
    "environment": "stage",
    "status": "active",
    "created_at": datetime.now(timezone.utc).isoformat()
}

PILOT_TENANT_B = {
    "id": "tenant_uat_pilot_b",
    "name": "Pilot Tenant B",
    "environment": "stage",
    "status": "active",
    "created_at": datetime.now(timezone.utc).isoformat()
}

# Workflow Families for Bounded Scope
WORKFLOW_DISCOVERY = {
    "id": "wf_discovery_v1",
    "name": "Product Discovery",
    "family": "discovery",
    "tenant_id": PILOT_TENANT_A["id"],
    "version": "1.0.0",
    "status": "active",
    "description": "Conversational product recommendation workflow"
}

WORKFLOW_POST_PURCHASE = {
    "id": "wf_post_purchase_v1",
    "name": "Order Status Agent",
    "family": "post_purchase",
    "tenant_id": PILOT_TENANT_A["id"],
    "version": "1.0.0",
    "status": "active",
    "description": "Order tracking and status inquiry workflow"
}

WORKFLOW_SERVICE_GUIDANCE = {
    "id": "wf_service_guidance_v1",
    "name": "Service Help Desk",
    "family": "service_guidance",
    "tenant_id": PILOT_TENANT_B["id"],
    "version": "1.0.0",
    "status": "active",
    "description": "Service guidance without financial mutations"
}

WORKFLOW_RETURNS = {
    "id": "wf_returns_v1",
    "name": "Returns Processor",
    "family": "returns",
    "tenant_id": PILOT_TENANT_B["id"],
    "version": "1.0.0",
    "status": "active",
    "description": "Controlled returns initiation with policy guardrails"
}

# Sample runs for investigation testing
SAMPLE_RUN_SUCCESS = {
    "id": "run_success_001",
    "workflow_id": WORKFLOW_DISCOVERY["id"],
    "tenant_id": PILOT_TENANT_A["id"],
    "status": "completed",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "ended_at": datetime.now(timezone.utc).isoformat(),
    "steps": [
        {"step": "classify_intent", "status": "completed", "duration_ms": 145},
        {"step": "search_products", "status": "completed", "duration_ms": 320},
        {"step": "rank_results", "status": "completed", "duration_ms": 210},
        {"step": "format_response", "status": "completed", "duration_ms": 95}
    ],
    "output": {"recommendations": 3, "engagement_score": 0.87}
}

SAMPLE_RUN_FAILURE = {
    "id": "run_failure_001",
    "workflow_id": WORKFLOW_POST_PURCHASE["id"],
    "tenant_id": PILOT_TENANT_A["id"],
    "status": "failed",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "ended_at": datetime.now(timezone.utc).isoformat(),
    "steps": [
        {"step": "validate_order_id", "status": "completed", "duration_ms": 85},
        {"step": "lookup_order", "status": "failed", "duration_ms": 150, "error": "order_not_found"},
        {"step": "format_response", "status": "skipped"}
    ],
    "error_message": "Order ID not found in system"
}

@pytest.fixture
def pilot_tenant_a():
    return PILOT_TENANT_A

@pytest.fixture
def pilot_tenant_b():
    return PILOT_TENANT_B

@pytest.fixture
def workflow_discovery():
    return WORKFLOW_DISCOVERY

@pytest.fixture
def workflow_post_purchase():
    return WORKFLOW_POST_PURCHASE

@pytest.fixture
def workflow_service_guidance():
    return WORKFLOW_SERVICE_GUIDANCE

@pytest.fixture
def workflow_returns():
    return WORKFLOW_RETURNS

@pytest.fixture
def sample_successful_run():
    return SAMPLE_RUN_SUCCESS

@pytest.fixture
def sample_failed_run():
    return SAMPLE_RUN_FAILURE
