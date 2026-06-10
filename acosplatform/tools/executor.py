import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4
from acosplatform.evidence.store import EvidenceEvent, record_evidence
from acosplatform.retail import mock_store
from acosplatform.retail_ops.tools import execute_retail_tool
from acosplatform.integrations.spree.client import execute_spree_tool
from acosplatform.integrations.stripe.client import execute_stripe_tool

def execute_tool(tool_name: str, arguments: dict[str, Any] | None = None, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    arguments = arguments or {}; context = context or {}; started = datetime.now(UTC); status = "success"
    provider = os.environ.get("ACOS_RETAIL_PROVIDER", "mock")
    
    try:
        # Check for Stripe Tool
        if tool_name.startswith("payments."):
            result = execute_stripe_tool(tool_name, arguments)
        # Check for Spree Override
        elif provider == "spree" and tool_name in {"catalog.search", "inventory.check_stock", "orders.get_order"}:
            result = execute_spree_tool(tool_name, arguments)
            if tool_name == "catalog.search" and isinstance(result, list):
                result = {"products": result}
        # Priority: New Real Retail Mock API Tools
        elif tool_name in {"catalog.search", "inventory.check_stock", "loyalty.get_balance", "orders.create"}:
            result = execute_retail_tool(tool_name, arguments)
            # Normalize result for ACOS runtime if needed
            if tool_name == "catalog.search" and isinstance(result, list):
                result = {"products": result}
        # Fallback: Native Mock Store
        elif tool_name == "catalog.get_product":
            result = mock_store.get_product(arguments.get("product_id", ""))
        elif tool_name == "pricing.calculate":
            result = mock_store.calculate_price(arguments.get("product_ids") or [], budget=arguments.get("budget"))
        elif tool_name == "promotions.find_offers":
            result = mock_store.find_offers(arguments.get("product_ids") or [])
        elif tool_name in {"orders.get_order", "orders.track_order"}:
            result = mock_store.get_order(arguments.get("order_id", "ORD-1001"))
        elif tool_name == "returns.check_eligibility":
            result = mock_store.returns_eligibility(arguments.get("order_id", "ORD-1001"))
        elif tool_name == "returns.create_return":
            result = mock_store.create_return(arguments.get("order_id", "ORD-1001"), reason=arguments.get("reason", "customer_request"))
        elif tool_name == "case.create":
            result = {"case_id": f"case_{uuid4().hex[:8]}", "status": "open", "summary": arguments.get("summary") or context.get("message")}
        else:
            status = "warning"; result = {"message": f"Unsupported tool {tool_name}"}
    except Exception as exc:
        status = "error"; result = {"error": exc.__class__.__name__, "message": str(exc)}
    
    latency_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
    trace = {"tool_trace_id": f"tool_{uuid4().hex[:12]}", "tool_name": tool_name, "protocol": "native", "status": status, "latency_ms": latency_ms, "arguments": arguments, "result": result, "policy_verdict": "allow"}
    record_evidence(EvidenceEvent(event_type="tool.called", tenant_id=context.get("tenant_id", "default"), correlation_id=context.get("correlation_id", "corr_local"), conversation_session_id=context.get("conversation_session_id"), journey_id=context.get("journey_id"), agent_id=context.get("agent_id"), tool_name=tool_name, policy_verdict="allow", payload=trace))
    return trace
