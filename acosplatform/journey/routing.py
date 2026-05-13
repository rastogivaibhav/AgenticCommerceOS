"""Journey router – dynamically routes to journey type based on user message."""

JOURNEY_KEYWORDS = {
    "purchase": [
        "buy", "purchase", "add to cart", "checkout", "price", "pricing",
        "how much", "cost", "deal", "discount", "promo", "coupon",
    ],
    "post_purchase": [
        "order", "track", "tracking", "where is my", "delivery", "shipped",
        "status", "when will", "estimated",
    ],
    "service": [
        "return", "refund", "exchange", "complaint", "problem", "broken",
        "defective", "warranty", "support", "help with order",
    ],
    "engagement": [
        "feedback", "review", "rate", "refer", "referral", "share",
        "newsletter", "subscribe", "unsubscribe",
    ],
    "discovery": [
        "recommend", "suggest", "show me", "looking for", "browse",
        "what do you have", "new arrivals", "popular", "best",
        "find", "search", "explore", "discover",
    ],
}


def route(ctx):
    """Route to the appropriate journey based on message content.

    Returns one of: discovery, purchase, post_purchase, service, engagement
    """
    message = ctx.get("message", "").lower()

    if not message:
        return "discovery"

    # Priority order: service > post_purchase > purchase > engagement > discovery
    priority = ["service", "post_purchase", "purchase", "engagement", "discovery"]

    best_journey = "discovery"
    best_score = 0

    for journey in priority:
        keywords = JOURNEY_KEYWORDS.get(journey, [])
        score = sum(1 for kw in keywords if kw in message)
        if score > best_score:
            best_score = score
            best_journey = journey

    return best_journey


def get_all_journeys():
    """Return list of supported journey types."""
    return list(JOURNEY_KEYWORDS.keys())
