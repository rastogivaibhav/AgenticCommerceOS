"""Multi-tenancy manager – tenant configs with currency, promos, and features."""

from acosplatform.db.repository import get_tenant, get_all_tenants, save_tenant

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
        "connectors": {
            "catalog": {"mode": "local"},
            "pricing": {"mode": "local"},
            "promotions": {"mode": "local"},
            "orders": {"mode": "local"},
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
        "connectors": {
            "catalog": {"mode": "local", "timeout_seconds": 1.0, "retries": 1},
            "pricing": {"mode": "local"},
            "promotions": {"mode": "local"},
            "orders": {"mode": "local"},
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
        "connectors": {
            "catalog": {"mode": "local"},
            "pricing": {"mode": "local", "timeout_seconds": 1.2},
            "promotions": {"mode": "local"},
            "orders": {"mode": "local"},
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
        "connectors": {
            "catalog": {"mode": "local"},
            "pricing": {"mode": "local"},
            "promotions": {"mode": "local", "retries": 3},
            "orders": {"mode": "local"},
        },
    },
}

_seeded = False


def _seed_tenants():
    """Seed DB with hardcoded tenants if the tenants table is empty."""
    global _seeded
    if _seeded:
        return
    _seeded = True
    try:
        existing = get_all_tenants()
        if not existing:
            for tid, cfg in TENANT_CONFIGS.items():
                save_tenant({"id": tid, **cfg})
    except Exception:
        pass


def resolve_tenant(tenant_id):
    """Resolve tenant ID to a valid tenant. Falls back to 'default'."""
    _seed_tenants()
    try:
        row = get_tenant(tenant_id)
        if row:
            return tenant_id
    except Exception:
        pass
    if tenant_id in TENANT_CONFIGS:
        return tenant_id
    return "default"


def get_tenant_config(tenant_id):
    """Get full configuration for a tenant."""
    _seed_tenants()
    try:
        row = get_tenant(tenant_id)
        if row:
            return {
                "name": row["name"],
                "currency": row["currency"],
                "tax_rate": row["tax_rate"],
                "promo_rules": row["promo_rules"],
                "features": row["features"],
                "connectors": row.get("connector_routes", row.get("connectors", {})) or {},
            }
    except Exception:
        pass
    tenant = tenant_id if tenant_id in TENANT_CONFIGS else "default"
    return dict(TENANT_CONFIGS[tenant])


def is_feature_enabled(tenant_id, feature):
    """Check if a feature is enabled for a tenant."""
    config = get_tenant_config(tenant_id)
    return config.get("features", {}).get(feature, False)


def list_tenants():
    """List all configured tenants."""
    _seed_tenants()
    try:
        rows = get_all_tenants()
        if rows:
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "currency": r["currency"],
                    "tax_rate": r["tax_rate"],
                    "features": r["features"],
                    "promo_rules": r["promo_rules"],
                    "connectors": r.get("connector_routes", r.get("connectors", {})) or {},
                }
                for r in rows
            ]
    except Exception:
        pass
    return [
        {
            "id": tid,
            "name": cfg["name"],
            "currency": cfg["currency"],
            "tax_rate": cfg["tax_rate"],
            "features": cfg["features"],
            "promo_rules": cfg["promo_rules"],
            "connectors": cfg.get("connectors", {}),
        }
        for tid, cfg in TENANT_CONFIGS.items()
    ]


def add_tenant(tenant_id, config_dict):
    """Add a new tenant. Raises ValueError if tenant already exists."""
    required_keys = {"name", "currency", "tax_rate", "promo_rules", "features"}
    missing = required_keys - set(config_dict.keys())
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")

    _seed_tenants()
    # Check DB first, then in-memory
    try:
        existing = get_tenant(tenant_id)
        if existing:
            raise ValueError(f"Tenant '{tenant_id}' already exists")
    except ValueError:
        raise
    except Exception:
        pass

    if tenant_id in TENANT_CONFIGS:
        raise ValueError(f"Tenant '{tenant_id}' already exists")

    record = {"id": tenant_id, **config_dict}
    record.setdefault("connectors", {})
    save_tenant(record)
    TENANT_CONFIGS[tenant_id] = {k: config_dict[k] for k in required_keys}
    TENANT_CONFIGS[tenant_id]["connectors"] = config_dict.get("connectors", {})
    return record


def update_tenant(tenant_id, partial_config):
    """Merge partial config into existing tenant and persist."""
    existing_config = get_tenant_config(tenant_id)
    merged = {**existing_config, **partial_config}
    record = {"id": tenant_id, **merged}
    record.setdefault("connectors", merged.get("connectors", {}))
    save_tenant(record)
    if tenant_id in TENANT_CONFIGS:
        TENANT_CONFIGS[tenant_id].update(partial_config)
    return record
