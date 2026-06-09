from fastapi.testclient import TestClient

from apps.ops_api.main import app
from acosplatform.outcomes.kpi import summarize_runs_for_outcomes


def test_business_outcome_summary_calculates_run_metrics():
    summary = summarize_runs_for_outcomes([
        {"status": "success", "handoff_count": 1, "tool_count": 4, "evidence_count": 8, "failed_tool_count": 0},
        {"status": "failed", "handoff_count": 0, "tool_count": 2, "evidence_count": 3, "failed_tool_count": 1},
    ])
    assert summary["sample_size"] == 2
    assert summary["metrics"]["successful_automation_rate"] == 0.5
    assert summary["metrics"]["fallback_or_handoff_rate"] == 0.5
    assert summary["metrics"]["failed_tool_rate"] == 0.1667
    assert summary["measurement_contract"]


def test_business_outcome_endpoint_exposes_pilot_kpis():
    client = TestClient(app)
    response = client.get("/api/northstar/business-outcomes")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["pilot_kpis"]) >= 7
    assert "successful_automation_rate" in payload["metrics"]
    assert payload["measurement_contract"]
