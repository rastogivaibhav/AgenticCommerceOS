"""Unit tests for journey routing and context building."""

from acosplatform.journey.routing import route, get_all_journeys
from acosplatform.journey.context import build_context


class TestRouting:
    def test_discovery_route(self):
        assert route({"message": "recommend me something"}) == "discovery"

    def test_discovery_browse(self):
        assert route({"message": "show me what you have"}) == "discovery"

    def test_purchase_route(self):
        assert route({"message": "I want to buy a laptop"}) == "purchase"

    def test_purchase_price(self):
        assert route({"message": "how much does it cost"}) == "purchase"

    def test_post_purchase_route(self):
        assert route({"message": "where is my order"}) == "post_purchase"

    def test_post_purchase_tracking(self):
        assert route({"message": "track my delivery"}) == "post_purchase"

    def test_service_return(self):
        assert route({"message": "I want to return this"}) == "service"

    def test_service_refund(self):
        assert route({"message": "I need a refund"}) == "service"

    def test_engagement_feedback(self):
        assert route({"message": "I want to leave feedback"}) == "engagement"

    def test_engagement_referral(self):
        assert route({"message": "refer a friend"}) == "engagement"

    def test_empty_message_defaults(self):
        assert route({"message": ""}) == "discovery"

    def test_all_journeys(self):
        journeys = get_all_journeys()
        assert "discovery" in journeys
        assert "purchase" in journeys
        assert "post_purchase" in journeys
        assert "service" in journeys
        assert "engagement" in journeys


class TestContext:
    def test_basic_context(self):
        ctx = build_context({"message": "hello"})
        assert ctx["message"] == "hello"
        assert ctx["customer_id"] == "anon"
        assert ctx["tenant_id"] == "default"
        assert "tenant_config" in ctx

    def test_context_with_customer(self):
        ctx = build_context({"message": "hi", "customer_id": "cust-1"})
        assert ctx["customer_id"] == "cust-1"
        assert ctx["preferences"] is not None
        assert len(ctx["history"]) > 0

    def test_context_with_tenant(self):
        ctx = build_context({"message": "hi", "tenant_id": "eu-store"})
        assert ctx["tenant_id"] == "eu-store"
        assert ctx["tenant_config"]["currency"] == "EUR"

    def test_context_preserves_optional_fields(self):
        ctx = build_context({
            "message": "test",
            "order_id": "ord-123",
            "category": "electronics",
            "points_to_redeem": 50,
        })
        assert ctx["order_id"] == "ord-123"
        assert ctx["category"] == "electronics"
        assert ctx["points_to_redeem"] == 50
