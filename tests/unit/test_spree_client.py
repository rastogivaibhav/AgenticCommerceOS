from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import requests

from acosplatform.integrations.spree.client import SpreeAPIError, SpreeClient, SpreeConnectionError


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=None):
        self.status_code = status_code
        self._body = body or {}
        self.text = text if text is not None else str(self._body)
        self.content = self.text.encode("utf-8")

    def json(self):
        return self._body


class FakeSession:
    responses = []
    calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, **kwargs):
        self.__class__.calls.append({"method": method, "url": url, **kwargs})
        response = self.__class__.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


@pytest.fixture(autouse=True)
def fake_session(monkeypatch):
    FakeSession.responses = []
    FakeSession.calls = []
    monkeypatch.setattr(requests, "Session", FakeSession)


def client():
    return SpreeClient("https://spree.test", "secret-token")


def product(pid="p1", **attrs):
    base = {"name": "Navy Dress", "price": "12.50", "currency": "GBP", "in_stock": True, "description": "A dress", "slug": "navy-dress"}
    base.update(attrs)
    return {"id": pid, "type": "product", "attributes": base}


def order(oid="R100", **attrs):
    base = {"number": oid, "state": "complete", "total": "40.00", "currency": "GBP", "shipment_state": "ready", "completed_at": datetime.now(UTC).isoformat()}
    base.update(attrs)
    return {"id": oid, "type": "order", "attributes": base}


def test_catalog_search_with_query():
    FakeSession.responses = [FakeResponse(body={"data": [product()]})]
    result = client().catalog_search(query="dress")
    assert result[0]["name"] == "Navy Dress"
    assert FakeSession.calls[0]["params"]["filter[search]"] == "dress"


def test_catalog_search_with_budget():
    FakeSession.responses = [FakeResponse(body={"data": []})]
    client().catalog_search(budget=50)
    assert FakeSession.calls[0]["params"]["filter[price_lte]"] == 50


def test_catalog_search_in_stock_flag():
    FakeSession.responses = [FakeResponse(body={"data": []})]
    client().catalog_search(in_stock=True)
    assert FakeSession.calls[0]["params"]["filter[in_stock]"] == "true"


def test_catalog_search_category():
    FakeSession.responses = [FakeResponse(body={"data": []})]
    client().catalog_search(category="dresses")
    assert FakeSession.calls[0]["params"]["filter[in_category]"] == "dresses"


def test_catalog_search_no_filters():
    FakeSession.responses = [FakeResponse(body={"data": [product(tags=["formal"])]})]
    assert len(client().catalog_search()) == 1
    assert FakeSession.calls[0]["params"] is None


def test_catalog_get_product_found():
    FakeSession.responses = [FakeResponse(body={"data": product("p2")})]
    assert client().catalog_get_product("p2")["id"] == "p2"


def test_catalog_get_product_not_found():
    FakeSession.responses = [FakeResponse(404, body={"errors": [{"detail": "not found"}]})]
    assert client().catalog_get_product("missing") == {"id": "missing", "status": "not_found"}


def test_catalog_get_product_expand_variants():
    FakeSession.responses = [FakeResponse(body={"data": product("p2")})]
    client().catalog_get_product("p2", expand_variants=True)
    assert FakeSession.calls[0]["params"] == {"expand": "variants"}


def test_catalog_get_product_supports_flat_spree_v3_payload():
    FakeSession.responses = [FakeResponse(body={"id": "p-flat", "name": "Automatic Espresso Machine", "price": {"amount": "879.99", "currency": "USD"}, "default_variant_id": "v-flat"})]
    result = client().catalog_get_product("p-flat")
    assert result["id"] == "p-flat"
    assert result["name"] == "Automatic Espresso Machine"
    assert result["price"] == 879.99
    assert result["default_variant_id"] == "v-flat"


def test_inventory_check_stock():
    body = {
        "data": {"id": "p1", "type": "product", "attributes": {}, "relationships": {"variants": {"data": [{"id": "v1", "type": "variant"}]}}},
        "included": [{"id": "v1", "type": "variant", "attributes": {"purchasable_quantity": 3}}],
    }
    FakeSession.responses = [FakeResponse(body=body)]
    assert client().inventory_check_stock("p1")["quantity"] == 3


def test_orders_get_order_found():
    FakeSession.responses = [FakeResponse(body={"data": order()})]
    assert client().orders_get_order("R100")["order_id"] == "R100"


def test_orders_get_order_not_found():
    FakeSession.responses = [FakeResponse(404, body={})]
    assert client().orders_get_order("NOPE") == {"order_id": "NOPE", "status": "not_found"}


def test_returns_check_eligibility_within_window():
    FakeSession.responses = [FakeResponse(body={"data": order(completed_at=datetime.now(UTC).isoformat())})]
    assert client().returns_check_eligibility("R100")["eligible"] is True


def test_returns_check_eligibility_expired():
    old = (datetime.now(UTC) - timedelta(days=90)).isoformat()
    FakeSession.responses = [FakeResponse(body={"data": order(completed_at=old)})]
    result = client().returns_check_eligibility("R100")
    assert result["eligible"] is False
    assert result["reason"]


def test_returns_create_return_eligible():
    FakeSession.responses = [
        FakeResponse(body={"data": order(completed_at=datetime.now(UTC).isoformat())}),
        FakeResponse(body={"data": {"id": "RET1", "type": "return", "attributes": {"state": "created"}}}),
    ]
    assert client().returns_create_return("R100")["return_id"] == "RET1"


