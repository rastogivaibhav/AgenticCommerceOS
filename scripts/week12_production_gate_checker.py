#!/usr/bin/env python3
"""
Week 12 Production Gate Checker

Validates production readiness checks from the go-live PRD and writes
an evidence artifact.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class ProductionGateChecker:
    def __init__(self, repo_root: Path | None = None):
        # Anchor all checks to repo root so results do not depend on current cwd.
        self.repo_root = (repo_root or Path(__file__).resolve().parent.parent).resolve()
        self.checks: dict[str, dict] = {}
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"

    def _abs(self, rel_path: str) -> Path:
        return self.repo_root / rel_path

    def _exists(self, rel_path: str) -> bool:
        return self._abs(rel_path).exists()

    def _read_text(self, rel_path: str) -> str:
        path = self._abs(rel_path)
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="utf-8", errors="ignore")

    def _contains_all(self, rel_path: str, tokens: list[str]) -> bool:
        content = self._read_text(rel_path)
        return bool(content) and all(token in content for token in tokens)

    def _contains_any(self, rel_path: str, tokens: list[str]) -> bool:
        content = self._read_text(rel_path)
        return bool(content) and any(token in content for token in tokens)

    def _record(self, key: str, requirement: str, passed: bool, details: str) -> bool:
        self.checks[key] = {
            "requirement": requirement,
            "passed": passed,
            "details": details,
        }
        print(f"  [{'PASS' if passed else 'FAIL'}] {key}: {details}")
        return passed

    def check_workflow_versioning(self) -> bool:
        """GR-1: Versioned workflow resources exist"""
        print("\nCheck: Workflow versioning")
        service_has_versioning = self._contains_all(
            "acosplatform/workflows/service.py",
            ["def create_workflow_version(", "active_version", "validation_status"],
        )
        persistence_has_versioning = self._contains_all(
            "acosplatform/db/repository.py",
            ["def save_workflow_version(", "workflow_versions", "version"],
        )
        passed = service_has_versioning and persistence_has_versioning
        details = (
            "Workflow service and persistence both expose versioned workflow lifecycle hooks"
            if passed
            else (
                f"service_has_versioning={service_has_versioning}, "
                f"persistence_has_versioning={persistence_has_versioning}"
            )
        )
        return self._record(
            "workflow_versioning",
            "GR-1: Versioned workflow resources exist in persistence",
            passed,
            details,
        )

    def check_run_version_tracking(self) -> bool:
        """GR-2: Runs reference workflow versions"""
        print("\nCheck: Run version tracking")
        repository_tracks_run_versions = self._contains_all(
            "acosplatform/db/repository.py",
            ["def save_run(", "workflow_version"],
        )
        journey_emits_run_versions = self._contains_all(
            "acosplatform/journey/engine.py",
            ["workflow_version"],
        )
        passed = repository_tracks_run_versions and journey_emits_run_versions
        details = (
            "Run persistence and journey engine both reference workflow_version"
            if passed
            else (
                f"repository_tracks_run_versions={repository_tracks_run_versions}, "
                f"journey_emits_run_versions={journey_emits_run_versions}"
            )
        )
        return self._record(
            "run_version_tracking",
            "GR-2: Every run records the workflow version used",
            passed,
            details,
        )

    def check_ui_surfaces(self) -> bool:
        """GR-8: React control-plane foundation exists"""
        print("\nCheck: UI control-plane surfaces")
        app_routes_exist = self._contains_all(
            "apps/ops_ui_v2/src/App.jsx",
            ["/workflows", "/simulation"],
        )
        ui_pages_exist = all(
            self._exists(path)
            for path in [
                "apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx",
                "apps/ops_ui_v2/src/pages/WorkflowEditor.jsx",
                "apps/ops_ui_v2/src/pages/Simulation.jsx",
            ]
        )
        investigation_routes_exist = all(
            self._exists(path)
            for path in [
                "apps/ops_api/routers/northstar_api.py",
                "apps/ops_api/routers/uat_compat.py",
                "apps/ops_api/routers/v2_control_plane.py",
            ]
        )
        passed = app_routes_exist and ui_pages_exist and investigation_routes_exist
        details = (
            "React routes and workflow/run investigation surfaces are present"
            if passed
            else (
                f"app_routes_exist={app_routes_exist}, "
                f"ui_pages_exist={ui_pages_exist}, "
                f"investigation_routes_exist={investigation_routes_exist}"
            )
        )
        return self._record(
            "ui_surfaces",
            "GR-8: Real React control plane with foundational views",
            passed,
            details,
        )

    def check_authentication(self) -> bool:
        """GNFR-2: Security auth is in place"""
        print("\nCheck: Authentication and authorization")
        auth_module_exists = self._contains_all(
            "acosplatform/auth/api_key.py",
            ["def require_ops_roles"],
        )
        main_has_auth_header = self._contains_all(
            "apps/ops_api/main.py",
            ["Authorization", "require_ops_roles"],
        )
        router_role_enforcement = False
        routers_root = self._abs("apps/ops_api/routers")
        if routers_root.exists():
            for file in routers_root.rglob("*.py"):
                text = file.read_text(encoding="utf-8", errors="ignore")
                if "require_ops_roles(" in text and "Depends(" in text:
                    router_role_enforcement = True
                    break

        passed = auth_module_exists and main_has_auth_header and router_role_enforcement
        details = (
            "Role-based auth hooks and protected routes detected"
            if passed
            else (
                f"auth_module_exists={auth_module_exists}, "
                f"main_has_auth_header={main_has_auth_header}, "
                f"router_role_enforcement={router_role_enforcement}"
            )
        )
        return self._record(
            "authentication",
            "GNFR-2: Auth, role enforcement, secrets handling in place",
            passed,
            details,
        )

    def check_observability(self) -> bool:
        """GNFR-3: Logs, metrics, health endpoints"""
        print("\nCheck: Observability")
        metrics_module_exists = self._exists("acosplatform/observability/metrics.py")
        health_endpoint_exists = self._contains_any(
            "apps/ops_api/main.py",
            ['@app.get("/health")', "@app.get('/health')"],
        )
        metrics_endpoint_exists = self._contains_any(
            "apps/ops_api/main.py",
            ['@app.get("/metrics")', "@app.get('/metrics')"],
        )
        passed = metrics_module_exists and health_endpoint_exists and metrics_endpoint_exists
        details = (
            "Metrics module and health/metrics endpoints are present"
            if passed
            else (
                f"metrics_module_exists={metrics_module_exists}, "
                f"health_endpoint_exists={health_endpoint_exists}, "
                f"metrics_endpoint_exists={metrics_endpoint_exists}"
            )
        )
        return self._record(
            "observability",
            "GNFR-3: Logs, metrics, and health endpoints for pilot operations",
            passed,
            details,
        )

    def check_docker_deployment(self) -> bool:
        """GNFR-1: Containerized operation"""
        print("\nCheck: Docker deployment")
        dockerfile_exists = self._exists("Dockerfile")
        compose_exists = self._exists("docker-compose.yml")
        compose_has_ops_api = self._contains_all("docker-compose.yml", ["ops-api"])
        passed = dockerfile_exists and compose_exists and compose_has_ops_api
        details = (
            "Dockerfile and compose path with ops-api service found"
            if passed
            else (
                f"dockerfile_exists={dockerfile_exists}, "
                f"compose_exists={compose_exists}, "
                f"compose_has_ops_api={compose_has_ops_api}"
            )
        )
        return self._record(
            "docker_deployment",
            "GNFR-1: Full release runs through Docker Compose",
            passed,
            details,
        )

    def check_audit_logging(self) -> bool:
        """GR-6: Audit coverage"""
        print("\nCheck: Audit logging")
        audit_module_exists = self._contains_all(
            "acosplatform/audit/logger.py",
            ["def audit("],
        )
        api_uses_audit = self._contains_all(
            "apps/ops_api/main.py",
            ["audit(", "save_audit_event"],
        )
        passed = audit_module_exists and api_uses_audit
        details = (
            "Audit logger and API audit calls are present"
            if passed
            else (
                f"audit_module_exists={audit_module_exists}, "
                f"api_uses_audit={api_uses_audit}"
            )
        )
        return self._record(
            "audit_logging",
            "GR-6: Control-plane mutations and risky decisions generate audit evidence",
            passed,
            details,
        )

    def run_all_checks(self) -> dict[str, dict]:
        print("=" * 60)
        print("ACOS WEEK 12: PRODUCTION GATE VALIDATION")
        print(f"Repo root: {self.repo_root}")
        print("=" * 60)

        checks_methods = [
            self.check_workflow_versioning,
            self.check_run_version_tracking,
            self.check_ui_surfaces,
            self.check_authentication,
            self.check_observability,
            self.check_docker_deployment,
            self.check_audit_logging,
        ]
        for check_method in checks_methods:
            check_method()
        return self.checks

    def generate_evidence_artifact(self) -> dict:
        passed_checks = sum(1 for check in self.checks.values() if check.get("passed", False))
        total_checks = len(self.checks)
        runbook_paths = [
            "docs/RUNBOOK_GO_LIVE.md",
            "docs/RUNBOOK_WORKFLOW_PROMOTION.md",
            "docs/RUNBOOK_INCIDENT_RESPONSE.md",
        ]
        operational_runbooks = all(self._exists(path) for path in runbook_paths)
        rollback_plan = self._exists("docs/RUNBOOK_WORKFLOW_PROMOTION.md")
        week11_evidence_exists = bool(
            list(self._abs("deploy/k8s/observability/evidence").glob("week11-uat-*.json"))
        )

        return {
            "timestamp": self.timestamp,
            "week": 12,
            "phase": "production_gate",
            "production_readiness_checks": self.checks,
            "summary": {
                "checks_passed": passed_checks,
                "checks_total": total_checks,
                "overall_pass": passed_checks == total_checks,
                "readiness_percentage": int((passed_checks / total_checks) * 100) if total_checks else 0,
            },
            "go_live_requirements": {
                "versioned_resources": self.checks.get("workflow_versioning", {}).get("passed", False),
                "auditable_promotions": self.checks.get("audit_logging", {}).get("passed", False),
                "operational_runbooks": operational_runbooks,
                "rollback_plans": rollback_plan,
                "release_evidence": week11_evidence_exists,
                "docker_deployment": self.checks.get("docker_deployment", {}).get("passed", False),
            },
        }

    def save_evidence(self, artifact: dict) -> str:
        evidence_dir = self._abs("deploy/k8s/observability/evidence")
        evidence_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = self.timestamp.replace(":", "-").replace(".", "-")
        file_path = evidence_dir / f"week12-production-gate-{timestamp_str}.json"
        file_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
        return str(file_path)


def main() -> None:
    checker = ProductionGateChecker()
    checks = checker.run_all_checks()
    artifact = checker.generate_evidence_artifact()
    evidence_file = checker.save_evidence(artifact)

    print("\n" + "=" * 60)
    print("PRODUCTION GATE SUMMARY")
    print("=" * 60)
    summary = artifact["summary"]
    print(f"\nChecks Passed: {summary['checks_passed']}/{summary['checks_total']}")
    print(f"Readiness: {summary['readiness_percentage']}%")
    print("\nDetailed Results:")
    for check_name, check_result in checks.items():
        status = "PASS" if check_result.get("passed", False) else "FAIL"
        print(f"  [{status}] {check_result.get('requirement', check_name)}")
    print(f"\nEvidence Artifact: {evidence_file}")
    print("\nPRODUCTION GATE PASSED" if summary["overall_pass"] else "\nPRODUCTION GATE REVIEW REQUIRED")

    sys.exit(0 if summary["overall_pass"] else 1)


if __name__ == "__main__":
    main()
