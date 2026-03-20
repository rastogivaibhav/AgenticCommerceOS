"""Pricing plugin – computes prices with tenant-specific currency multiplier."""


CURRENCY_MULTIPLIERS = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "INR": 83.10,
    "CAD": 1.36,
}


def run(ctx):
    """Price a list of products using base price and tenant currency.

    ctx keys:
        products: list of product dicts (must have 'base_price')
        currency: str, default 'USD'
        tenant_config: optional dict with 'currency' key
    """
    products = ctx.get("products", [])
    currency = ctx.get("currency") or (ctx.get("tenant_config") or {}).get("currency", "USD")
    multiplier = CURRENCY_MULTIPLIERS.get(currency, 1.0)

    priced = []
    for p in products:
        base = p.get("base_price", 0)
        final = round(base * multiplier, 2)
        priced.append({
            **p,
            "currency": currency,
            "price": final,
            "original_price": base,
        })

    return {"products": priced, "currency": currency, "multiplier": multiplier}


def price_single(product, currency="USD"):
    """Price a single product."""
    result = run({"products": [product], "currency": currency})
    return result["products"][0] if result["products"] else None
