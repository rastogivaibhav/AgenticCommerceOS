"""Promotions plugin with category and seasonal discounts."""

from datetime import UTC, datetime

from integrations.connectors import ConnectorContract, execute_connector


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

_PROMOTIONS_CONNECTOR = ConnectorContract(
    name="promotions",
    required_request_fields=("tenant_id", "products"),
    required_response_fields=("products", "total_savings"),
)


def run(ctx):
    """Apply promotions to priced products."""
    tenant_config = ctx.get("tenant_config") or {}
    connector_result = execute_connector(
        contract=_PROMOTIONS_CONNECTOR,
        payload={
            "tenant_id": ctx.get("tenant_id", "default"),
            "products": ctx.get("products", []),
            "tenant_config": tenant_config,
        },
        tenant_config=tenant_config,
        local_handler=_local_promotions_run,
    )
    return connector_result.as_dict()


def _local_promotions_run(ctx):
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

    for product in products:
        category = product.get("category", "")
        price = product.get("price", product.get("base_price", 0))

        cat_discount_rate = category_discounts.get(category, 0)
        cat_discount = round(price * cat_discount_rate, 2)

        seasonal_discount = 0.0
        seasonal_names = []
        for promo in active_seasonal:
            if category in promo["categories"]:
                seasonal_discount += round(price * promo["extra_discount"], 2)
                seasonal_names.append(promo["name"])

        total_discount = round(cat_discount + seasonal_discount, 2)
        promo_price = round(price - total_discount, 2)

        promo_entry = {
            **product,
            "promo_price": promo_price,
            "category_discount": cat_discount,
            "seasonal_discount": seasonal_discount,
            "total_discount": total_discount,
            "applied_promos": [f"{category}_{int(cat_discount_rate * 100)}pct"] + seasonal_names,
        }
        result.append(promo_entry)
        total_savings += total_discount
        applied_promos.extend(promo_entry["applied_promos"])

    return {
        "products": result,
        "total_savings": round(total_savings, 2),
        "active_seasonal_promos": [promo["name"] for promo in active_seasonal],
        "applied_promos": list(set(applied_promos)),
    }


def apply_to_single(product, tenant_config=None):
    """Apply promotions to a single product."""
    result = run(
        {
            "products": [product],
            "tenant_config": tenant_config or {},
            "tenant_id": "default",
        }
    )
    return result["products"][0] if result["products"] else None
