from __future__ import annotations

import re
from typing import Any

from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.evidence.store import EvidenceEvent, record_evidence
from acosplatform.orchestration.agent_registry import DEFAULT_AGENTS
from acosplatform.orchestration.contracts import IntentResult

_INTENT_RULES: list[tuple[str, str, str, list[str]]] = [
    ("return_or_refund", r"\b(return|refund|exchange)\b", "returns_agent", ["returns.check_eligibility"]),
    ("order_status", r"\b(order|delivery|where is|track|tracking|late)\b", "order_agent", ["orders.get_order"]),
    ("loyalty_query", r"\b(loyalty|points|voucher|reward)\b", "loyalty_agent", ["loyalty.get_balance"]),
    # Product/styling signals take precedence over pure stock keywords so a rich
    # query like "winter wedding outfit under £200 available for pickup" is routed
    # as a discovery/styling journey instead of a narrow stock lookup.
    ("styling_advice", r"\b(outfit|style|wedding|occasion|wear|match)\b", "stylist_agent", ["catalog.search", "inventory.check_stock", "pricing.calculate"]),
    ("product_discovery", r"\b(find|need|looking for|recommend|search|product|dress|shoes|coat)\b", "discovery_agent", ["catalog.search"]),
    ("stock_availability", r"\b(stock|available|availability|pickup|collect|store)\b", "inventory_agent", ["inventory.check_stock"]),
    ("complaint", r"\b(complaint|angry|unhappy|bad service|escalate)\b", "service_agent", ["case.create"]),
]


def classify_intent(envelope: MessageEnvelope) -> IntentResult:
    text = envelope.text.lower()
    missing: list[str] = []
    selected = IntentResult(
        intent="unknown",
        confidence=0.35,
        journey_stage="clarify",
        recommended_agent="service_agent",
        required_tools=["case.create"],
        missing_information=["clear customer intent"],
        needs_human=False,
        rationale="No high-confidence retail intent matched.",
    )
    for intent, pattern, agent, tools in _INTENT_RULES:
        if re.search(pattern, text):
            selected = IntentResult(
                intent=intent,
                confidence=0.86 if intent != "unknown" else 0.35,
                journey_stage="discovery" if intent in {"product_discovery", "styling_advice", "stock_availability"} else "service",
                recommended_agent=agent,
                required_tools=tools,
                rationale=f"Matched retail rule for {intent}.",
            )
            break

    if selected.intent in {"product_discovery", "styling_advice", "stock_availability"}:
        if not re.search(r"£|\bpound|\bbudget|under \d+|less than \d+", text):
            missing.append("budget")
        if "pickup" in text or "collect" in text:
            if not re.search(r"near\s+[a-zA-Z]+|in\s+[a-zA-Z]+|reading|london|manchester", text):
                missing.append("preferred store/location")
    selected.missing_information.extend(item for item in missing if item not in selected.missing_information)
    if selected.confidence < 0.5:
        selected.needs_human = True

    record_evidence(EvidenceEvent(
        event_type="intent.classified",
        tenant_id=envelope.tenant_id,
        correlation_id=envelope.correlation_id,
        conversation_session_id=envelope.conversation_session_id,
        journey_id=envelope.journey_id,
        agent_id=selected.recommended_agent,
        payload=selected.to_dict(),
    ))
    return selected


def select_agent(intent: IntentResult) -> dict[str, Any]:
    agent = DEFAULT_AGENTS.get(intent.recommended_agent) or DEFAULT_AGENTS["service_agent"]
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "tools": agent.tools,
        "system_prompt": agent.system_prompt,
    }
