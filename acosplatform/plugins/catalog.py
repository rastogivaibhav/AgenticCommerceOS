PRODUCTS = [
    {"id": "prod-001", "name": "UltraBook Pro 15", "category": "electronics", "base_price": 1299.99, "description": "15-inch laptop with M3 chip, 16GB RAM, 512GB SSD", "tags": ["laptop", "portable", "premium"]},
    {"id": "prod-002", "name": "Wireless Noise-Cancelling Headphones", "category": "electronics", "base_price": 349.99, "description": "Over-ear headphones with 30-hour battery and ANC", "tags": ["audio", "wireless", "noise-cancelling"]},
    {"id": "prod-003", "name": "Smart Watch Series 9", "category": "electronics", "base_price": 449.99, "description": "Health tracking, GPS, always-on display", "tags": ["wearable", "fitness", "smart"]},
    {"id": "prod-004", "name": "4K OLED Monitor 27\"", "category": "electronics", "base_price": 899.99, "description": "27-inch 4K OLED with HDR1000 and USB-C hub", "tags": ["display", "4k", "professional"]},
    {"id": "prod-005", "name": "Classic Denim Jacket", "category": "clothing", "base_price": 89.99, "description": "Timeless denim jacket with modern slim fit", "tags": ["outerwear", "casual", "denim"]},
    {"id": "prod-006", "name": "Merino Wool Sweater", "category": "clothing", "base_price": 129.99, "description": "Lightweight merino wool crew neck sweater", "tags": ["knitwear", "premium", "warm"]},
    {"id": "prod-007", "name": "Performance Running Shoes", "category": "sports", "base_price": 159.99, "description": "Carbon-plate running shoes for marathon training", "tags": ["running", "performance", "lightweight"]},
    {"id": "prod-008", "name": "Yoga Mat Premium", "category": "sports", "base_price": 79.99, "description": "6mm thick non-slip yoga mat with alignment lines", "tags": ["yoga", "fitness", "non-slip"]},
    {"id": "prod-009", "name": "Ergonomic Office Chair", "category": "home", "base_price": 599.99, "description": "Mesh back office chair with lumbar support and headrest", "tags": ["office", "ergonomic", "comfort"]},
    {"id": "prod-010", "name": "Orthopedic Memory Foam Mattress", "category": "home", "base_price": 749.99, "description": "Queen-size memory foam mattress with cooling gel layer", "tags": ["sleep", "memory-foam", "cooling"]},
    {"id": "prod-011", "name": "Smart Home Hub", "category": "electronics", "base_price": 129.99, "description": "Voice-controlled smart home hub with Matter support", "tags": ["smart-home", "voice", "iot"]},
    {"id": "prod-012", "name": "Stainless Steel Water Bottle", "category": "sports", "base_price": 34.99, "description": "Insulated 32oz bottle keeps drinks cold 24 hours", "tags": ["hydration", "insulated", "eco"]},
    {"id": "prod-013", "name": "Organic Cotton T-Shirt", "category": "clothing", "base_price": 39.99, "description": "Soft organic cotton crew neck t-shirt", "tags": ["basics", "organic", "sustainable"]},
    {"id": "prod-014", "name": "Vitamin C Serum", "category": "beauty", "base_price": 49.99, "description": "20% vitamin C serum with hyaluronic acid", "tags": ["skincare", "anti-aging", "brightening"]},
    {"id": "prod-015", "name": "Retinol Night Cream", "category": "beauty", "base_price": 64.99, "description": "0.5% retinol night cream for skin renewal", "tags": ["skincare", "anti-aging", "night"]},
    {"id": "prod-016", "name": "Bluetooth Portable Speaker", "category": "electronics", "base_price": 199.99, "description": "Waterproof portable speaker with 360-degree sound", "tags": ["audio", "portable", "waterproof"]},
    {"id": "prod-017", "name": "Cast Iron Skillet Set", "category": "home", "base_price": 89.99, "description": "Pre-seasoned 3-piece cast iron skillet set", "tags": ["cookware", "cast-iron", "durable"]},
    {"id": "prod-018", "name": "Resistance Band Set", "category": "sports", "base_price": 29.99, "description": "5-piece resistance band set with door anchor", "tags": ["fitness", "strength", "portable"]},
    {"id": "prod-019", "name": "Luxury Scented Candle", "category": "home", "base_price": 44.99, "description": "Soy wax candle with sandalwood and vanilla notes", "tags": ["decor", "aromatherapy", "luxury"]},
    {"id": "prod-020", "name": "SPF 50 Sunscreen", "category": "beauty", "base_price": 24.99, "description": "Lightweight mineral sunscreen SPF 50, reef-safe", "tags": ["skincare", "sun-protection", "mineral"]},
]

CATEGORIES = list(set(p["category"] for p in PRODUCTS))


def run(ctx):
    """Return product catalog, optionally filtered by category or search query."""
    category = ctx.get("category")
    query = ctx.get("query", "").lower()
    tags = ctx.get("tags", [])

    results = PRODUCTS

    if category:
        results = [p for p in results if p["category"] == category]

    if query:
        results = [
            p for p in results
            if query in p["name"].lower()
            or query in p["description"].lower()
            or any(query in t for t in p["tags"])
        ]

    if tags:
        results = [
            p for p in results
            if any(t in p["tags"] for t in tags)
        ]

    return {"products": results, "total": len(results), "categories": CATEGORIES}


def get_product(product_id):
    """Get a single product by ID."""
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def search(query):
    """Search products by name, description, or tags."""
    return run({"query": query})


def get_by_category(category):
    """Get products in a category."""
    return run({"category": category})


def recommend(ctx):
    """Recommend products based on customer preferences and history."""
    preferences = ctx.get("preferences", {})
    history = ctx.get("history", [])

    preferred_categories = preferences.get("categories", [])
    preferred_tags = preferences.get("tags", [])

    # Score products based on preference match
    scored = []
    purchased_ids = {item.get("product_id") for item in history}

    for p in PRODUCTS:
        if p["id"] in purchased_ids:
            continue
        score = 0
        if p["category"] in preferred_categories:
            score += 3
        for tag in p["tags"]:
            if tag in preferred_tags:
                score += 1
        scored.append((score, p))

    # Sort by score descending, take top 5
    scored.sort(key=lambda x: (-x[0], x[1]["base_price"]))
    top = [item[1] for item in scored[:5]]

    if not top:
        top = PRODUCTS[:5]

    return {"recommendations": top, "total": len(top)}