def test_returns_create_return_ineligible():
    FakeSession.responses = [FakeResponse(body={"data": order(state="cart")})]
    result = client().returns_create_return("R100")
    assert result["status"] == "blocked"
    assert len(FakeSession.calls) == 1


def test_loyalty_get_balance_aggregates():
    FakeSession.responses = [FakeResponse(body={"data": [{"attributes": {"amount_remaining": "10", "currency": "GBP"}}, {"attributes": {"amount_remaining": "5"}}]})]
    assert client().loyalty_get_balance("cust")["voucher_value"] == 15


def test_loyalty_tier_bronze_silver_gold():
    c = client()
    assert c._transform_store_credits([{"attributes": {"amount_remaining": "5"}}])["tier"] == "bronze"
    assert c._transform_store_credits([{"attributes": {"amount_remaining": "20"}}])["tier"] == "silver"
    assert c._transform_store_credits([{"attributes": {"amount_remaining": "70"}}])["tier"] == "gold"


def test_loyalty_empty_store_credits():
    assert client()._transform_store_credits([])["points"] == 0


def test_cart_add_remove_roundtrip():
    FakeSession.responses = [
        FakeResponse(body={"data": {"id": "cart1", "attributes": {"item_count": 1, "total": "12", "currency": "GBP"}}}),
        FakeResponse(body={"data": {"id": "cart1", "attributes": {"item_count": 0, "total": "0", "currency": "GBP"}}}),
    ]
    c = client()
    assert c.cart_add_item("cart1", "v1", 1)["item_count"] == 1
    assert c.cart_remove_item("cart1", "li1")["item_count"] == 0


def test_cart_get_and_add_item_support_flat_spree_v3_payload_and_token_header():
    FakeSession.responses = [
        FakeResponse(body={"id": "cart_flat", "token": "tok_flat", "number": "R100", "total_quantity": 1, "item_total": "12.00", "total": "12.00", "currency": "USD", "amount_due": "12.00", "items": [{"id": "line1"}]}),
        FakeResponse(body={"id": "cart_flat", "token": "tok_flat", "number": "R100", "total_quantity": 2, "item_total": "24.00", "total": "24.00", "currency": "USD", "amount_due": "24.00", "items": [{"id": "line1"}, {"id": "line2"}]}),
    ]
    c = client()
    cart = c.cart_get("cart_flat", cart_token="tok_flat")
    updated = c.cart_add_item("cart_flat", "variant1", 1, cart_token="tok_flat")
    assert cart["cart_id"] == "cart_flat"
    assert cart["cart_token"] == "tok_flat"
    assert updated["item_count"] == 2
    assert FakeSession.calls[0]["headers"]["X-Spree-Token"] == "tok_flat"
    assert FakeSession.calls[1]["headers"]["X-Spree-Token"] == "tok_flat"


def test_cart_apply_invalid_discount():
    FakeSession.responses = [FakeResponse(422, body={"errors": [{"detail": "invalid"}]})]
    assert client().cart_apply_discount("cart1", "NOPE")["code"] == "invalid_discount_code"


def test_cart_complete_rejected():
    FakeSession.responses = [FakeResponse(422, body={"errors": [{"detail": "payment required"}], "data": {"id": "cart1", "attributes": {"total": "12"}}})]
    assert client().cart_complete("cart1")["code"] == "cart_completion_failed"


def test_connection_error_raises_SpreeConnectionError():
    FakeSession.responses = [requests.ConnectionError("down")]
    with pytest.raises(SpreeConnectionError):
        client().catalog_search()


def test_timeout_raises_SpreeConnectionError():
    FakeSession.responses = [requests.Timeout("slow")]
    with pytest.raises(SpreeConnectionError):
        client().catalog_search()


def test_4xx_raises_SpreeAPIError():
    FakeSession.responses = [FakeResponse(400, body={"errors": [{"detail": "bad"}]})]
    with pytest.raises(SpreeAPIError):
        client().catalog_search()


def test_401_token_refresh_retry():
    c = SpreeClient("https://spree.test", "old", refresh_token="refresh")
    FakeSession.responses = [
        FakeResponse(401, body={"error": "token expired"}),
        FakeResponse(200, body={"access_token": "fresh"}),
        FakeResponse(200, body={"data": [product()]}),
    ]
    assert c.catalog_search()[0]["id"] == "p1"
    assert FakeSession.calls[-1]["headers"]["Authorization"] == "Bearer fresh"


def test_publishable_key_uses_spree_api_key_header():
    c = SpreeClient("https://spree.test", "pk_acos_demo_publishable_key")
    FakeSession.responses = [FakeResponse(body={"data": []})]
    c.catalog_search()
    headers = FakeSession.calls[0]["headers"]
    assert headers["X-Spree-API-Key"] == "pk_acos_demo_publishable_key"
    assert "Authorization" not in headers


def test_401_refresh_fails_raises_error():
    c = SpreeClient("https://spree.test", "old", refresh_token="refresh")
    FakeSession.responses = [FakeResponse(401, body={"error": "token expired"}), FakeResponse(422, body={})]
    with pytest.raises(SpreeConnectionError):
        c.catalog_search()


def test_https_enforcement_blocks_http():
    with pytest.raises(ValueError):
        SpreeClient("http://spree.test", "token")


def test_https_enforcement_allows_http_when_flag_set():
    assert SpreeClient("http://spree.test", "token", allow_http=True).base_url == "http://spree.test"


def test_bearer_token_not_in_repr():
    rendered = repr(SpreeClient("https://spree.test", "super-secret"))
    assert "super-secret" not in rendered
    assert "****" in rendered
