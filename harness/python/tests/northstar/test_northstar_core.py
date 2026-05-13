from fastapi.testclient import TestClient

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import clear_evidence, list_evidence
from acosplatform.mcp.tool_router import call_mcp_tool, list_local_mcp_tools
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.sessions.spine import resolve_or_create_session
from apps.mcp_server.main import app as mcp_app
from apps.ops_api.main import app as ops_app


def test_session_spine_creates_session_journey_and_evidence():
    clear_evidence()
    env = resolve_or_create_session(MessageEnvelope(tenant_id="t1", channel="web", channel_user_id="u1", text="hello"))
    assert env.conversation_session_id.startswith("sess_")
    assert env.journey_id.startswith("journey_")
    assert any(e["event_type"] == "message.received" for e in list_evidence(correlation_id=env.correlation_id))


def test_golden_retail_journey_runs_multiple_tools_and_evidence():
    clear_evidence()
    result = run_omnichannel_turn(MessageEnvelope(
        tenant_id="pilot",
        channel="web",
        channel_user_id="cust-1",
        customer_id="cust-1",
        text="I need an outfit for a winter wedding under £200, available for pickup near Reading",
    ))
    assert result["status"] == "success"
    assert result["intent"]["intent"] in {"styling_advice", "stock_availability", "product_discovery"}
    assert len(result["tool_trace"]) >= 2
    assert "Reading" in result["response_text"]
    event_types = {e["event_type"] for e in result["evidence"]}
    assert {"message.received", "intent.classified", "agent.selected", "tool.called", "response.sent"}.issubset(event_types)


def test_mcp_local_tools_are_discoverable_and_callable():
    tools = list_local_mcp_tools()
    assert any(t["name"] == "catalog.search" for t in tools)
    result = call_mcp_tool("local-retail", "catalog.search", {"query": "winter wedding", "budget": 200}, context={"tenant_id": "pilot", "correlation_id": "corr-test"})
    assert result["status"] == "success"
    assert result["protocol"] == "mcp"


def test_mcp_server_json_rpc_tools_list_and_call():
    client = TestClient(mcp_app)
    listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert listed.status_code == 200
    assert any(t["name"] == "catalog.search" for t in listed.json()["result"]["tools"])
    called = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "catalog.search", "arguments": {"query": "wedding", "budget": 200}}})
    assert called.status_code == 200
    assert called.json()["result"]["structuredContent"]["status"] == "success"


def test_ops_api_northstar_and_graphql_are_available():
    client = TestClient(ops_app)
    resp = client.post("/api/northstar/messages", json={"tenant_id": "pilot", "channel": "web", "channel_user_id": "u2", "text": "Find me a winter wedding outfit under £200 near Reading"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    gql = client.post("/graphql", json={"query": "{ tools { name protocol } }"})
    assert gql.status_code == 200
    assert any(t["name"] == "catalog.search" for t in gql.json()["data"]["tools"])
