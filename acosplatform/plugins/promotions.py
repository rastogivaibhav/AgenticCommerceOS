"""Promotions plugin – category-based and seasonal discounts."""

from datetime import datetime, UTC

DEFAULT_CATEGORY_DISCOUNTS = {
    "electronics": 0.10,
    "clothing": 0.15,
    "home": 0.05,
    "sports": 0.12,
    "beauty": 0.08,
}

SEASONAL_PROMOS = {
    "SUMMER_SALE": {
        "months": [6, 7, 8],
        "extra_discount": 0.05,
        "categories": ["clothing", "sports"],
    },
    "HOLIDAY_DEAL": {
        "months": [11, 12],
        "extra_discount": 0.10,
        "categories": ["electronics", "home"],
    },
    "SPRING_REFRESH": {
        "months": [3, 4, 5],
        "extra_discount": 0.07,
        "categories": ["beauty", "home"],
    },
}


def run(ctx):
    """Apply promotions to priced products.

    ctx keys:
        products: list of product dicts (must have 'price', 'category')
        tenant_config: optional dict with 'promo_rules' overrides
    """
    products = ctx.get("products", [])
    tenant_config = ctx.get("tenant_config") or {}
    category_discounts = tenant_config.get("promo_rules", DEFAULT_CATEGORY_DISCOUNTS)
    now = datetime.now(UTC)
    current_month = now.month

    active_seasonal = []
    for name, promo in SEASONAL_PROMOS.items():
        if current_month in promo["months"]:
            active_seasonal.append({"name": name, **promo})

    result = []
    total_savings = 0.0
    applied_promos = []

    for p in products:
        category = p.get("category", "")
        price = p.get("price", p.get("base_price", 0))

        # Category discount
        cat_discount_rate = category_discounts.get(category, 0)
        cat_discount = round(price * cat_discount_rate, 2)

        # Seasonal discount (additive)
        seasonal_discount = 0.0
        seasonal_names = []
        for promo in active_seasonal:
            if category in promo["categories"]:
                seasonal_discount += round(price * promo["extra_discount"], 2)
                seasonal_names.append(promo["name"])

        total_discount = round(cat_discount + seasonal_discount, 2)
        promo_price = round(price - total_discount, 2)

        promo_entry = {
            **p,
            "promo_price": promo_price,
            "category_discount": cat_discount,
            "seasonal_discount": seasonal_discount,
            "total_discount": total_discount,
            "applied_promos": [f"{category}_{int(cat_discount_rate*100)}pct"] + seasonal_names,
        }
        result.append(promo_entry)
        total_savings += total_discount
        applied_promos.extend(promo_entry["applied_promos"])

    return {
        "products": result,
        "total_savings": round(total_savings, 2),
        "active_seasonal_promos": [p["name"] for p in active_seasonal],
        "applied_promos": list(set(applied_promos)),
    }


def apply_to_single(product, tenant_config=None):
    """Apply promotions to a single product."""
    result = run({"products": [product], "tenant_config": tenant_config})
    return result["products"][0] if result["products"] else None
