from fastapi.testclient import TestClient

from apps.ops_api.main import app


def test_demo_script_endpoint_explains_buyer_demo_path():
    client = TestClient(app)
    response = client.get('/api/northstar/demo-script')
    assert response.status_code == 200
    payload = response.json()
    assert payload['title'] == 'ACOS North-Star CTO Demo'
    assert payload['demo_message']
    assert len(payload['storyboard']) >= 5
    assert any('make smoke-northstar' in cmd for cmd in payload['demo_commands'])
    assert any('Evidence' in item['screen'] or 'Studio Proof' in item['screen'] for item in payload['storyboard'])


def test_test_plan_endpoint_lists_runtime_ui_db_and_mcp_checks():
    client = TestClient(app)
    response = client.get('/api/northstar/test-plan')
    assert response.status_code == 200
    payload = response.json()
    checks = payload['checks']
    ids = {check['id'] for check in checks}
    assert {'smoke.golden_journey', 'ui.build', 'db.migration_sql', 'compose.prod', 'mcp.client', 'graphql.studio'}.issubset(ids)
    assert payload['hardening']['summary']['phase_count'] == 7


def test_hardening_gates_endpoint_lists_all_enterprise_phases():
    client = TestClient(app)
    response = client.get('/api/northstar/hardening-gates')
    assert response.status_code == 200
    payload = response.json()
    phases = payload['phases']
    assert len(phases) == 7
    titles = {phase['title'] for phase in phases}
    assert 'Enterprise Identity, RBAC, And Secure Defaults' in titles
    assert 'Tenant Isolation And Data Boundaries' in titles
    assert 'Connector Certification' in titles
    assert 'Business Outcome Proof' in titles
    assert all(phase['total_gates'] >= 4 for phase in phases)
    assert payload['summary']['external_blockers'] >= 1
