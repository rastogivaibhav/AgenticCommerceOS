"""Multi-tenancy manager – tenant configs with currency, promos, and features."""

TENANT_CONFIGS = {
    "default": {
        "name": "Default Store",
        "currency": "USD",
        "tax_rate": 0.08,
        "promo_rules": {
            "electronics": 0.10,
            "clothing": 0.15,
            "home": 0.05,
            "sports": 0.12,
            "beauty": 0.08,
        },
        "features": {
            "loyalty": True,
            "referrals": True,
            "adk_agent": True,
            "returns": True,
        },
    },
    "eu-store": {
        "name": "European Store",
        "currency": "EUR",
        "tax_rate": 0.20,
        "promo_rules": {
            "electronics": 0.08,
            "clothing": 0.20,
            "home": 0.10,
            "sports": 0.15,
            "beauty": 0.12,
        },
        "features": {
            "loyalty": True,
            "referrals": True,
            "adk_agent": True,
            "returns": True,
        },
    },
    "jp-store": {
        "name": "Japan Store",
        "currency": "JPY",
        "tax_rate": 0.10,
        "promo_rules": {
            "electronics": 0.05,
            "clothing": 0.10,
            "home": 0.08,
            "sports": 0.10,
            "beauty": 0.15,
        },
        "features": {
            "loyalty": True,
            "referrals": False,
            "adk_agent": True,
            "returns": True,
        },
    },
    "in-store": {
        "name": "India Store",
        "currency": "INR",
        "tax_rate": 0.18,
        "promo_rules": {
            "electronics": 0.12,
            "clothing": 0.25,
            "home": 0.08,
            "sports": 0.15,
            "beauty": 0.10,
        },
        "features": {
            "loyalty": True,
            "referrals": True,
            "adk_agent": False,
            "returns": True,
        },
    },
}


def resolve_tenant(tenant_id):
    """Resolve tenant ID to a valid tenant. Falls back to 'default'."""
    if tenant_id in TENANT_CONFIGS:
        return tenant_id
    return "default"


def get_tenant_config(tenant_id):
    """Get full configuration for a tenant."""
    tenant = resolve_tenant(tenant_id)
    return dict(TENANT_CONFIGS[tenant])


def is_feature_enabled(tenant_id, feature):
    """Check if a feature is enabled for a tenant."""
    config = get_tenant_config(tenant_id)
    return config.get("features", {}).get(feature, False)


def list_tenants():
    """List all configured tenants."""
    return [
        {"id": tid, "name": cfg["name"], "currency": cfg["currency"]}
        for tid, cfg in TENANT_CONFIGS.items()
    ]
