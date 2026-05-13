"""Personalization engine – uses customer context to modify recommendations."""

# Mock customer profiles
_CUSTOMER_PROFILES = {
    "cust-1": {
        "preferences": {
            "categories": ["electronics", "home"],
            "tags": ["premium", "ergonomic", "smart"],
            "price_range": {"min": 100, "max": 1500},
        },
        "history": [
            {"product_id": "prod-001", "category": "electronics", "purchased_at": "2025-12-15"},
            {"product_id": "prod-009", "category": "home", "purchased_at": "2025-11-20"},
        ],
        "loyalty_points": 250,
    },
    "cust-2": {
        "preferences": {
            "categories": ["sports", "clothing"],
            "tags": ["fitness", "performance", "running"],
            "price_range": {"min": 20, "max": 200},
        },
        "history": [
            {"product_id": "prod-007", "category": "sports", "purchased_at": "2026-01-10"},
        ],
        "loyalty_points": 75,
    },
    "cust-3": {
        "preferences": {
            "categories": ["home", "beauty"],
            "tags": ["luxury", "comfort", "skincare"],
            "price_range": {"min": 30, "max": 800},
        },
        "history": [
            {"product_id": "prod-010", "category": "home", "purchased_at": "2025-10-05"},
            {"product_id": "prod-014", "category": "beauty", "purchased_at": "2025-12-01"},
            {"product_id": "prod-019", "category": "home", "purchased_at": "2026-01-25"},
        ],
        "loyalty_points": 600,
    },
    "cust-4": {
        "preferences": {
            "categories": ["electronics", "sports"],
            "tags": ["portable", "wireless", "waterproof"],
            "price_range": {"min": 25, "max": 500},
        },
        "history": [
            {"product_id": "prod-002", "category": "electronics", "purchased_at": "2025-09-15"},
            {"product_id": "prod-016", "category": "electronics", "purchased_at": "2025-11-01"},
            {"product_id": "prod-012", "category": "sports", "purchased_at": "2026-02-14"},
            {"product_id": "prod-018", "category": "sports", "purchased_at": "2026-03-01"},
        ],
        "loyalty_points": 1200,
    },
}

_DEFAULT_PROFILE = {
    "preferences": {"categories": [], "tags": [], "price_range": {"min": 0, "max": 10000}},
    "history": [],
    "loyalty_points": 0,
}


def get_customer_profile(customer_id):
    """Get customer profile with preferences and history."""
    return _CUSTOMER_PROFILES.get(customer_id, dict(_DEFAULT_PROFILE))


def personalize(ctx, result):
    """Apply personalization to journey results.

    Modifications:
    - Re-rank recommendations based on preference match score
    - Add personalized messaging
    - Highlight relevant deals
    """
    preferences = ctx.get("preferences", {})
    history = ctx.get("history", [])
    customer_id = ctx.get("customer_id", "anon")

    # Re-rank recommendations if present
    recs = result.get("recommendations", [])
    if recs and preferences.get("categories"):
        preferred_cats = set(preferences.get("categories", []))
        preferred_tags = set(preferences.get("tags", []))

        def preference_score(product):
            score = 0
            if product.get("category") in preferred_cats:
                score += 3
            for tag in product.get("tags", []):
                if tag in preferred_tags:
                    score += 1
            return score

        recs_scored = [(preference_score(r), r) for r in recs]
        recs_scored.sort(key=lambda x: -x[0])
        result["recommendations"] = [r for _, r in recs_scored]

    # Add personalized messaging
    msg_parts = []
    if history:
        last_cat = history[-1].get("category", "")
        if last_cat:
            msg_parts.append(f"Based on your recent {last_cat} purchases")
    if preferences.get("categories"):
        msg_parts.append(f"curated for your interest in {', '.join(preferences['categories'][:2])}")

    result["personalization"] = {
        "customer_id": customer_id,
        "is_personalized": bool(preferences.get("categories") or history),
        "message": " and ".join(msg_parts) + "." if msg_parts else "Discover our top picks for you!",
        "preference_categories": preferences.get("categories", []),
        "purchase_history_count": len(history),
    }

    return result
