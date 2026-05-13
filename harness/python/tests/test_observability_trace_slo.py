"""Trace envelope and SLO snapshot tests for Week-9 baseline."""

from acosplatform.observability.slo import get_slo_snapshot, record_journey_observation
from acosplatform.observability.trace import (
    begin_trace_envelope,
    end_trace_envelope,
    get_recent_trace_events,
    log_trace_event,
)


def test_trace_envelope_contains_required_ids():
    envelope = begin_trace_envelope(
        run_id="run-test-1",
        tenant_id="default",
        journey="purchase",
        workflow_id="wf-purchase",
        workflow_version="v2",
        trace_id="trace-test-1",
    )
    assert envelope["tenant_id"] == "default"
    assert envelope["run_id"] == "run-test-1"
    assert envelope["workflow_id"] == "wf-purchase"

    log_trace_event("step.completed", {"step": "pricing"})
    finished = end_trace_envelope(status="success")
    assert finished["trace_id"] == "trace-test-1"

    recent = get_recent_trace_events(limit=5, run_id="run-test-1")
    assert any(event["event_type"] == "step.completed" for event in recent)
    assert any(event["event_type"] == "trace_finished" for event in recent)


def test_slo_snapshot_includes_availability_and_p95():
    record_journey_observation(
        tenant_id="default",
        journey="discovery",
        run_id="run-slo-1",
        duration_ms=120,
        success=True,
        cost=0.01,
    )
    record_journey_observation(
        tenant_id="default",
        journey="discovery",
        run_id="run-slo-2",
        duration_ms=650,
        success=False,
        cost=0.02,
    )
    snapshot = get_slo_snapshot(window_minutes=60, tenant_id="default")
    assert snapshot["tenant_id"] == "default"
    assert snapshot["total_runs"] >= 2
    assert "availability_pct" in snapshot
    assert snapshot["latency_ms"]["p95"] >= 120
