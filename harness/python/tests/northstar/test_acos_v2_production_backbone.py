from fastapi.testclient import TestClient
from apps.ops_api.main import app

client = TestClient(app)

def test_v2_missing_production_apis_exist_and_work():
    version = client.post('/api/v2/agents/mattress_recommender/versions', json={'version':'1.0.1','notes':'hardening'}).json()['version']
    assert version['agent_id'] == 'mattress_recommender'
    assert client.post('/api/v2/agents/mattress_recommender/promote', json={'target_stage':'production'}).status_code == 200
    assert client.post('/api/v2/agents/gift_advisor/retire').json()['agent']['status'] == 'retired'
    assert client.get('/api/v2/capabilities/coverage').json()['covered'] >= 5

def test_v2_a2a_task_lifecycle_and_vendor_kill_switch():
    created = client.post('/api/v2/vendor-agents', json={'name':'Mock Beauty Vendor','vendor_agent_id':'vendor_beauty_test','allowed_capabilities':['shopping.find_products']}).json()['vendor_agent']
    assert created['vendor_agent_id'] == 'vendor_beauty_test'
    res = client.post('/api/v2/a2a/tasks', json={'message':'Need a cot mattress under £250 and previous order return', 'vendor_agent_id':'vendor_beauty_test'})
    assert res.status_code == 200
    payload = res.json()
    assert payload['tasks']
    task_id = payload['tasks'][0]['task_id']
    assert client.get(f'/api/v2/a2a/tasks/{task_id}').json()['task']['status'] == 'completed'
    killed = client.post('/api/v2/vendor-agents/vendor_beauty_test/kill-switch').json()['vendor_agent']
    assert killed['kill_switch'] is True

def test_v2_tools_memory_evaluation_apis():
    assert client.get('/api/v2/tools').json()['tools']
    assert client.get('/api/v2/mcp/servers').json()['mcp_servers']
    assert client.get('/api/v2/memory/session/demo-session').json()['memory']
    assert client.get('/api/v2/memory/journey/demo-journey').json()['memory']
    run = client.post('/api/v2/evaluations/run', json={'agent_id':'mattress_recommender'}).json()['evaluation_run']
    assert run['status'] == 'pass'
    assert client.get(f"/api/v2/evaluations/{run['run_id']}").json()['evaluation_run']['agent_id'] == 'mattress_recommender'

def test_v2_new_ui_routes_are_served():
    for route in ['/ui/tool-registry','/ui/memory','/ui/tone','/ui/finops','/ui/route-to-production']:
        assert client.get(route).status_code in {200, 503}
