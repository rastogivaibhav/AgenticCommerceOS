"""Shopify Admin API probe helpers for connector credibility checks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

_RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
_DEFAULT_TIMEOUT_SECONDS = 4.0
_DEFAULT_API_VERSION = "2024-10"


@dataclass(frozen=True)
class ShopifyConfig:
    """Resolved Shopify Admin API configuration."""

    store_domain: str
    admin_access_token: str
    api_version: str = _DEFAULT_API_VERSION


def load_shopify_config() -> ShopifyConfig | None:
    """Load Shopify config from environment variables."""
    store_domain = (
        os.environ.get("SHOPIFY_STORE_DOMAIN")
        or os.environ.get("SHOPIFY_SHOP_DOMAIN")
        or ""
    ).strip()
    token = (
        os.environ.get("SHOPIFY_ADMIN_ACCESS_TOKEN")
        or os.environ.get("SHOPIFY_ACCESS_TOKEN")
        or ""
    ).strip()
    api_version = (os.environ.get("SHOPIFY_API_VERSION") or _DEFAULT_API_VERSION).strip()
    if not store_domain or not token:
        return None
    normalized_domain = (
        store_domain.replace("https://", "").replace("http://", "").strip("/")
    )
    if not normalized_domain:
        return None
    return ShopifyConfig(
        store_domain=normalized_domain,
        admin_access_token=token,
        api_version=api_version or _DEFAULT_API_VERSION,
    )


def is_shopify_configured() -> bool:
    """Whether enough environment configuration exists for Shopify probing."""
    return load_shopify_config() is not None


def execute_shopify_action(
    action: str,
    payload: dict[str, Any],
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    retries: int = 1,
) -> dict[str, Any]:
    """Execute a narrow set of Shopify Admin API actions with honest fallback."""
    config = load_shopify_config()
    if not config:
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action,
            "connector_source": "local_fallback",
            "note": "shopify_not_configured",
            "result": _shopify_sandbox_result(action, payload),
        }

    action_key = (action or "").strip().lower()
    if action_key == "get_order":
        order_id = str(payload.get("order_id") or "").strip()
        if not order_id:
            return _unsupported_shopify_action(action_key, "missing_order_id", payload)
        if order_id.isdigit():
            endpoint = f"/orders/{order_id}.json"
            params = {"status": "any"}
        else:
            endpoint = "/orders.json"
            params = {"status": "any", "limit": 1, "name": order_id}
    elif action_key == "get_customer":
        customer_id = str(payload.get("customer_id") or "").strip()
        if not customer_id:
            return _unsupported_shopify_action(action_key, "missing_customer_id", payload)
        if customer_id.isdigit():
            endpoint = f"/customers/{customer_id}.json"
            params = {}
        else:
            endpoint = "/customers/search.json"
            params = {"query": customer_id}
    elif action_key == "get_product":
        product_id = str(payload.get("product_id") or "").strip()
        if not product_id:
            return _unsupported_shopify_action(action_key, "missing_product_id", payload)
        if product_id.isdigit():
            endpoint = f"/products/{product_id}.json"
            params = {}
        else:
            endpoint = "/products.json"
            params = {"limit": 1, "handle": product_id}
    elif action_key == "create_return_intent":
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action_key,
            "connector_source": "shopify_admin_api",
            "note": "mutation_not_enabled_for_demo",
            "result": _shopify_sandbox_result(action_key, payload),
        }
    else:
        return _unsupported_shopify_action(action_key, "unsupported_action", payload)

    response = _shopify_get(
        config=config,
        endpoint=endpoint,
        params=params,
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    if not response["ok"]:
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action_key,
            "connector_source": "shopify_admin_api",
            "error": response.get("error"),
            "note": "shopify_request_failed",
            "result": _shopify_sandbox_result(action_key, payload),
        }

    body = response["body"]
    if action_key == "get_order":
        result = _normalize_order_result(body)
    elif action_key == "get_customer":
        result = _normalize_customer_result(body)
    else:
        result = _normalize_product_result(body)

    return {
        "status": "ok",
        "mode": "live",
        "action": action_key,
        "connector_source": "shopify_admin_api",
        "store_domain": config.store_domain,
        "api_version": config.api_version,
        "result": result,
    }


def probe_shopify_admin(
    input_payload: dict[str, Any],
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    retries: int = 1,
) -> dict[str, Any]:
    """Probe Shopify Admin API with lightweight endpoints.

    Probe selection:
    - `order_id` -> order lookup
    - `product_id` -> product lookup
    - otherwise -> shop metadata ping
    """
    config = load_shopify_config()
    if not config:
        return {
            "status": "skipped",
            "connector_source": "local_fallback",
            "reason": "shopify_not_configured",
            "configured": False,
        }

    order_id = str(input_payload.get("order_id") or "").strip()
    product_id = str(input_payload.get("product_id") or "").strip()
    query = str(input_payload.get("query") or "").strip()

    if order_id:
        if order_id.isdigit():
            endpoint = f"/orders/{order_id}.json"
            params = {"status": "any"}
            probe = "order_lookup"
        else:
            endpoint = "/orders.json"
            params = {"status": "any", "limit": 1, "name": order_id}
            probe = "order_search"
    elif product_id:
        if product_id.isdigit():
            endpoint = f"/products/{product_id}.json"
            params = {}
            probe = "product_lookup"
        else:
            endpoint = "/products.json"
            params = {"limit": 1, "handle": product_id}
            probe = "product_search"
    elif query:
        endpoint = "/products.json"
        params = {"limit": 3, "title": query}
        probe = "catalog_probe"
    else:
        endpoint = "/shop.json"
        params = {}
        probe = "shop_probe"

    response = _shopify_get(
        config=config,
        endpoint=endpoint,
        params=params,
        timeout_seconds=timeout_seconds,
        retries=retries,
    )
    if not response["ok"]:
        return {
            "status": "error",
            "connector_source": "shopify_admin_api",
            "probe": probe,
            "configured": True,
            "store_domain": config.store_domain,
            "api_version": config.api_version,
            "status_code": response.get("status_code"),
            "error": response.get("error"),
            "attempts": response.get("attempts", 1),
            "request": {"endpoint": endpoint, "params": params},
        }

    body = response["body"]
    normalized_result: dict[str, Any]
    if probe in {"order_lookup", "order_search"}:
        normalized_result = _normalize_order_result(body)
    elif probe in {"product_lookup", "product_search", "catalog_probe"}:
        normalized_result = _normalize_product_result(body)
    else:
        shop = body.get("shop", {}) if isinstance(body, dict) else {}
        normalized_result = {
            "shop_name": shop.get("name"),
            "myshopify_domain": shop.get("myshopify_domain"),
            "plan_name": shop.get("plan_name"),
        }

    return {
        "status": "ok",
        "connector_source": "shopify_admin_api",
        "probe": probe,
        "configured": True,
        "store_domain": config.store_domain,
        "api_version": config.api_version,
        "attempts": response.get("attempts", 1),
        "status_code": response.get("status_code", 200),
        "request": {"endpoint": endpoint, "params": params},
        "result": normalized_result,
    }


def _shopify_get(
    *,
    config: ShopifyConfig,
    endpoint: str,
    params: dict[str, Any],
    timeout_seconds: float,
    retries: int,
) -> dict[str, Any]:
    url = (
        f"https://{config.store_domain}/admin/api/{config.api_version}/{endpoint.lstrip('/')}"
    )
    headers = {
        "X-Shopify-Access-Token": config.admin_access_token,
        "Accept": "application/json",
    }
    attempts = 0
    max_attempts = max(int(retries) + 1, 1)
    last_error: str | None = None

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=max(float(timeout_seconds), 0.2),
            )
            status_code = response.status_code
            if status_code in _RETRYABLE_STATUS_CODES and attempt < max_attempts:
                last_error = f"http_{status_code}"
                continue
            if status_code >= 400:
                return {
                    "ok": False,
                    "status_code": status_code,
                    "attempts": attempts,
                    "error": f"Shopify HTTP {status_code}",
                }
            try:
                body = response.json() if response.content else {}
            except ValueError:
                return {
                    "ok": False,
                    "status_code": status_code,
                    "attempts": attempts,
                    "error": "shopify_invalid_json",
                }
            if not isinstance(body, dict):
                return {
                    "ok": False,
                    "status_code": status_code,
                    "attempts": attempts,
                    "error": "shopify_response_not_object",
                }
            return {
                "ok": True,
                "status_code": status_code,
                "attempts": attempts,
                "body": body,
            }
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            if attempt < max_attempts:
                continue
            break

    return {
        "ok": False,
        "status_code": None,
        "attempts": attempts,
        "error": last_error or "shopify_request_failed",
    }


def _normalize_order_result(body: dict[str, Any]) -> dict[str, Any]:
    order = body.get("order")
    if not order and isinstance(body.get("orders"), list):
        order = body["orders"][0] if body["orders"] else {}
    order = order or {}
    return {
        "order_id": order.get("id"),
        "name": order.get("name"),
        "financial_status": order.get("financial_status"),
        "fulfillment_status": order.get("fulfillment_status"),
        "created_at": order.get("created_at"),
    }


def _normalize_product_result(body: dict[str, Any]) -> dict[str, Any]:
    product = body.get("product")
    if not product and isinstance(body.get("products"), list):
        product = body["products"][0] if body["products"] else {}
    product = product or {}
    return {
        "product_id": product.get("id"),
        "title": product.get("title"),
        "status": product.get("status"),
        "vendor": product.get("vendor"),
        "product_type": product.get("product_type"),
    }


def _normalize_customer_result(body: dict[str, Any]) -> dict[str, Any]:
    customer = body.get("customer")
    if not customer and isinstance(body.get("customers"), list):
        customer = body["customers"][0] if body["customers"] else {}
    customer = customer or {}
    return {
        "customer_id": customer.get("id"),
        "email": customer.get("email"),
        "first_name": customer.get("first_name"),
        "last_name": customer.get("last_name"),
        "state": customer.get("state"),
    }


def _unsupported_shopify_action(action: str, reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "ok",
        "mode": "sandbox",
        "action": action,
        "connector_source": "local_fallback",
        "note": reason,
        "result": _shopify_sandbox_result(action, payload),
    }


def _shopify_sandbox_result(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "get_customer":
        return {
            "customer_id": payload.get("customer_id") or "cust_demo",
            "email": "customer@example.com",
            "first_name": "Demo",
            "last_name": "Customer",
            "state": "enabled",
        }
    if action == "get_product":
        return {
            "product_id": payload.get("product_id") or "prod_demo",
            "title": "Demo Product",
            "status": "active",
            "vendor": "ACOS",
            "product_type": "Demo",
        }
    if action == "create_return_intent":
        return {
            "order_id": payload.get("order_id") or "ORD-1001",
            "status": "draft_return_intent",
            "reason": payload.get("reason") or "customer_request",
        }
    return {
        "order_id": payload.get("order_id") or "ORD-1001",
        "name": payload.get("order_id") or "ORD-1001",
        "financial_status": "paid",
        "fulfillment_status": "in_transit",
        "created_at": None,
    }
