"""Mock retail domain store for golden journey and local demos."""
from __future__ import annotations
from typing import Any

PRODUCTS = [
    {"id": "sku_dress_navy_01", "name": "Navy Satin Midi Dress", "category": "dress", "price": 89, "tags": ["wedding", "winter", "formal"], "variants": ["8", "10", "12", "14"]},
    {"id": "sku_shawl_silver_01", "name": "Silver Wrap Shawl", "category": "accessory", "price": 35, "tags": ["wedding", "winter", "layering"], "variants": ["one-size"]},
    {"id": "sku_heels_black_01", "name": "Black Block-Heel Court Shoes", "category": "shoes", "price": 59, "tags": ["wedding", "comfort", "formal"], "variants": ["5", "6", "7"]},
    {"id": "sku_coat_wool_01", "name": "Charcoal Wool Blend Coat", "category": "coat", "price": 120, "tags": ["winter", "formal"], "variants": ["S", "M", "L"]},
]
STOCK = {("sku_dress_navy_01", "Reading"): 4, ("sku_shawl_silver_01", "Reading"): 8, ("sku_heels_black_01", "Reading"): 3, ("sku_coat_wool_01", "Reading"): 0}
ORDERS = {"ORD-1001": {"id": "ORD-1001", "status": "out_for_delivery", "eta": "tomorrow", "items": ["Navy Satin Midi Dress"]}}

def search_products(query: str, *, budget: float | None = None, tags: list[str] | None = None) -> list[dict[str, Any]]:
    q = query.lower(); tags = tags or []; results = []
    for product in PRODUCTS:
        haystack = " ".join([product["name"], product["category"], *product["tags"]]).lower()
        if any(token in haystack for token in q.split()) or any(tag in product["tags"] for tag in tags):
            if budget is None or product["price"] <= budget:
                results.append(product)
    return results or PRODUCTS[:3]

def check_stock(product_id: str, location: str = "Reading") -> dict[str, Any]:
    qty = STOCK.get((product_id, location), 0)
    return {"product_id": product_id, "location": location, "quantity": qty, "available": qty > 0}

def get_order(order_id: str) -> dict[str, Any]:
    return ORDERS.get(order_id, {"id": order_id, "status": "not_found"})

def returns_eligibility(order_id: str) -> dict[str, Any]:
    order = get_order(order_id)
    return {"order_id": order_id, "eligible": order.get("status") not in {"not_found", "refunded"}, "policy": "30-day standard return window"}

def loyalty_balance(customer_id: str) -> dict[str, Any]:
    return {"customer_id": customer_id, "points": 1240, "tier": "silver", "voucher_value": 10}


def get_product(product_id: str) -> dict[str, Any]:
    return next((p for p in PRODUCTS if p["id"] == product_id), {"id": product_id, "status": "not_found"})

def calculate_price(product_ids: list[str] | None = None, *, budget: float | None = None) -> dict[str, Any]:
    product_ids = product_ids or []
    items = [get_product(pid) for pid in product_ids if get_product(pid).get("status") != "not_found"]
    subtotal = sum(float(item.get("price", 0)) for item in items)
    discount = 10.0 if subtotal >= 150 else 0.0
    total = max(subtotal - discount, 0.0)
    return {"currency": "GBP", "subtotal": subtotal, "discount": discount, "total": total, "within_budget": budget is None or total <= budget, "items": items}

def find_offers(product_ids: list[str] | None = None) -> dict[str, Any]:
    return {"offers": [{"id": "offer_wedding_bundle_10", "description": "£10 off occasionwear bundles over £150", "eligible_product_ids": product_ids or []}]}

def create_return(order_id: str, reason: str = "customer_request") -> dict[str, Any]:
    eligibility = returns_eligibility(order_id)
    if not eligibility.get("eligible"):
        return {"order_id": order_id, "status": "blocked", "reason": "not_eligible"}
    return {"return_id": f"RET-{order_id.replace('ORD-', '')}", "order_id": order_id, "status": "created", "reason": reason}
