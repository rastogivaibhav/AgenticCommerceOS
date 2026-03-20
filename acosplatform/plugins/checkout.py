"""Checkout plugin – cart simulation with totals."""

import uuid
from datetime import datetime, UTC

TAX_RATE = 0.08  # 8% default tax


def run(ctx):
    """Build a cart summary and compute totals.

    ctx keys:
        products: list of product dicts (should have 'promo_price' or 'price')
        promo_savings: float (total promo discount already applied in price)
        loyalty: dict from loyalty plugin
        tenant_config: optional dict with 'tax_rate'
        customer_id: str
    """
    products = ctx.get("products", [])
    loyalty = ctx.get("loyalty", {})
    tenant_config = ctx.get("tenant_config") or {}
    tax_rate = tenant_config.get("tax_rate", TAX_RATE)
    customer_id = ctx.get("customer_id", "anon")

    cart_items = []
    subtotal = 0.0

    for p in products:
        item_price = p.get("promo_price", p.get("price", p.get("base_price", 0)))
        cart_items.append({
            "product_id": p.get("id", "unknown"),
            "name": p.get("name", "Unknown Product"),
            "unit_price": item_price,
            "quantity": 1,
            "line_total": item_price,
        })
        subtotal += item_price

    subtotal = round(subtotal, 2)

    # Loyalty discount
    loyalty_discount = loyalty.get("total_loyalty_discount", 0)
    after_loyalty = round(subtotal - loyalty_discount, 2)

    # Tax
    tax = round(after_loyalty * tax_rate, 2)
    total = round(after_loyalty + tax, 2)

    # Promo savings summary
    promo_savings = ctx.get("promo_savings", 0)

    cart_id = "cart-" + uuid.uuid4().hex[:8]

    return {
        "cart_id": cart_id,
        "customer_id": customer_id,
        "items": cart_items,
        "item_count": len(cart_items),
        "subtotal": subtotal,
        "promo_savings": round(promo_savings, 2),
        "loyalty_discount": loyalty_discount,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
        "currency": products[0].get("currency", "USD") if products else "USD",
        "loyalty_tier": loyalty.get("tier", "Bronze"),
        "points_earned": loyalty.get("points_earned", 0),
        "created_at": datetime.now(UTC).isoformat(),
    }
