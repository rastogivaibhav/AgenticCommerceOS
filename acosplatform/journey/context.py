"""Journey context builder – enriches raw payload with tenant, customer, and session data."""

from acosplatform.tenancy.manager import resolve_tenant, get_tenant_config
from acosplatform.personalization.engine import get_customer_profile


def build_context(payload):
    """Build enriched context from the incoming request payload.

    Payload keys:
        message: str (required)
        customer_id: str (default 'anon')
        tenant_id: str (default 'default')
        cart: list (optional)
        order_id: str (optional)
        category: str (optional)
        points_to_redeem: int (optional)
    """
    message = payload.get("message", "")
    customer_id = payload.get("customer_id", "anon")
    tenant_id = payload.get("tenant_id", "default")

    # Resolve tenant
    tenant = resolve_tenant(tenant_id)
    tenant_config = get_tenant_config(tenant)

    # Get customer profile
    profile = get_customer_profile(customer_id)

    ctx = {
        "message": message,
        "customer_id": customer_id,
        "tenant_id": tenant,
        "tenant_config": tenant_config,
        "preferences": profile.get("preferences", {}),
        "history": profile.get("history", []),
        "loyalty_points": profile.get("loyalty_points", 0),
        "cart": payload.get("cart", []),
        "order_id": payload.get("order_id"),
        "category": payload.get("category"),
        "points_to_redeem": payload.get("points_to_redeem", 0),
        "query": payload.get("query", message),
    }

    return ctx
