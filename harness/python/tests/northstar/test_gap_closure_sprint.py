from __future__ import annotations

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import clear_evidence, list_evidence
from acosplatform.events.outbox import list_pending
from acosplatform.orchestration.runtime import run_omnichannel_turn
from acosplatform.tools.executor import execute_tool
from apps.ops_api.graphql.schema import schema


def setup_function():
    clear_evidence()


def test_golden_journey_uses_multiple_agents_and_handoff():
    result = run_omnichannel_turn(MessageEnvelope(
        tenant_id="tenant_test",
        channel="web",
        channel_user_id="user-1",
        customer_id="cust-1",
        text="I need an outfit for a winter wedding under £200, available for pickup near Reading",
    ))
    assert result["status"] == "success"
    agents = {agent["id"] for agent in result["participating_agents"]}
    assert {"discovery_agent", "stylist_agent", "inventory_agent", "service_agent"}.issubset(agents)
    tool_names = {trace["tool_name"] for trace in result["tool_trace"]}
    assert {"catalog.search", "pricing.calculate", "promotions.find_offers", "inventory.check_stock", "case.create"}.issubset(tool_names)
    event_types = {event["event_type"] for event in result["evidence"]}
    assert "human.handoff.created" in event_types


def test_outbox_receives_message_event():
    result = run_omnichannel_turn(MessageEnvelope(tenant_id="tenant_test", channel="web", channel_user_id="user-2", text="Where is my order ORD-1001?"))
    pending = list_pending()
    assert any(item["event_type"] == "message.received" and item["aggregate_id"] == result["message_envelope"]["conversation_session_id"] for item in pending)


def test_extended_retail_tools_create_evidence():
    context = {"tenant_id": "tenant_test", "correlation_id": "corr_tools", "agent_id": "stylist_agent"}
    price = execute_tool("pricing.calculate", {"product_ids": ["sku_dress_navy_01", "sku_shawl_silver_01"], "budget": 200}, context=context)
    offers = execute_tool("promotions.find_offers", {"product_ids": ["sku_dress_navy_01"]}, context=context)
    assert price["result"]["within_budget"] is True
    assert offers["result"]["offers"]
    evidence = list_evidence(correlation_id="corr_tools")
    assert len([event for event in evidence if event["event_type"] == "tool.called"]) == 2


def test_graphql_dry_run_and_generate_agent_mutations():
    dry_run = schema.execute_sync(
        '''mutation { runDryTest(input: {text: "I need an outfit for a winter wedding under £200, available for pickup near Reading", tenantId: "tenant_graphql"}) { ok status payload { key value } } }'''
    )
    assert dry_run.errors is None
    assert dry_run.data["runDryTest"]["ok"] is True
    payload = {item["key"]: item["value"] for item in dry_run.data["runDryTest"]["payload"]}
    assert int(payload["tool_count"]) >= 5
    assert "discovery_agent" in payload["participating_agents"]

    generated = schema.execute_sync(
        '''mutation { generateAgent(input: {intent: "returns", name: "Returns Concierge"}) { ok status payload { key value } } }'''
    )
    assert generated.errors is None
    assert generated.data["generateAgent"]["ok"] is True
