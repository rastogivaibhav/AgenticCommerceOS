"""Unit tests for all ACOS plugins."""

from acosplatform.plugins import catalog, pricing, promotions, loyalty, checkout, orders, returns


# ── Catalog ───────────────────────────────────────────────────────────────────

class TestCatalog:
    def test_full_catalog(self):
        result = catalog.run({})
        assert result["total"] == 20
        assert len(result["products"]) == 20

    def test_filter_by_category(self):
        result = catalog.run({"category": "electronics"})
        assert result["total"] > 0
        assert all(p["category"] == "electronics" for p in result["products"])

    def test_search_by_query(self):
        result = catalog.search("laptop")
        assert result["total"] >= 1
        assert any("laptop" in p["name"].lower() or "laptop" in p["description"].lower() for p in result["products"])

    def test_get_product(self):
        product = catalog.get_product("prod-001")
        assert product is not None
        assert product["id"] == "prod-001"
        assert product["name"] == "UltraBook Pro 15"

    def test_get_product_not_found(self):
        product = catalog.get_product("nonexistent")
        assert product is None

    def test_recommend(self):
        ctx = {
            "preferences": {"categories": ["electronics"], "tags": ["premium"]},
            "history": [],
        }
        result = catalog.recommend(ctx)
        assert len(result["recommendations"]) <= 5
        assert len(result["recommendations"]) > 0

    def test_recommend_excludes_purchased(self):
        ctx = {
            "preferences": {"categories": ["electronics"]},
            "history": [{"product_id": "prod-001"}],
        }
        result = catalog.recommend(ctx)
        ids = [r["id"] for r in result["recommendations"]]
        assert "prod-001" not in ids


# ── Pricing ───────────────────────────────────────────────────────────────────

class TestPricing:
    def test_usd_pricing(self):
        result = pricing.run({
            "products": [{"base_price": 100}],
            "currency": "USD",
        })
        assert result["products"][0]["price"] == 100.0
        assert result["currency"] == "USD"

    def test_eur_pricing(self):
        result = pricing.run({
            "products": [{"base_price": 100}],
            "currency": "EUR",
        })
        assert result["products"][0]["price"] == 92.0

    def test_tenant_currency(self):
        result = pricing.run({
            "products": [{"base_price": 100}],
            "tenant_config": {"currency": "GBP"},
        })
        assert result["currency"] == "GBP"
        assert result["products"][0]["price"] == 79.0


# ── Promotions ────────────────────────────────────────────────────────────────

class TestPromotions:
    def test_category_discount(self):
        result = promotions.run({
            "products": [{"price": 100, "category": "electronics"}],
        })
        assert result["products"][0]["category_discount"] == 10.0
        assert result["products"][0]["promo_price"] <= 100.0

    def test_clothing_discount(self):
        result = promotions.run({
            "products": [{"price": 100, "category": "clothing"}],
        })
        assert result["products"][0]["category_discount"] == 15.0

    def test_total_savings(self):
        result = promotions.run({
            "products": [
                {"price": 100, "category": "electronics"},
                {"price": 50, "category": "clothing"},
            ],
        })
        assert result["total_savings"] > 0


# ── Loyalty ───────────────────────────────────────────────────────────────────

class TestLoyalty:
    def test_bronze_tier(self):
        result = loyalty.run({"customer_id": "cust-2", "subtotal": 100})
        assert result["tier"] == "Bronze"
        assert result["tier_discount"] == 0

    def test_silver_tier(self):
        result = loyalty.run({"customer_id": "cust-1", "subtotal": 100})
        assert result["tier"] == "Silver"
        assert result["tier_discount"] == 3.0

    def test_gold_tier(self):
        result = loyalty.run({"customer_id": "cust-3", "subtotal": 100})
        assert result["tier"] == "Gold"
        assert result["tier_discount"] == 5.0

    def test_points_earned(self):
        result = loyalty.run({"customer_id": "cust-1", "subtotal": 100})
        assert result["points_earned"] == 100

    def test_points_redemption(self):
        result = loyalty.run({"customer_id": "cust-1", "subtotal": 100, "points_to_redeem": 100})
        assert result["points_redeemed"] == 100
        assert result["points_discount"] == 1.0


# ── Checkout ──────────────────────────────────────────────────────────────────

class TestCheckout:
    def test_basic_checkout(self):
        result = checkout.run({
            "products": [
                {"id": "prod-001", "name": "Test Product", "promo_price": 100},
            ],
            "loyalty": {},
            "customer_id": "cust-1",
        })
        assert result["subtotal"] == 100
        assert result["tax"] > 0
        assert result["total"] > 100
        assert result["item_count"] == 1

    def test_checkout_with_loyalty(self):
        result = checkout.run({
            "products": [{"id": "p1", "name": "P1", "promo_price": 100}],
            "loyalty": {"total_loyalty_discount": 5},
            "customer_id": "cust-1",
        })
        assert result["loyalty_discount"] == 5
        assert result["total"] < 108  # 100 - 5 + tax

    def test_multi_item_checkout(self):
        result = checkout.run({
            "products": [
                {"id": "p1", "name": "P1", "promo_price": 50},
                {"id": "p2", "name": "P2", "promo_price": 75},
            ],
            "loyalty": {},
            "customer_id": "cust-1",
        })
        assert result["subtotal"] == 125
        assert result["item_count"] == 2


# ── Orders ────────────────────────────────────────────────────────────────────

class TestOrders:
    def test_get_customer_orders(self):
        result = orders.run({"customer_id": "cust-1"})
        assert result["total"] == 2
        assert len(result["orders"]) == 2

    def test_get_no_orders(self):
        result = orders.run({"customer_id": "nonexistent"})
        assert result["total"] == 0

    def test_track_order(self):
        result = orders.track("ord-10001")
        assert result["found"] is True
        assert result["tracking"]["status"] == "delivered"

    def test_track_nonexistent_order(self):
        result = orders.track("nonexistent")
        assert result["found"] is False


# ── Returns ───────────────────────────────────────────────────────────────────

class TestReturns:
    def test_valid_return(self):
        result = returns.run({"order_id": "ord-10002", "condition": "opened"})
        assert result["success"] is True
        assert result["return"]["refund_amount"] > 0
        assert result["return"]["restocking_fee"] > 0

    def test_return_no_order_id(self):
        result = returns.run({})
        assert result["success"] is False
        assert "order_id is required" in result["error"]

    def test_return_nonexistent_order(self):
        result = returns.run({"order_id": "nonexistent"})
        assert result["success"] is False

    def test_unopened_return_no_fee(self):
        result = returns.run({"order_id": "ord-10002", "condition": "unopened"})
        assert result["success"] is True
        assert result["return"]["restocking_fee"] == 0
