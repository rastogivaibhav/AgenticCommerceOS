import importlib

from fastapi.testclient import TestClient

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import clear_evidence, list_evidence
from acosplatform.northstar import repository
from acosplatform.sessions.spine import resolve_or_create_session, get_session, list_messages
from apps.mcp_server.main import app as mcp_app
from apps.ops_api.main import app as ops_app


def test_northstar_state_is_durable_via_repository(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_NORTHSTAR_SQLITE_PATH", str(tmp_path / "northstar.db"))
    repository.reset_all()
    envelope = resolve_or_create_session(MessageEnvelope(
        tenant_id="tenant-durable",
        channel="web",
        channel_user_id="user-1",
        text="Find a winter wedding outfit near Reading",
    ))
    assert get_session(envelope.conversation_session_id)["tenant_id"] == "tenant-durable"
    assert list_messages(conversation_session_id=envelope.conversation_session_id)[0]["message_id"] == envelope.message_id

    persisted_session = repository.get_session(envelope.conversation_session_id)
    persisted_events = repository.list_evidence_events(correlation_id=envelope.correlation_id)
    assert persisted_session["channel_identities"]["web"] == "user-1"
    assert any(e["event_type"] == "message.received" for e in persisted_events)


def test_northstar_optional_auth_blocks_when_enabled(monkeypatch):
    monkeypatch.setenv("ACOS_NORTHSTAR_REQUIRE_AUTH", "1")
    monkeypatch.setenv("ACOS_NORTHSTAR_API_KEYS", "northstar-secret")
    client = TestClient(ops_app)
    blocked = client.get("/api/northstar/tools")
    assert blocked.status_code == 403
    allowed = client.get("/api/northstar/tools", headers={"X-API-Key": "northstar-secret"})
    assert allowed.status_code == 200


def test_mcp_optional_auth_blocks_when_enabled(monkeypatch):
    monkeypatch.setenv("ACOS_MCP_REQUIRE_AUTH", "1")
    monkeypatch.setenv("ACOS_MCP_API_KEYS", "mcp-secret")
    client = TestClient(mcp_app)
    blocked = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert blocked.status_code == 403
    allowed = client.post(
        "/mcp",
        headers={"X-API-Key": "mcp-secret"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    assert allowed.status_code == 200
    assert "tools" in allowed.json()["result"]
