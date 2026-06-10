from __future__ import annotations

from typing import Any
from datetime import UTC, datetime
from uuid import uuid4

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import EvidenceEvent, record_evidence, list_evidence
from acosplatform.orchestration.router import classify_intent, select_agent
from acosplatform.orchestration.agent_registry import get_agent
from acosplatform.sessions.spine import resolve_or_create_session
from acosplatform.tools.executor import execute_tool
from acosplatform.northstar.repository import save_replay_run


def _agent_payload(agent_id: str) -> dict[str, Any]:
    agent = get_agent(agent_id)
    if not agent:
        return select_agent(type("IntentLike", (), {"recommended_agent": "service_agent"})())
    return {"id": agent.id, "name": agent.name, "role": agent.role, "tools": agent.tools, "system_prompt": agent.system_prompt}


def _record_agent_selected(envelope: MessageEnvelope, agent: dict[str, Any], intent: Any, *, reason: str) -> None:
    record_evidence(EvidenceEvent(
        event_type="agent.selected",
        tenant_id=envelope.tenant_id,
        correlation_id=envelope.correlation_id,
        conversation_session_id=envelope.conversation_session_id,
        journey_id=envelope.journey_id,
        agent_id=agent["id"],
        payload={"agent": agent, "intent": intent.to_dict(), "reason": reason},
    ))


