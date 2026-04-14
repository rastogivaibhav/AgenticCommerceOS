"""Week-9 observability wiring asset checks."""

from __future__ import annotations

import json
from pathlib import Path


def test_week9_observability_assets_exist():
    root = Path(__file__).resolve().parents[1]
    required = [
        root / "deploy" / "k8s" / "observability" / "kustomization.yaml",
        root / "deploy" / "k8s" / "observability" / "prometheus-rule-slo-alerts.yaml",
        root / "deploy" / "k8s" / "observability" / "README.md",
        root / "scripts" / "verify_week9_observability_assets.py",
        root / "docs" / "observability" / "grafana_slo_dashboard.json",
    ]
    for path in required:
        assert path.exists(), f"missing expected Week-9 asset: {path}"


def test_dashboard_contains_required_week9_panels():
    root = Path(__file__).resolve().parents[1]
    dashboard = json.loads(
        (root / "docs" / "observability" / "grafana_slo_dashboard.json").read_text(encoding="utf-8")
    )
    titles = {panel.get("title", "") for panel in dashboard.get("panels", [])}
    assert "Journey Availability %" in titles
    assert "Journey Latency P95 (ms)" in titles
    assert "API Errors by Endpoint" in titles
    assert "Journey Cost (USD)" in titles


def test_alert_rule_pack_contains_slo_alerts():
    root = Path(__file__).resolve().parents[1]
    content = (root / "deploy" / "k8s" / "observability" / "prometheus-rule-slo-alerts.yaml").read_text(
        encoding="utf-8"
    )
    assert "alert: AcosJourneyAvailabilityBurn" in content
    assert "alert: AcosJourneyLatencyP95High" in content
    assert "alert: AcosTenantErrorRateHigh" in content
    assert "acos_journey_requests_total" in content
    assert "acos_journey_duration_seconds_bucket" in content
