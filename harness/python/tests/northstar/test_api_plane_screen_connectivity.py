from fastapi.testclient import TestClient

from apps.ops_api.main import app


def test_api_plane_matrix_lists_all_operator_screens_and_graphql_probe():
    client = TestClient(app)
    response = client.get('/api/northstar/api-plane')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'connected'
    routes = {screen['route'] for screen in payload['screens']}
    expected_routes = {
        '/ui/workflows',
        '/ui/studio-proof',
        '/ui/runs',
        '/ui/demo-guide',
        '/ui/test-center',
        '/ui/api-plane',
        '/ui/channels',
        '/ui/demo-routes',
        '/ui/agents',
        '/ui/skills',
        '/ui/analytics',
        '/ui/tenants',
        '/ui/experiments',
        '/ui/simulation',
    }
    assert expected_routes.issubset(routes)
    assert payload['summary']['connected'] == payload['summary']['screens']

    gql = client.post('/graphql', json={'query': '{ tools { name protocol } }'})
    assert gql.status_code == 200
    assert any(tool['name'] == 'catalog.search' for tool in gql.json()['data']['tools'])
