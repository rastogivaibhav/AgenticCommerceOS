"""Verify Week-9 observability dashboard and alert assets, then emit evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


REQUIRED_PANELS = {
    "Journey Availability %",
    "Journey Latency P95 (ms)",
    "API Errors by Endpoint",
    "Journey Cost (USD)",
}

REQUIRED_ALERT_NAMES = {
    "AcosJourneyAvailabilityBurn",
    "AcosJourneyLatencyP95High",
    "AcosTenantErrorRateHigh",
}

REQUIRED_ALERT_EXPRESSIONS = {
    "acos_journey_requests_total",
    "acos_journey_duration_seconds_bucket",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence-path",
        default="",
        help="Optional output path for evidence JSON report.",
    )
    return parser.parse_args()


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    dashboard_path = root / "docs" / "observability" / "grafana_slo_dashboard.json"
    kustomization_path = root / "deploy" / "k8s" / "observability" / "kustomization.yaml"
    alert_rules_path = root / "deploy" / "k8s" / "observability" / "prometheus-rule-slo-alerts.yaml"

    checks: list[dict[str, object]] = []

    dashboard_exists = dashboard_path.exists()
    checks.append(
        {
            "name": "dashboard_source_exists",
            "passed": dashboard_exists,
            "details": {"path": str(dashboard_path)},
        }
    )

    panel_titles: set[str] = set()
    if dashboard_exists:
        dashboard = json.loads(_load_text(dashboard_path))
        panel_titles = {panel.get("title", "") for panel in dashboard.get("panels", [])}
    checks.append(
        {
            "name": "dashboard_panels_complete",
            "passed": REQUIRED_PANELS.issubset(panel_titles),
            "details": {"required": sorted(REQUIRED_PANELS), "present": sorted(panel_titles)},
        }
    )

    kustomization_exists = kustomization_path.exists()
    kustomization_text = _load_text(kustomization_path) if kustomization_exists else ""
    checks.append(
        {
            "name": "kustomization_wires_dashboard",
            "passed": (
                kustomization_exists
                and "grafana-dashboard-acos-slo" in kustomization_text
                and "docs/observability/grafana_slo_dashboard.json" in kustomization_text
            ),
            "details": {"path": str(kustomization_path)},
        }
    )

    alert_exists = alert_rules_path.exists()
    alert_text = _load_text(alert_rules_path) if alert_exists else ""
    checks.append(
        {
            "name": "alert_rules_exist",
            "passed": alert_exists,
            "details": {"path": str(alert_rules_path)},
        }
    )

    found_alert_names = {name for name in REQUIRED_ALERT_NAMES if name in alert_text}
    checks.append(
        {
            "name": "alert_names_present",
            "passed": REQUIRED_ALERT_NAMES.issubset(found_alert_names),
            "details": {"required": sorted(REQUIRED_ALERT_NAMES), "present": sorted(found_alert_names)},
        }
    )

    checks.append(
        {
            "name": "alert_expressions_reference_metrics",
            "passed": all(expr in alert_text for expr in REQUIRED_ALERT_EXPRESSIONS),
            "details": {"required_metrics": sorted(REQUIRED_ALERT_EXPRESSIONS)},
        }
    )

    overall_pass = all(bool(check["passed"]) for check in checks)
    timestamp = datetime.now(UTC)
    default_name = f"week9-observability-{timestamp.strftime('%Y%m%d-%H%M%S')}.json"
    evidence_path = (
        Path(args.evidence_path)
        if args.evidence_path
        else root / "deploy" / "k8s" / "observability" / "evidence" / default_name
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": timestamp.isoformat(),
        "overall_pass": overall_pass,
        "checks": checks,
        "artifacts": {
            "dashboard": str(dashboard_path),
            "kustomization": str(kustomization_path),
            "alert_rules": str(alert_rules_path),
        },
    }
    evidence_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    status = "passed" if overall_pass else "failed"
    print(f"Week-9 observability asset verification {status}. Evidence: {evidence_path}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
