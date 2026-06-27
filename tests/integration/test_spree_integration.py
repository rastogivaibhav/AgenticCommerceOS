from __future__ import annotations

import os

import pytest

from acosplatform.integrations.spree import SpreeClient


pytestmark = pytest.mark.integration


def _client() -> SpreeClient:
    base_url = os.environ.get("SPREE_BASE_URL")
    if not base_url:
        pytest.skip("SPREE_BASE_URL is not set")
    allow_http = os.environ.get("SPREE_ALLOW_HTTP", "").strip().lower() in {"1", "true", "yes", "on"}
    return SpreeClient(base_url=base_url, bearer_token=os.environ.get("SPREE_BEARER_TOKEN", ""), allow_http=allow_http)


def test_catalog_search_live():
    result = _client().catalog_search()
    assert isinstance(result, list)


def test_catalog_get_product_roundtrip():
    client = _client()
    products = client.catalog_search()
    if not products:
        pytest.skip("Live Spree catalog has no products")
    product = client.catalog_get_product(products[0]["id"])
    assert product["id"] == products[0]["id"]


def test_cart_create_add_and_get_roundtrip_live():
    client = _client()
    products = client.catalog_search()
    if not products:
        pytest.skip("Live Spree catalog has no products")
    detail = client.catalog_get_product(products[0]["id"], expand_variants=True)
    variants = detail.get("variants") or []
    variant = next((item for item in variants if item.get("id")), None)
    if not variant and detail.get("default_variant_id"):
        variant = {"id": detail["default_variant_id"]}
    if not variant:
        pytest.skip("Live Spree product has no purchasable variants")

    cart = client.cart_create()
    assert cart["cart_id"]
    assert cart["cart_token"]

    updated = client.cart_add_item(cart["cart_id"], variant["id"], 1, cart_token=cart["cart_token"])
    assert updated["item_count"] >= 1

    fetched = client.cart_get(cart["cart_id"], cart_token=cart["cart_token"])
    assert fetched["cart_id"] == cart["cart_id"]
    assert fetched["item_count"] >= 1
