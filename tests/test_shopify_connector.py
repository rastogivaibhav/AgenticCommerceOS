"""Tests for Shopify connector probing helpers."""

from __future__ import annotations

import requests

from integrations.shopify.client import load_shopify_config, probe_shopify_admin


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self._body = body or {}
        self.content = b"{}"

    def json(self):
        return self._body


def test_load_shopify_config_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ADMIN_ACCESS_TOKEN", raising=False)
    assert load_shopify_config() is None


def test_probe_shopify_admin_returns_skip_without_config(monkeypatch):
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ADMIN_ACCESS_TOKEN", raising=False)
    result = probe_shopify_admin({})
    assert result["status"] == "skipped"
    assert result["connector_source"] == "local_fallback"


def test_probe_shopify_admin_shop_probe_success(monkeypatch):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo-store.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "test-token")

    def fake_get(*args, **kwargs):
        return _FakeResponse(
            200,
            {
                "shop": {
                    "name": "Demo Store",
                    "myshopify_domain": "demo-store.myshopify.com",
                    "plan_name": "basic",
                }
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)
    result = probe_shopify_admin({})
    assert result["status"] == "ok"
    assert result["connector_source"] == "shopify_admin_api"
    assert result["result"]["shop_name"] == "Demo Store"


def test_probe_shopify_admin_returns_error_for_http_failure(monkeypatch):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo-store.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "test-token")

    def fake_get(*args, **kwargs):
        return _FakeResponse(401, {"errors": "Unauthorized"})

    monkeypatch.setattr(requests, "get", fake_get)
    result = probe_shopify_admin({"order_id": "1234"})
    assert result["status"] == "error"
    assert result["connector_source"] == "shopify_admin_api"
    assert result["status_code"] == 401


def test_probe_shopify_admin_retries_connection_errors(monkeypatch):
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "demo-store.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "test-token")
    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.ConnectionError("temporary failure")
        return _FakeResponse(200, {"shop": {"name": "Demo Store"}})

    monkeypatch.setattr(requests, "get", fake_get)
    result = probe_shopify_admin({}, retries=1)
    assert result["status"] == "ok"
    assert calls["count"] == 2
