"""Orders plugin – mock order history with status tracking."""

from datetime import datetime, timedelta, UTC

_MOCK_ORDERS = {
    "cust-1": [
        {
            "order_id": "ord-10001",
            "customer_id": "cust-1",
            "items": [
                {"product_id": "prod-001", "name": "UltraBook Pro 15", "quantity": 1, "price": 1169.99},
            ],
            "total": 1263.59,
            "status": "delivered",
            "placed_at": (datetime.now(UTC) - timedelta(days=10)).isoformat(),
            "delivered_at": (datetime.now(UTC) - timedelta(days=3)).isoformat(),
        },
        {
            "order_id": "ord-10002",
            "customer_id": "cust-1",
            "items": [
                {"product_id": "prod-005", "name": "Classic Denim Jacket", "quantity": 1, "price": 76.49},
                {"product_id": "prod-013", "name": "Organic Cotton T-Shirt", "quantity": 2, "price": 33.99},
            ],
            "total": 155.63,
            "status": "shipped",
            "placed_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
            "shipped_at": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    ],
    "cust-2": [
        {
            "order_id": "ord-10003",
            "customer_id": "cust-2",
            "items": [
                {"product_id": "prod-007", "name": "Performance Running Shoes", "quantity": 1, "price": 140.79},
            ],
            "total": 152.05,
            "status": "placed",
            "placed_at": (datetime.now(UTC) - timedelta(hours=6)).isoformat(),
        },
    ],
    "cust-3": [
        {
            "order_id": "ord-10004",
            "customer_id": "cust-3",
            "items": [
                {"product_id": "prod-010", "name": "Orthopedic Memory Foam Mattress", "quantity": 1, "price": 712.49},
                {"product_id": "prod-009", "name": "Ergonomic Office Chair", "quantity": 1, "price": 569.99},
            ],
            "total": 1384.88,
            "status": "delivered",
            "placed_at": (datetime.now(UTC) - timedelta(days=20)).isoformat(),
            "delivered_at": (datetime.now(UTC) - timedelta(days=14)).isoformat(),
        },
    ],
}


def run(ctx):
    """Get order history for a customer.

    ctx keys:
        customer_id: str
        order_id: str (optional, fetch single order)
    """
    customer_id = ctx.get("customer_id", "anon")
    order_id = ctx.get("order_id")

    orders = _MOCK_ORDERS.get(customer_id, [])

    if order_id:
        for o in orders:
            if o["order_id"] == order_id:
                return {"order": o, "found": True}
        return {"order": None, "found": False, "message": f"Order {order_id} not found"}

    return {"orders": orders, "total": len(orders), "customer_id": customer_id}


def get_order(order_id):
    """Find an order across all customers."""
    for customer_id, orders in _MOCK_ORDERS.items():
        for o in orders:
            if o["order_id"] == order_id:
                return o
    return None


def track(order_id):
    """Get tracking status for an order."""
    order = get_order(order_id)
    if not order:
        return {"found": False, "message": f"Order {order_id} not found"}

    status = order["status"]
    tracking = {
        "order_id": order_id,
        "status": status,
        "placed_at": order.get("placed_at"),
    }

    if status in ("shipped", "delivered"):
        tracking["shipped_at"] = order.get("shipped_at")
    if status == "delivered":
        tracking["delivered_at"] = order.get("delivered_at")

    status_steps = ["placed", "shipped", "delivered"]
    current_step = status_steps.index(status) if status in status_steps else 0
    tracking["progress"] = f"{current_step + 1}/{len(status_steps)}"

    return {"tracking": tracking, "found": True}
