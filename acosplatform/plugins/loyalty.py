"""Loyalty plugin – points system with tiers and discount conversion."""

from acosplatform.db.repository import get_loyalty_points, save_loyalty_points

TIERS = [
    {"name": "Bronze", "min_points": 0, "discount_rate": 0.00},
    {"name": "Silver", "min_points": 100, "discount_rate": 0.03},
    {"name": "Gold", "min_points": 500, "discount_rate": 0.05},
    {"name": "Platinum", "min_points": 1000, "discount_rate": 0.08},
]

POINTS_PER_DOLLAR = 1
POINTS_TO_DOLLAR = 0.01  # 100 points = $1


_customer_points = {
    "cust-1": 250,
    "cust-2": 75,
    "cust-3": 600,
    "cust-4": 1200,
}


def run(ctx):
    """Compute loyalty status and discount for a customer.

    ctx keys:
        customer_id: str
        subtotal: float (cart subtotal for discount calc)
        points_to_redeem: int (optional, how many points to burn)
    """
    customer_id = ctx.get("customer_id", "anon")
    subtotal = ctx.get("subtotal", 0)
    points_to_redeem = ctx.get("points_to_redeem", 0)

    db_points = get_loyalty_points(customer_id)
    if db_points is not None:
        current_points = db_points
    else:
        current_points = _customer_points.get(customer_id, 0)

    # Determine tier
    tier = TIERS[0]
    for t in TIERS:
        if current_points >= t["min_points"]:
            tier = t

    # Tier-based percentage discount
    tier_discount = round(subtotal * tier["discount_rate"], 2)

    # Points redemption discount
    redeemable = min(points_to_redeem, current_points)
    points_discount = round(redeemable * POINTS_TO_DOLLAR, 2)
    points_discount = min(points_discount, subtotal - tier_discount)  # can't go below 0

    total_discount = round(tier_discount + points_discount, 2)

    # Points earned from this purchase (on subtotal before discounts)
    points_earned = int(subtotal * POINTS_PER_DOLLAR)

    new_points_balance = current_points - redeemable + points_earned
    save_loyalty_points(customer_id, new_points_balance)
    _customer_points[customer_id] = new_points_balance

    return {
        "customer_id": customer_id,
        "current_points": current_points,
        "tier": tier["name"],
        "tier_discount_rate": tier["discount_rate"],
        "tier_discount": tier_discount,
        "points_redeemed": redeemable,
        "points_discount": points_discount,
        "total_loyalty_discount": total_discount,
        "points_earned": points_earned,
        "new_points_balance": new_points_balance,
    }


def get_status(customer_id):
    """Get loyalty status for a customer."""
    return run({"customer_id": customer_id})


def add_points(customer_id, points):
    """Add points to a customer's balance."""
    _customer_points[customer_id] = _customer_points.get(customer_id, 0) + points
    save_loyalty_points(customer_id, _customer_points[customer_id])
    return _customer_points[customer_id]
