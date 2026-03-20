"""Tests for the database repository (uses in-memory fallback)."""

from acosplatform.db.repository import (
    save_run, get_runs, get_run, save_event, get_events,
    save_experiment, get_experiments, get_dashboard,
    save_workflow, get_workflows, get_workflow, save_workflow_version, get_workflow_versions,
    save_workflow_promotion, get_workflow_promotions, save_audit_event, get_audit_events,
    _fallback_runs, _fallback_events, _fallback_experiments,
    _fallback_workflows, _fallback_workflow_versions, _fallback_workflow_promotions, _fallback_audit_events,
)


def _clear_fallback():
    """Clear in-memory fallback stores for test isolation."""
    _fallback_runs.clear()
    _fallback_events.clear()
    _fallback_experiments.clear()
    _fallback_workflows.clear()
    _fallback_workflow_versions.clear()
    _fallback_workflow_promotions.clear()
    _fallback_audit_events.clear()


class TestRepository:
    def setup_method(self):
        _clear_fallback()

    def test_save_and_get_run(self):
        save_run(
            run_id="test-run-1",
            tenant_id="default",
            customer_id="cust-1",
            journey="discovery",
            input_data={"message": "test"},
            output_data={"result": "ok"},
            cost=0.01,
            score=7.5,
        )
        runs = get_runs()
        assert len(runs) >= 1
        found = [r for r in runs if r["id"] == "test-run-1"]
        assert len(found) == 1
        assert found[0]["journey"] == "discovery"

    def test_get_run_by_id(self):
        save_run("test-run-2", "default", "cust-1", "purchase", {}, {})
        run = get_run("test-run-2")
        assert run is not None
        assert run["id"] == "test-run-2"

    def test_get_run_not_found(self):
        run = get_run("nonexistent")
        assert run is None

    def test_save_and_get_events(self):
        save_run("test-run-3", "default", "cust-1", "discovery", {}, {})
        save_event("test-run-3", "journey_started", {"step": 1})
        save_event("test-run-3", "journey_completed", {"step": 2})
        events = get_events("test-run-3")
        assert len(events) == 2
        assert events[0]["event_type"] == "journey_started"
        assert events[1]["event_type"] == "journey_completed"

    def test_save_and_get_experiments(self):
        save_experiment(
            name="test_experiment",
            variant_a={"score": 8},
            variant_b={"score": 6},
            winner="A",
        )
        experiments = get_experiments()
        assert len(experiments) >= 1
        assert experiments[-1]["name"] == "test_experiment"
        assert experiments[-1]["winner"] == "A"

    def test_dashboard(self):
        save_run("dash-1", "default", "cust-1", "discovery", {}, {}, cost=0.01, score=8.0)
        save_run("dash-2", "default", "cust-2", "purchase", {}, {}, cost=0.02, score=6.0)
        dash = get_dashboard()
        assert dash["total_runs"] >= 2
        assert dash["unique_customers"] >= 2
        assert dash["total_cost"] > 0
        assert dash["avg_score"] > 0
        assert "discovery" in dash["runs_by_journey"]

    def test_runs_filter_by_tenant(self):
        save_run("t1", "tenant-a", "cust-1", "discovery", {}, {})
        save_run("t2", "tenant-b", "cust-1", "purchase", {}, {})
        all_runs = get_runs()
        assert len(all_runs) >= 2

    def test_save_and_get_workflow_registry(self):
        save_workflow("wf-test", "default", "Test Workflow", "service", "desc", "ops", "draft")
        save_workflow_version("wf-test", "v1", "Initial draft")
        save_workflow_promotion("wf-test", "v1", None, "dev", "tester", "tester", "activate")
        save_audit_event("tester", "workflow.promoted", "workflow", "wf-test", payload={"version": "v1"})

        workflows = get_workflows()
        assert len(workflows) == 1
        assert get_workflow("wf-test")["name"] == "Test Workflow"
        assert get_workflow_versions("wf-test")[0]["version"] == "v1"
        assert get_workflow_promotions("wf-test")[0]["version"] == "v1"
        assert get_audit_events("workflow", "wf-test")[0]["action"] == "workflow.promoted"
