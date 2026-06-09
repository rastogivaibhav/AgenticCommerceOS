from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


READ_ONLY_TOOLS = {
    "catalog.search",
    "catalog.get_product",
    "inventory.check_stock",
    "orders.get_order",
    "orders.track_order",
    "returns.check_eligibility",
    "loyalty.get_balance",
    "pricing.calculate",
    "promotions.find_offers",
    "cart.get",
}

CUSTOMER_IMPACTING_TOOLS = {
    "cart.create",
    "cart.add_item",
    "cart.update",
    "cart.remove_item",
    "cart.apply_discount",
    "cart.apply_store_credit",
    "case.create",
}

HIGH_RISK_TOOLS = {
    "orders.create",
    "returns.create_return",
    "cart.complete",
    "payments.create",
}


@dataclass(frozen=True)
class ToolPolicyDecision:
    verdict: str
    risk_level: str
    reason: str
    required_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "required_approval": self.required_approval,
        }


def policy_enforcement_enabled() -> bool:
    return os.environ.get("ACOS_POLICY_ENFORCEMENT", "0").strip().lower() in {"1", "true", "yes", "on"}


def classify_tool(tool_name: str) -> str:
    if tool_name in HIGH_RISK_TOOLS:
        return "high"
    if tool_name in CUSTOMER_IMPACTING_TOOLS:
        return "medium"
    if tool_name in READ_ONLY_TOOLS:
        return "low"
    return "unknown"


def evaluate_tool_policy(tool_name: str, arguments: dict[str, Any] | None = None, *, context: dict[str, Any] | None = None) -> ToolPolicyDecision:
    arguments = arguments or {}
    context = context or {}
    risk = classify_tool(tool_name)
    approved = bool(context.get("approval_id") or context.get("policy_approved"))
    try:
        quantity = int(arguments.get("quantity", 1) or 1)
    except (TypeError, ValueError):
        quantity = 1

    if risk == "unknown":
        return ToolPolicyDecision(
            verdict="block" if policy_enforcement_enabled() else "allow",
            risk_level="unknown",
            reason="Unknown tools require registration before production use." if policy_enforcement_enabled() else "Unknown tool allowed in non-enforcing local mode.",
            required_approval=policy_enforcement_enabled(),
        )

    if risk == "high" and policy_enforcement_enabled() and not approved:
        return ToolPolicyDecision(
            verdict="require_approval",
            risk_level=risk,
            reason="High-risk commerce action requires explicit approval before execution.",
            required_approval=True,
        )

    if risk == "medium" and policy_enforcement_enabled() and quantity > 10:
        return ToolPolicyDecision(
            verdict="require_approval",
            risk_level=risk,
            reason="Large customer-impacting quantity change requires approval.",
            required_approval=True,
        )

    return ToolPolicyDecision(
        verdict="allow",
        risk_level=risk,
        reason="Tool execution is within configured policy.",
    )
