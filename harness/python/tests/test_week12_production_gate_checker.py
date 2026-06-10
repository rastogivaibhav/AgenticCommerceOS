from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "week12_production_gate_checker.py"
SPEC = importlib.util.spec_from_file_location("week12_production_gate_checker", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)
ProductionGateChecker = MODULE.ProductionGateChecker


def _write(base: Path, rel_path: str, content: str = "") -> None:
    target = base / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_checker_default_repo_root_is_not_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    checker = ProductionGateChecker()
    assert (checker.repo_root / "scripts" / "week12_production_gate_checker.py").exists()


def test_checker_reports_full_pass_for_expected_contracts(tmp_path):
    _write(
        tmp_path,
        "acosplatform/workflows/service.py",
        "def create_workflow_version():\n    pass\nactive_version = 'v1'\nvalidation_status = 'approved'\n",
    )
    _write(
        tmp_path,
        "acosplatform/db/repository.py",
        "def save_workflow_version():\n    pass\n"
        "def save_run():\n    pass\n"
        "workflow_versions = []\n"
        "workflow_version = 'v1'\n"
        "version = 'v1'\n",
    )
    _write(tmp_path, "acosplatform/journey/engine.py", "workflow_version = 'v1'\n")
    _write(
        tmp_path,
        "apps/ops_ui_v2/src/App.jsx",
        "const routes = ['/workflows', '/simulation'];\n",
    )
    _write(tmp_path, "apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx", "export default {};\n")
    _write(tmp_path, "apps/ops_ui_v2/src/pages/WorkflowEditor.jsx", "export default {};\n")
    _write(tmp_path, "apps/ops_ui_v2/src/pages/Simulation.jsx", "export default {};\n")
    _write(tmp_path, "apps/ops_api/routers/northstar_api.py", "x=1\n")
    _write(tmp_path, "apps/ops_api/routers/uat_compat.py", "x=1\n")
    _write(tmp_path, "apps/ops_api/routers/v2_control_plane.py", "from fastapi import Depends\nfrom acosplatform.auth.api_key import require_ops_roles\nDepends(require_ops_roles('admin'))\n")
    _write(tmp_path, "acosplatform/auth/api_key.py", "def require_ops_roles(*args):\n    return args\n")
    _write(
        tmp_path,
        "apps/ops_api/main.py",
        "from acosplatform.auth.api_key import require_ops_roles\n"
        "from acosplatform.audit.logger import audit\n"
        "from acosplatform.db.repository import save_audit_event\n"
        "allow_headers=['Authorization']\n"
        "@app.get('/health')\n"
        "def h():\n    pass\n"
        "@app.get('/metrics')\n"
        "def m():\n    pass\n"
        "audit('x')\n"
        "save_audit_event('a','b','c','d')\n",
    )
    _write(tmp_path, "acosplatform/observability/metrics.py", "def metrics_endpoint():\n    return {}\n")
    _write(tmp_path, "acosplatform/audit/logger.py", "def audit(*args, **kwargs):\n    return None\n")
    _write(tmp_path, "Dockerfile", "FROM python:3.11\n")
    _write(tmp_path, "docker-compose.yml", "services:\n  ops-api:\n    image: x\n")
    _write(
        tmp_path,
        "deploy/k8s/observability/evidence/week11-uat-test.json",
        '{"ok": true}\n',
    )

    checker = ProductionGateChecker(repo_root=tmp_path)
    checker.run_all_checks()
    artifact = checker.generate_evidence_artifact()

    assert artifact["summary"]["checks_passed"] == artifact["summary"]["checks_total"] == 7
    assert artifact["summary"]["overall_pass"] is True
    assert artifact["go_live_requirements"]["release_evidence"] is True
    assert artifact["go_live_requirements"]["operational_runbooks"] is False


def test_checker_records_missing_controls_and_saves_artifact(tmp_path):
    _write(tmp_path, "Dockerfile", "FROM python:3.11\n")
    _write(tmp_path, "docker-compose.yml", "services:\n  ops-api:\n    image: x\n")

    checker = ProductionGateChecker(repo_root=tmp_path)
    checker.run_all_checks()
    artifact = checker.generate_evidence_artifact()
    path = checker.save_evidence(artifact)

    assert artifact["summary"]["checks_total"] == 7
    assert artifact["summary"]["checks_passed"] < artifact["summary"]["checks_total"]
    assert artifact["summary"]["overall_pass"] is False
    assert Path(path).exists()
    assert "week12-production-gate-" in Path(path).name
