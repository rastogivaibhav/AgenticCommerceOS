"""Returns plugin – return flow with validation and refund calculation."""

import uuid
from datetime import datetime, timedelta, UTC

from acosplatform.plugins.orders import get_order

RETURN_WINDOW_DAYS = 30
RESTOCKING_FEE_RATE = 0.10  # 10% restocking fee for opened items

_return_records = []


def run(ctx):
    """Process a return request.

    ctx keys:
        order_id: str
        reason: str (optional)
        items: list of product_ids to return (optional, defaults to all items)
        condition: str ('unopened' or 'opened')
    """
    order_id = ctx.get("order_id")
    reason = ctx.get("reason", "Customer request")
    return_items = ctx.get("items")
    condition = ctx.get("condition", "opened")

    if not order_id:
        return {"success": False, "error": "order_id is required"}

    order = get_order(order_id)
    if not order:
        return {"success": False, "error": f"Order {order_id} not found"}

    # Check return window
    placed_str = order.get("placed_at", "")
    if placed_str:
        try:
            placed_at = datetime.fromisoformat(placed_str)
            if datetime.now(UTC) - placed_at.replace(tzinfo=UTC) > timedelta(days=RETURN_WINDOW_DAYS):
                return {
                    "success": False,
                    "error": f"Return window of {RETURN_WINDOW_DAYS} days has expired",
                    "placed_at": placed_str,
                    "days_since_order": (datetime.now(UTC) - placed_at.replace(tzinfo=UTC)).days,
                }
        except Exception:
            pass

    # Determine which items to return
    order_items = order.get("items", [])
    if return_items:
        items_to_return = [i for i in order_items if i["product_id"] in return_items]
    else:
        items_to_return = order_items

    if not items_to_return:
        return {"success": False, "error": "No valid items to return"}

    # Calculate refund
    refund_subtotal = sum(i.get("price", 0) * i.get("quantity", 1) for i in items_to_return)
    restocking_fee = 0.0
    if condition == "opened":
        restocking_fee = round(refund_subtotal * RESTOCKING_FEE_RATE, 2)
    refund_amount = round(refund_subtotal - restocking_fee, 2)

    return_id = "ret-" + uuid.uuid4().hex[:8]
    record = {
        "return_id": return_id,
        "order_id": order_id,
        "items": items_to_return,
        "reason": reason,
        "condition": condition,
        "refund_subtotal": round(refund_subtotal, 2),
        "restocking_fee": restocking_fee,
        "refund_amount": refund_amount,
        "status": "approved",
        "created_at": datetime.now(UTC).isoformat(),
    }
    _return_records.append(record)

    return {"success": True, "return": record}


def get_returns(customer_id=None):
    """Get all return records, optionally filtered."""
    if customer_id:
        return [r for r in _return_records if r.get("customer_id") == customer_id]
    return list(_return_records)
