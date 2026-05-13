from fastapi.testclient import TestClient
from apps.ops_api.main import app

client = TestClient(app)

def test_v2_agent_registry_and_cards():
    agents = client.get('/api/v2/agents').json()['agents']
    ids = {a['agent_id'] for a in agents}
    assert {'shopping_agent','returns_agent','mattress_recommender','nursery_advisor','gift_advisor'} <= ids
    card = client.get('/api/v2/agents/mattress_recommender/card').json()['agent_card']
    assert card['agent_id'] == 'mattress_recommender'
    assert any(s['skill_id'] == 'mattress.recommend' for s in card['skills'])

def test_v2_capability_registry_coverage():
    payload = client.get('/api/v2/capabilities').json()
    assert payload['summary']['covered'] >= 5
    caps = {c['capability_id']: c for c in payload['capabilities']}
    assert 'returns.check_eligibility' in caps
    assert 'returns_agent' in caps['returns.check_eligibility']['mapped_agents']

def test_v2_a2a_nursery_mattress_returns_demo():
    res = client.post('/api/v2/a2a/invoke', json={
        'message': 'I’m buying a cot mattress for a newborn under £250, and I need to know if my previous nursery order can be returned.',
        'channel': 'store_partner',
        'actor_type': 'partner',
        'channel_mode': 'store_partner_assist'
    })
    assert res.status_code == 200
    trace = res.json()['trace']
    agent_ids = {a['agent_id'] for a in trace['agents']}
    assert {'nursery_advisor','mattress_recommender','returns_agent'} <= agent_ids
    assert len(trace['tool_trace']) >= 3
    assert 'Partner assist' in trace['final_response']
    traces = client.get('/api/v2/a2a/traces').json()['traces']
    assert any(t['trace_id'] == trace['trace_id'] for t in traces)

def test_v2_channel_modes_evaluation_governance_finops_route():
    assert len(client.get('/api/v2/channel-modes').json()['channel_modes']) >= 3
    assert len(client.get('/api/v2/tone-profiles').json()['tone_profiles']) >= 3
    assert len(client.get('/api/v2/evaluations').json()['evaluations']) >= 5
    assert len(client.get('/api/v2/guardrails').json()['policies']) >= 3
    assert client.get('/api/v2/finops').json()['summary']['avg_cost_per_run'] > 0
    assert len(client.get('/api/v2/route-to-production').json()['agents']) >= 5


def test_v2_ui_routes_are_served():
    for route in ['/ui/estate','/ui/agent-registry','/ui/capabilities','/ui/a2a-trace','/ui/channel-modes','/ui/evaluations','/ui/governance']:
        assert client.get(route).status_code in {200, 503}
