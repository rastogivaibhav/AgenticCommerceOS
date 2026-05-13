from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient

from apps.ops_api.main import app as ops_app


def test_studio_proof_endpoint_proves_runtime_and_studio_capabilities():
    client = TestClient(ops_app)
    response = client.get('/api/northstar/studio-proof')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ready'
    assert payload['readiness']['multi_agent_orchestration'] is True
    assert payload['readiness']['retail_tools'] is True
    assert payload['readiness']['human_handoff'] is True
    assert payload['studio_capabilities']['tabbed_inspector'] is True
    assert payload['studio_capabilities']['mcp_tool_browser'] is True
    assert len(payload['golden_journey']['participating_agents']) >= 3
    assert len(payload['golden_journey']['tool_trace']) >= 5


def test_northstar_handoffs_outbox_and_readiness_endpoints():
    client = TestClient(ops_app)
    client.get('/api/northstar/studio-proof')
    handoffs = client.get('/api/northstar/handoffs')
    assert handoffs.status_code == 200
    assert handoffs.json()['handoffs']

    outbox = client.get('/api/northstar/outbox')
    assert outbox.status_code == 200
    assert 'pending' in outbox.json()

    readiness = client.get('/api/northstar/readiness')
    assert readiness.status_code == 200
    checks = readiness.json()['checks']
    assert checks['production_compose_present'] is True
    assert checks['northstar_schema_present'] is True


def test_production_runtime_check_script_passes():
    root = Path(__file__).resolve().parents[4]
    proc = subprocess.run([sys.executable, 'scripts/production_runtime_check.py'], cwd=root, text=True, capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (root / 'docs' / 'release' / 'production-runtime-check.json').exists()
