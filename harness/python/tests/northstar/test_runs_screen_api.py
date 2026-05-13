from fastapi.testclient import TestClient

from apps.ops_api.main import app


def test_runs_endpoint_lists_captured_orchestration_runs():
    client = TestClient(app)
    created = client.post('/api/northstar/messages', json={
        'tenant_id': 'default',
        'channel': 'web',
        'channel_user_id': 'runs-api-user',
        'customer_id': 'runs-api-customer',
        'text': 'I need an outfit for a winter wedding under £200, available for pickup near Reading',
    })
    assert created.status_code == 200
    runs = client.get('/api/northstar/runs')
    assert runs.status_code == 200
    payload = runs.json()
    assert payload['runs']
    latest = payload['runs'][0]
    assert latest['agent_count'] >= 3
    assert latest['tool_count'] >= 5
    assert latest['evidence_count'] >= 8
    detail = client.get(f"/api/northstar/runs/{latest['id']}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload['run']['id'] == latest['id']
    assert detail_payload['result']['tool_trace']


def test_runs_endpoint_respects_viewer_role(monkeypatch):
    monkeypatch.setenv('ACOS_NORTHSTAR_REQUIRE_AUTH', '1')
    monkeypatch.setenv('ACOS_NORTHSTAR_API_KEYS', 'viewer-key:default:viewer')
    client = TestClient(app)
    response = client.get('/api/northstar/runs', headers={'X-API-Key': 'viewer-key'})
    assert response.status_code == 200
