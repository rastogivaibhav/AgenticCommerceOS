from fastapi.testclient import TestClient

from apps.ops_api.main import app
from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.northstar.repository import list_replay_runs


def test_northstar_replay_is_captured_and_rerunnable(monkeypatch, tmp_path):
    monkeypatch.setenv("ACOS_NORTHSTAR_SQLITE_PATH", str(tmp_path / "northstar.db"))
    result = run_omnichannel_turn(MessageEnvelope(
        tenant_id="replay-tenant",
        channel="web",
        channel_user_id="u1",
        customer_id="c1",
        text="I need an outfit for a winter wedding under £200, available for pickup near Reading",
    ))
    assert result["status"] == "success"
    replays = list_replay_runs(tenant_id="replay-tenant")
    assert replays
    client = TestClient(app)
    response = client.post(f"/api/northstar/replays/{replays[0]['id']}/rerun")
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"


def test_northstar_rbac_tenant_guard(monkeypatch):
    monkeypatch.setenv("ACOS_NORTHSTAR_REQUIRE_AUTH", "1")
    monkeypatch.setenv("ACOS_NORTHSTAR_API_KEYS", "viewer-key:tenant-a:viewer,ops-key:tenant-a:ops")
    client = TestClient(app)
    forbidden = client.post(
        "/api/northstar/messages",
        headers={"X-API-Key": "viewer-key"},
        json={"tenant_id": "tenant-a", "text": "hello"},
    )
    assert forbidden.status_code == 403
    cross_tenant = client.post(
        "/api/northstar/messages",
        headers={"X-API-Key": "ops-key"},
        json={"tenant_id": "tenant-b", "text": "hello"},
    )
    assert cross_tenant.status_code == 403


def test_graphql_rbac_middleware_blocks_when_enabled(monkeypatch):
    monkeypatch.setenv("ACOS_GRAPHQL_REQUIRE_AUTH", "1")
    monkeypatch.setenv("ACOS_GRAPHQL_API_KEYS", "viewer-key:tenant-a:viewer")
    client = TestClient(app)
    blocked = client.post("/graphql", json={"query": "{ tools { name } }"})
    assert blocked.status_code == 403
    allowed = client.post("/graphql", headers={"X-API-Key": "viewer-key"}, json={"query": "{ tools { name } }"})
    assert allowed.status_code == 200