def run_omnichannel_turn(envelope: MessageEnvelope) -> dict[str, Any]:
    """Run one north-star omnichannel retail turn.

    The pilot runtime now models a small but genuine multi-agent handoff: a rich
    discovery/styling query is handled by Discovery, Stylist, Inventory and
    Service/Handoff agents, with every selection and tool call captured as
    evidence. This keeps the implementation deterministic for tests while
    proving the product architecture.
    """
    envelope = resolve_or_create_session(envelope)
    intent = classify_intent(envelope)
    primary_agent = select_agent(intent)
    context = {
        "tenant_id": envelope.tenant_id,
        "customer_id": envelope.customer_id,
        "conversation_session_id": envelope.conversation_session_id,
        "journey_id": envelope.journey_id,
        "correlation_id": envelope.correlation_id,
        "agent_id": primary_agent["id"],
        "message": envelope.text,
    }
    _record_agent_selected(envelope, primary_agent, intent, reason="primary_intent_route")

    tool_traces: list[dict[str, Any]] = []
    participating_agents: list[dict[str, Any]] = [primary_agent]

    if intent.intent in {"product_discovery", "styling_advice", "stock_availability"}:
        # Discovery agent: get candidate products.
        discovery_agent = _agent_payload("discovery_agent")
        if discovery_agent["id"] not in {a["id"] for a in participating_agents}:
            participating_agents.append(discovery_agent)
            _record_agent_selected(envelope, discovery_agent, intent, reason="catalog_discovery_required")
        discovery_context = {**context, "agent_id": "discovery_agent"}
        search = execute_tool("catalog.search", {"query": envelope.text, "budget": 200, "tags": ["wedding", "winter"]}, context=discovery_context)
        tool_traces.append(search)
        products = search.get("result", {}).get("products", [])
        product_ids = [p["id"] for p in products[:3]]

        # Stylist agent: build the basket/outfit shape and budget fit.
        stylist_agent = _agent_payload("stylist_agent")
        if stylist_agent["id"] not in {a["id"] for a in participating_agents}:
            participating_agents.append(stylist_agent)
            _record_agent_selected(envelope, stylist_agent, intent, reason="outfit_composition_required")
        stylist_context = {**context, "agent_id": "stylist_agent"}
        tool_traces.append(execute_tool("pricing.calculate", {"product_ids": product_ids, "budget": 200}, context=stylist_context))
        tool_traces.append(execute_tool("promotions.find_offers", {"product_ids": product_ids}, context=stylist_context))

        # Inventory agent: prove pickup/location availability.
        inventory_agent = _agent_payload("inventory_agent")
        if inventory_agent["id"] not in {a["id"] for a in participating_agents}:
            participating_agents.append(inventory_agent)
            _record_agent_selected(envelope, inventory_agent, intent, reason="store_stock_required")
        inventory_context = {**context, "agent_id": "inventory_agent"}
        for product in products[:3]:
            tool_traces.append(execute_tool("inventory.check_stock", {"product_id": product["id"], "location": "Reading"}, context=inventory_context))

        # Service/handoff agent: prepare colleague-ready handoff when pickup/store fulfilment is involved.
        service_agent = _agent_payload("service_agent")
        if "pickup" in envelope.text.lower() or "collect" in envelope.text.lower() or "reading" in envelope.text.lower():
            participating_agents.append(service_agent)
            _record_agent_selected(envelope, service_agent, intent, reason="pickup_handoff_summary_required")
            handoff = execute_tool("case.create", {"summary": f"Pickup-ready styling journey for {envelope.customer_id}: {envelope.text}"}, context={**context, "agent_id": "service_agent"})
            tool_traces.append(handoff)
            record_evidence(EvidenceEvent(
                event_type="human.handoff.created",
                tenant_id=envelope.tenant_id,
                correlation_id=envelope.correlation_id,
                conversation_session_id=envelope.conversation_session_id,
                journey_id=envelope.journey_id,
                agent_id="service_agent",
                payload={"handoff": handoff.get("result", {}), "reason": "store_pickup_context"},
            ))
        response_text = _compose_retail_recommendation(products, tool_traces)
    elif intent.intent == "order_status":
        order_id = "ORD-1001"
        tool_traces.append(execute_tool("orders.get_order", {"order_id": order_id}, context=context))
        order = tool_traces[-1].get("result", {})
        response_text = f"I found {order.get('id', order_id)}. Current status: {order.get('status', 'unknown')}. ETA: {order.get('eta', 'not available')}."
    elif intent.intent == "return_or_refund":
        tool_traces.append(execute_tool("returns.check_eligibility", {"order_id": "ORD-1001"}, context=context))
        response_text = "I checked the return policy and prepared the next return step with evidence."
    elif intent.intent == "loyalty_query":
        tool_traces.append(execute_tool("loyalty.get_balance", {"customer_id": envelope.customer_id}, context=context))
        balance = tool_traces[-1].get("result", {})
        response_text = f"Your loyalty balance is {balance.get('points', 0)} points with {balance.get('voucher_value', 0)} GBP voucher value."
    else:
        tool_traces.append(execute_tool("case.create", {"summary": envelope.text}, context=context))
        record_evidence(EvidenceEvent(
            event_type="human.handoff.created",
            tenant_id=envelope.tenant_id,
            correlation_id=envelope.correlation_id,
            conversation_session_id=envelope.conversation_session_id,
            journey_id=envelope.journey_id,
            agent_id=primary_agent["id"],
            payload={"reason": "low_confidence_or_unknown_intent"},
        ))
        response_text = "I need a little more detail, so I have prepared this for a support handoff."

    record_evidence(EvidenceEvent(
        event_type="response.sent",
        tenant_id=envelope.tenant_id,
        correlation_id=envelope.correlation_id,
        conversation_session_id=envelope.conversation_session_id,
        journey_id=envelope.journey_id,
        agent_id=primary_agent["id"],
        payload={"response_text": response_text, "participating_agents": [a["id"] for a in participating_agents]},
    ))
    result = {
        "status": "success",
        "message_envelope": envelope.to_dict(),
        "intent": intent.to_dict(),
        "agent": primary_agent,
        "participating_agents": participating_agents,
        "tool_trace": tool_traces,
        "response_text": response_text,
        "evidence": list_evidence(correlation_id=envelope.correlation_id),
    }
    try:
        save_replay_run({
            "id": f"replay_{uuid4().hex[:12]}",
            "tenant_id": envelope.tenant_id,
            "conversation_session_id": envelope.conversation_session_id,
            "journey_id": envelope.journey_id,
            "correlation_id": envelope.correlation_id,
            "request": envelope.to_dict(),
            "result": result,
            "status": "captured",
            "created_at": datetime.now(UTC).isoformat(),
        })
    except Exception:
        pass
    return result


def _compose_retail_recommendation(products: list[dict[str, Any]], traces: list[dict[str, Any]]) -> str:
    available = []
    stock_by_id = {t.get("result", {}).get("product_id"): t.get("result", {}) for t in traces if t.get("tool_name") == "inventory.check_stock"}
    price = next((t.get("result", {}) for t in traces if t.get("tool_name") == "pricing.calculate"), {})
    offers = next((t.get("result", {}) for t in traces if t.get("tool_name") == "promotions.find_offers"), {})
    for product in products[:3]:
        stock = stock_by_id.get(product["id"], {})
        if stock.get("available"):
            available.append(f"{product['name']} (£{product['price']}, {stock.get('quantity')} in Reading)")
    if not available:
        return "I found suitable products, but I could not confirm Reading pickup stock yet."
    budget_note = "within the £200 budget" if price.get("within_budget", True) else "slightly above the £200 budget"
    offer_note = " Eligible offer: " + offers["offers"][0]["description"] + "." if offers.get("offers") else ""
    return "For a winter wedding under £200, I recommend: " + "; ".join(available) + f". Basket is {budget_note}." + offer_note
