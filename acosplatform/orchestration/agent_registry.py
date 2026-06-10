from __future__ import annotations

from acosplatform.orchestration.contracts import AgentDefinition

DEFAULT_AGENTS: dict[str, AgentDefinition] = {
    "discovery_agent": AgentDefinition(
        id="discovery_agent",
        name="Discovery Agent",
        role="Finds suitable products and alternatives.",
        intent_families=["product_discovery", "stock_availability", "price_or_promotion"],
        tools=["catalog.search", "catalog.get_product", "inventory.check_stock", "pricing.calculate"],
        system_prompt="Help customers discover products with evidence-backed options.",
    ),
    "stylist_agent": AgentDefinition(
        id="stylist_agent",
        name="Stylist Agent",
        role="Builds outfits, bundles, and recommendations.",
        intent_families=["styling_advice", "product_discovery"],
        tools=["catalog.search", "inventory.check_stock", "promotions.find_offers"],
        system_prompt="Create practical retail styling recommendations under customer constraints.",
    ),
    "inventory_agent": AgentDefinition(
        id="inventory_agent",
        name="Inventory Agent",
        role="Checks store and online stock availability.",
        intent_families=["stock_availability"],
        tools=["inventory.check_stock"],
        system_prompt="Return precise availability and substitution evidence.",
    ),
    "order_agent": AgentDefinition(
        id="order_agent",
        name="Order Agent",
        role="Handles order lookup, status, and delivery issues.",
        intent_families=["order_status", "delivery_issue"],
        tools=["orders.get_order", "orders.track_order"],
        system_prompt="Resolve order questions using order evidence before responding.",
    ),
    "returns_agent": AgentDefinition(
        id="returns_agent",
        name="Returns Agent",
        role="Handles returns, refunds, and exchanges.",
        intent_families=["return_or_refund"],
        tools=["returns.check_eligibility", "case.create"],
        system_prompt="Prepare governed return paths without unauthorized refunds.",
    ),
    "loyalty_agent": AgentDefinition(
        id="loyalty_agent",
        name="Loyalty Agent",
        role="Handles points, vouchers, and member benefits.",
        intent_families=["loyalty_query"],
        tools=["loyalty.get_balance", "promotions.find_offers"],
        system_prompt="Explain loyalty benefits accurately with account evidence.",
    ),
    "service_agent": AgentDefinition(
        id="service_agent",
        name="Service Agent",
        role="Handles complaints, cases, and human handoff.",
        intent_families=["complaint", "human_handoff", "unknown"],
        tools=["case.create"],
        system_prompt="Summarize customer context and route to the right support queue.",
    ),
}


def get_agent(agent_id: str) -> AgentDefinition | None:
    return DEFAULT_AGENTS.get(agent_id)


def list_agents() -> list[AgentDefinition]:
    return list(DEFAULT_AGENTS.values())
