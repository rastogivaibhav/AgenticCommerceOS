"""Pricing plugin computes prices with tenant-specific currency multiplier."""

from integrations.connectors import ConnectorContract, execute_connector


CURRENCY_MULTIPLIERS = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "INR": 83.10,
    "CAD": 1.36,
}

_PRICING_CONNECTOR = ConnectorContract(
    name="pricing",
    required_request_fields=("tenant_id", "products"),
    required_response_fields=("products", "currency"),
)


def run(ctx):
    """Price a list of products using base price and tenant currency."""
    tenant_config = ctx.get("tenant_config") or {}
    connector_result = execute_connector(
        contract=_PRICING_CONNECTOR,
        payload={
            "tenant_id": ctx.get("tenant_id", "default"),
            "products": ctx.get("products", []),
            "currency": ctx.get("currency"),
            "tenant_config": tenant_config,
        },
        tenant_config=tenant_config,
        local_handler=_local_pricing_run,
    )
    return connector_result.as_dict()


def _local_pricing_run(ctx):
    products = ctx.get("products", [])
    currency = ctx.get("currency") or (ctx.get("tenant_config") or {}).get("currency", "USD")
    multiplier = CURRENCY_MULTIPLIERS.get(currency, 1.0)

    priced = []
    for product in products:
        base = product.get("base_price", 0)
        final = round(base * multiplier, 2)
        priced.append(
            {
                **product,
                "currency": currency,
                "price": final,
                "original_price": base,
            }
        )
    return {"products": priced, "currency": currency, "multiplier": multiplier}


def price_single(product, currency="USD"):
    """Price a single product."""
    result = run({"products": [product], "currency": currency, "tenant_id": "default"})
    return result["products"][0] if result["products"] else None
