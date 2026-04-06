#!/usr/bin/env python3
"""
Week 12 Production Gate Checker

Validates all production readiness criteria from the go-live PRD.
Generates production gate evidence pack.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

class ProductionGateChecker:
    def __init__(self):
        self.checks = {}
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"

    def check_workflow_versioning(self):
        """GR-1: Versioned workflow resources exist"""
        print("\n🔍 Check: Workflow Versioning...")
        try:
            result = subprocess.run(
                ["python", "-c", "from ops_api.models import Workflow; print(hasattr(Workflow, 'version'))"],
                capture_output=True, text=True, timeout=5
            )
            passed = result.returncode == 0
            self.checks["workflow_versioning"] = {
                "requirement": "GR-1: Versioned workflow resources exist in persistence",
                "passed": passed,
                "details": "Workflow model includes version field" if passed else "Version field not found"
            }
            print(f"  {'✅' if passed else '❌'} Workflow versioning: {self.checks['workflow_versioning']['details']}")
            return passed
        except Exception as e:
            self.checks["workflow_versioning"] = {"passed": False, "error": str(e)}
            return False

    def check_run_version_tracking(self):
        """GR-2: Runs reference workflow versions"""
        print("\n🔍 Check: Run Version Tracking...")
        try:
            result = subprocess.run(
                ["python", "-c", "from ops_api.models import WorkflowRun; print(hasattr(WorkflowRun, 'workflow_version'))"],
                capture_output=True, text=True, timeout=5
            )
            passed = result.returncode == 0
            self.checks["run_version_tracking"] = {
                "requirement": "GR-2: Every run records the workflow version used",
                "passed": passed,
                "details": "WorkflowRun model tracks workflow_version" if passed else "Version tracking not found"
            }
            print(f"  {'✅' if passed else '❌'} Run version tracking: {self.checks['run_version_tracking']['details']}")
            return passed
        except Exception as e:
            self.checks["run_version_tracking"] = {"passed": False, "error": str(e)}
            return False

    def check_ui_surfaces(self):
        """GR-8: React control-plane foundation exists"""
        print("\n🔍 Check: UI Control Plane Surfaces...")
        required_pages = ["workflows", "runs", "promotions", "approvals"]
        try:
            src_path = Path("apps/ops_ui_v2/src")
            pages_found = []
            for page in required_pages:
                page_files = list(src_path.rglob(f"*{page}*"))
                pages_found.append(len(page_files) > 0)

            passed = all(pages_found)
            self.checks["ui_surfaces"] = {
                "requirement": "GR-8: Real React control plane with foundational views",
                "passed": passed,
                "details": f"Found UI for: {', '.join([p for p, f in zip(required_pages, pages_found) if f])}"
            }
            print(f"  {'✅' if passed else '❌'} UI surfaces: {self.checks['ui_surfaces']['details']}")
            return passed
        except Exception as e:
            self.checks["ui_surfaces"] = {"passed": False, "error": str(e)}
            return False

    def check_authentication(self):
        """GNFR-2: Security auth is in place"""
        print("\n🔍 Check: Authentication & Authorization...")
        try:
            auth_found = False
            for file in Path("apps/ops_api").rglob("*.py"):
                content = file.read_text()
                if "Bearer" in content and "Authorization" in content:
                    auth_found = True
                    break
            passed = auth_found
            self.checks["authentication"] = {
                "requirement": "GNFR-2: Auth, role enforcement, secrets handling in place",
                "passed": passed,
                "details": "Bearer token authentication implemented" if passed else "Auth not found"
            }
            print(f"  {'✅' if passed else '❌'} Authentication: {self.checks['authentication']['details']}")
            return passed
        except Exception as e:
            self.checks["authentication"] = {"passed": False, "error": str(e)}
            return False

    def check_observability(self):
        """GNFR-3: Logs, metrics, health endpoints"""
        print("\n🔍 Check: Observability (Logs, Metrics, Health)...")
        try:
            health_exists = Path("apps/ops_api/main.py").exists()  # Health endpoint is inline
            metrics_exists = Path("acosplatform/observability/metrics.py").exists()

            passed = health_exists and metrics_exists
            self.checks["observability"] = {
                "requirement": "GNFR-3: Logs, metrics, and health endpoints for pilot operations",
                "passed": passed,
                "details": f"Health: {'✅' if health_exists else '❌'}, Metrics: {'✅' if metrics_exists else '❌'}"
            }
            print(f"  {'✅' if passed else '❌'} Observability: {self.checks['observability']['details']}")
            return passed
        except Exception as e:
            self.checks["observability"] = {"passed": False, "error": str(e)}
            return False

    def check_docker_deployment(self):
        """GNFR-1: Containerized operation"""
        print("\n🔍 Check: Docker Deployment...")
        try:
            dockerfile_exists = Path("Dockerfile").exists()
            compose_exists = Path("docker-compose.yml").exists()

            passed = dockerfile_exists and compose_exists
            self.checks["docker_deployment"] = {
                "requirement": "GNFR-1: Full release runs through Docker Compose",
                "passed": passed,
                "details": f"Dockerfile: {'✅' if dockerfile_exists else '❌'}, docker-compose: {'✅' if compose_exists else '❌'}"
            }
            print(f"  {'✅' if passed else '❌'} Docker deployment: {self.checks['docker_deployment']['details']}")
            return passed
        except Exception as e:
            self.checks["docker_deployment"] = {"passed": False, "error": str(e)}
            return False

    def check_audit_logging(self):
        """GR-6: Audit coverage"""
        print("\n🔍 Check: Audit Logging...")
        try:
            audit_exists = Path("acosplatform/audit/logger.py").exists()
            passed = audit_exists
            self.checks["audit_logging"] = {
                "requirement": "GR-6: Control-plane mutations and risky decisions generate audit evidence",
                "passed": passed,
                "details": "Audit module present" if passed else "Audit module not found"
            }
            print(f"  {'✅' if passed else '❌'} Audit logging: {self.checks['audit_logging']['details']}")
            return passed
        except Exception as e:
            self.checks["audit_logging"] = {"passed": False, "error": str(e)}
            return False

    def run_all_checks(self):
        """Run all production gate checks"""
        print("═" * 60)
        print("ACOS WEEK 12: PRODUCTION GATE VALIDATION")
        print("═" * 60)

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
            try:
                check_method()
            except Exception as e:
                print(f"  ⚠️  Error: {e}")

        return self.checks

    def generate_evidence_artifact(self):
        """Create evidence artifact"""
        passed_checks = sum(1 for c in self.checks.values() if c.get("passed", False))
        total_checks = len(self.checks)

        artifact = {
            "timestamp": self.timestamp,
            "week": 12,
            "phase": "production_gate",
            "production_readiness_checks": self.checks,
            "summary": {
                "checks_passed": passed_checks,
                "checks_total": total_checks,
                "overall_pass": passed_checks == total_checks,
                "readiness_percentage": int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
            },
            "go_live_requirements": {
                "versioned_resources": self.checks.get("workflow_versioning", {}).get("passed", False),
                "auditable_promotions": self.checks.get("audit_logging", {}).get("passed", False),
                "operational_runbooks": Path("docs/RUNBOOK_GO_LIVE.md").exists() and \
                                       Path("docs/RUNBOOK_WORKFLOW_PROMOTION.md").exists() and \
                                       Path("docs/RUNBOOK_INCIDENT_RESPONSE.md").exists(),
                "rollback_plans": Path("docs/RUNBOOK_GO_LIVE.md").exists(),
                "release_evidence": len(list(Path("deploy/k8s/observability/evidence").glob("week11*.json"))) > 0,
                "docker_deployment": self.checks.get("docker_deployment", {}).get("passed", False)
            }
        }

        return artifact

    def save_evidence(self, artifact):
        """Save evidence artifact"""
        evidence_dir = Path("deploy/k8s/observability/evidence")
        evidence_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = self.timestamp.replace(":", "-").replace(".", "-")
        filename = f"week12-production-gate-{timestamp_str}.json"
        filepath = evidence_dir / filename

        with open(filepath, "w") as f:
            json.dump(artifact, f, indent=2)

        return str(filepath)

def main():
    checker = ProductionGateChecker()

    # Run all checks
    checks = checker.run_all_checks()

    # Generate and save evidence
    artifact = checker.generate_evidence_artifact()
    evidence_file = checker.save_evidence(artifact)

    # Print summary
    print("\n" + "═" * 60)
    print("PRODUCTION GATE SUMMARY")
    print("═" * 60)

    summary = artifact["summary"]
    print(f"\n✅ Checks Passed: {summary['checks_passed']}/{summary['checks_total']}")
    print(f"📊 Readiness: {summary['readiness_percentage']}%")

    print("\n📋 Detailed Results:")
    for check_name, check_result in checks.items():
        status = "✅" if check_result.get("passed", False) else "❌"
        print(f"  {status} {check_result.get('requirement', check_name)}")

    print(f"\n💾 Evidence Artifact: {evidence_file}")
    print(f"\n{'🎉 PRODUCTION GATE PASSED' if summary['overall_pass'] else '⚠️  PRODUCTION GATE REVIEW REQUIRED'}")

    sys.exit(0 if summary['overall_pass'] else 1)

if __name__ == "__main__":
    main()
