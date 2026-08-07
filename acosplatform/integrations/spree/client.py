"""Spree Commerce Store API client for ACOS retail tools."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any
import requests
import re


class SpreeConnectionError(OSError):
    """Raised when ACOS cannot safely communicate with Spree."""

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class SpreeAPIError(RuntimeError):
    """Raised for non-retriable Spree API errors."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class SpreeClient:
    """Small stateless bridge around Spree Commerce Store API v3."""

    def __init__(
        self,
        base_url: str | None = None,
        bearer_token: str | None = None,
        allow_http: bool = False,
        timeout: float = 5.0,
        refresh_token: str | None = None,
        api_key: str | None = None,
    ):
        resolved_base_url = (base_url or os.environ.get("SPREE_BASE_URL") or "").strip()
        if not resolved_base_url:
            raise ValueError("Spree base_url is required")
        if resolved_base_url.lower().startswith("http://") and not allow_http:
            raise ValueError("Spree base_url must use HTTPS unless allow_http=True")

        self.base_url = resolved_base_url.rstrip("/")
        resolved_bearer_token = bearer_token or os.environ.get("SPREE_BEARER_TOKEN") or ""
        resolved_api_key = api_key or os.environ.get("SPREE_API_KEY") or ""
        if not resolved_api_key and self._looks_like_api_key(resolved_bearer_token):
            resolved_api_key = resolved_bearer_token
            resolved_bearer_token = ""
        self.api_key = resolved_api_key
        self.bearer_token = resolved_bearer_token
        self.timeout = float(timeout)
        self.refresh_token = refresh_token or os.environ.get("SPREE_REFRESH_TOKEN") or ""

    def __repr__(self) -> str:
        return (
            f"SpreeClient(base_url={self.base_url!r}, credential='****', "
            f"allow_http={self.base_url.startswith('http://')}, timeout={self.timeout!r})"
        )

    __str__ = __repr__

    def _store_url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        bearer_token: str | None = None,
        extra_headers: dict[str, Any] | None = None,
        retry_on_expired_token: bool = True,
    ) -> requests.Response:
        token = bearer_token if bearer_token is not None else self.bearer_token
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            headers["X-Spree-API-Key"] = self.api_key
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update({str(key): str(value) for key, value in extra_headers.items() if value is not None})

        try:
            with requests.Session() as session:
                response = session.request(
                    method.upper(),
                    self._store_url(path),
                    params=params or None,
                    json=json,
                    headers=headers,
                    timeout=self.timeout,
                )
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise SpreeConnectionError(str(exc), 0) from exc

        if response.status_code == 401:
            if retry_on_expired_token and self._is_token_expired(response):
                refreshed_token = self._refresh_access_token()
                retry_response = self._request(
                    method,
                    path,
                    params=params,
                    json=json,
                    bearer_token=refreshed_token,
                    extra_headers=extra_headers,
                    retry_on_expired_token=False,
                )
                if retry_response.status_code == 401:
                    raise SpreeConnectionError("Spree authentication failed after token refresh", 401)
                return retry_response
            raise SpreeConnectionError("Spree authentication failed", 401)

        if response.status_code >= 500:
            raise SpreeConnectionError(f"Spree server error {response.status_code}", response.status_code)
        if 400 <= response.status_code < 500 and response.status_code not in {404, 422}:
            raise SpreeAPIError(self._error_message(response), response.status_code)
        return response

    def _refresh_access_token(self) -> str:
        if not self.refresh_token:
            raise SpreeConnectionError("Spree token expired and no refresh token is configured", 401)
        response = self._request(
            "POST",
            "/api/v3/store/auth/refresh",
            json={"refresh_token": self.refresh_token},
            bearer_token="",
            retry_on_expired_token=False,
        )
        if response.status_code >= 400:
            raise SpreeConnectionError("Spree token refresh failed", response.status_code)
        body = self._json(response)
        token = (
            body.get("access_token")
            or body.get("bearer_token")
            or body.get("token")
            or body.get("jwt")
            or (body.get("data") or {}).get("access_token")
        )
        if not token:
            raise SpreeConnectionError("Spree token refresh response did not include an access token", response.status_code)
        return str(token)

    @staticmethod
    def _json(response: requests.Response) -> dict[str, Any]:
        if not response.content:
            return {}
        try:
            body = response.json()
        except ValueError:
            return {}
        return body if isinstance(body, dict) else {}

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        body = SpreeClient._json(response)
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                return str(first.get("detail") or first.get("title") or first)
            return str(first)
        return str(body.get("error") or body.get("message") or f"Spree HTTP {response.status_code}")

    @staticmethod
    def _is_token_expired(response: requests.Response) -> bool:
        haystack = f"{response.text or ''} {SpreeClient._json(response)}".lower()
        return "expired" in haystack or "token_expired" in haystack or "jwt expired" in haystack

    @staticmethod
    def _looks_like_api_key(token: str) -> bool:
        return token.startswith(("pk_", "sk_"))

    @staticmethod
    def _resource(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            return data
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _resources(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list):
            return data
        if isinstance(payload, list):
            return payload
        return []

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value or default)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(value: Any, default: int = 0) -> int:
        try:
            return int(float(value or default))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _included_by_type(payload: dict[str, Any], resource_type: str) -> dict[str, dict[str, Any]]:
        included = payload.get("included") if isinstance(payload, dict) else None
        if not isinstance(included, list):
            return {}
        return {
            str(item.get("id")): item
            for item in included
            if isinstance(item, dict) and str(item.get("type", "")).lower().endswith(resource_type)
        }

    def _extract_variants(self, product: dict[str, Any], payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if isinstance(product.get("variants"), list):
            variants = []
            for variant in product.get("variants") or []:
                if not isinstance(variant, dict):
                    continue
                price = variant.get("price") if isinstance(variant.get("price"), dict) else {}
                variants.append(
                    {
                        "id": str(variant.get("id") or ""),
                        "sku": variant.get("sku"),
                        "price": self._float((price or {}).get("amount") or variant.get("price_amount") or variant.get("price")),
                        "currency": (price or {}).get("currency") or variant.get("currency"),
                        "in_stock": bool(variant.get("in_stock", variant.get("purchasable", True))),
                        "purchasable_quantity": self._int(variant.get("purchasable_quantity") or variant.get("total_on_hand")),
                        "total_on_hand": self._int(variant.get("total_on_hand") or variant.get("purchasable_quantity")),
                        "options_text": variant.get("options_text"),
                    }
                )
            return variants
        relationships = product.get("relationships") or {}
        variant_refs = ((relationships.get("variants") or {}).get("data") or [])
        included_variants = self._included_by_type(payload or {}, "variant")
        variants = []
        for ref in variant_refs:
            variant = included_variants.get(str(ref.get("id")), ref)
            attrs = variant.get("attributes") or {}
            variants.append(
                {
                    "id": str(variant.get("id") or ref.get("id")),
                    "sku": attrs.get("sku"),
                    "price": self._float(attrs.get("price") or attrs.get("display_price")),
                    "currency": attrs.get("currency"),
                    "in_stock": bool(attrs.get("in_stock", attrs.get("purchasable", True))),
                    "purchasable_quantity": self._int(attrs.get("purchasable_quantity")),
                    "total_on_hand": self._int(attrs.get("total_on_hand")),
                }
            )
        return variants

    def _transform_product(self, product: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        product = self._resource(product)
        attrs = product.get("attributes") or {}
        price = product.get("price") if isinstance(product.get("price"), dict) else {}
        result = {
            "id": str(product.get("id") or attrs.get("id") or ""),
            "name": product.get("name") or attrs.get("name"),
            "price": self._float((price or {}).get("amount") or attrs.get("price") or attrs.get("display_price")),
            "currency": (price or {}).get("currency") or product.get("currency") or attrs.get("currency"),
            "in_stock": bool(product.get("in_stock", attrs.get("in_stock", product.get("purchasable", attrs.get("purchasable", True))))),
            "description": product.get("description") or attrs.get("description"),
            "slug": product.get("slug") or attrs.get("slug"),
            "tags": product.get("tags") or attrs.get("tags") or attrs.get("tag_list") or [],
            "default_variant_id": product.get("default_variant_id") or attrs.get("default_variant_id"),
        }
        relationships = product.get("relationships") or {}
        if isinstance(product.get("variants"), list) or "variants" in relationships:
            result["variants"] = self._extract_variants(product, payload)
        return result

    def _transform_order(self, order: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        order = self._resource(order)
        attrs = order.get("attributes") or {}
        relationships = order.get("relationships") or {}
        line_refs = ((relationships.get("line_items") or {}).get("data") or [])
        included_line_items = self._included_by_type(payload or {}, "line_item")
        line_items = []
        inline_line_items = attrs.get("line_items")
        if not isinstance(inline_line_items, list) and isinstance(order.get("items"), list):
            inline_line_items = order.get("items")
        if isinstance(inline_line_items, list):
            for item in inline_line_items:
                if isinstance(item, dict):
                    line_items.append(
                        {
                            "id": str(item.get("id") or ""),
                            "name": item.get("name"),
                            "quantity": self._int(item.get("quantity"), 1),
                            "price": self._float(item.get("price") or item.get("amount")),
                            "total": self._float(item.get("total") or item.get("amount")),
                        }
                    )
        for ref in line_refs:
            item = included_line_items.get(str(ref.get("id")), ref)
            item_attrs = item.get("attributes") or {}
            line_items.append(
                {
                    "id": str(item.get("id") or ref.get("id")),
                    "name": item_attrs.get("name"),
                    "quantity": self._int(item_attrs.get("quantity"), 1),
                    "price": self._float(item_attrs.get("price")),
                    "total": self._float(item_attrs.get("total")),
                }
            )
        return {
            "order_id": str(order.get("number") or attrs.get("number") or order.get("id") or ""),
            "status": order.get("state") or order.get("status") or attrs.get("state") or attrs.get("status"),
            "total": self._float(order.get("total") or attrs.get("total")),
            "currency": order.get("currency") or attrs.get("currency"),
            "line_items": line_items,
            "shipment_state": order.get("shipment_state") or order.get("fulfillment_status") or attrs.get("shipment_state"),
            "completed_at": order.get("completed_at") or attrs.get("completed_at"),
        }

    def _transform_store_credits(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        voucher_value = 0.0
        currency = None
        for record in records or []:
            attrs = record.get("attributes") or {}
            voucher_value += self._float(attrs.get("amount_remaining"))
            currency = currency or attrs.get("currency")
        tier = "gold" if voucher_value >= 50 else "silver" if voucher_value >= 10 else "bronze"
        return {
            "points": int(voucher_value * 100),
            "voucher_value": voucher_value,
            "tier": tier,
            "currency": currency,
        }

    def _transform_stock(self, product: dict[str, Any], product_id: str, location: str | None = None) -> dict[str, Any]:
        payload = product
        product = self._resource(product)
        attrs = product.get("attributes") or {}
        variants = self._extract_variants(product, payload)
        if variants:
            quantity = sum(self._int(variant.get("purchasable_quantity")) for variant in variants)
        else:
            quantity = self._int(attrs.get("total_on_hand") or attrs.get("purchasable_quantity"))
        return {
            "product_id": product_id,
            "available": quantity > 0,
            "quantity": quantity,
            "location": location or "default",
        }

    def _transform_cart(self, cart: dict[str, Any]) -> dict[str, Any]:
        cart = self._resource(cart)
        attrs = cart.get("attributes") or {}
        items = cart.get("items") if isinstance(cart.get("items"), list) else attrs.get("items")
        return {
            "cart_id": str(cart.get("id") or attrs.get("id") or ""),
            "cart_number": str(cart.get("number") or attrs.get("number") or ""),
            "cart_token": str(cart.get("token") or attrs.get("token") or ""),
            "item_count": self._int(cart.get("total_quantity") or attrs.get("item_count")),
            "subtotal": self._float(cart.get("item_total") or attrs.get("item_total") or attrs.get("subtotal")),
            "total": self._float(cart.get("total") or attrs.get("total")),
            "currency": cart.get("currency") or attrs.get("currency"),
            "amount_due": self._float(cart.get("amount_due") or attrs.get("amount_due") or cart.get("total") or attrs.get("total")),
            "items": items if isinstance(items, list) else [],
        }

    def _transform_payment(self, payment: dict[str, Any]) -> dict[str, Any]:
        payment = self._resource(payment)
        attrs = payment.get("attributes") or {}
        payment_method = payment.get("payment_method") or attrs.get("payment_method") or {}
        return {
            "payment_id": str(payment.get("id") or ""),
            "payment_method_id": payment.get("payment_method_id") or attrs.get("payment_method_id"),
            "amount": self._float(payment.get("amount") or attrs.get("amount")),
            "display_amount": payment.get("display_amount") or attrs.get("display_amount"),
            "status": payment.get("status") or attrs.get("status"),
            "payment_method": {
                "id": payment_method.get("id"),
                "name": payment_method.get("name"),
                "type": payment_method.get("type"),
            } if isinstance(payment_method, dict) and payment_method else None,
        }

    @staticmethod
    def _query_terms(value: str | None) -> list[str]:
        text = re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()
        return [term for term in text.split() if term]

    @staticmethod
    def _cart_headers(cart_token: str | None) -> dict[str, Any]:
        return {"X-Spree-Token": cart_token} if cart_token else {}

    def catalog_search(
        self,
        query: str | None = None,
        category: str | None = None,
        budget: float | None = None,
        tags: list[str] | None = None,
        in_stock: bool | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if query:
            params["filter[search]"] = query
        if budget is not None:
            params["filter[price_lte]"] = budget
        if in_stock:
            params["filter[in_stock]"] = "true"
        if category:
            params["filter[in_category]"] = category
        response = self._request("GET", "/api/v3/store/products", params=params)
        payload = self._json(response)
        products = [self._transform_product(item, payload) for item in self._resources(payload)]
        query_terms = self._query_terms(query)
        if query_terms:
            filtered = []
            for product in products:
                haystack = " ".join(
                    str(value or "")
                    for value in (
                        product.get("name"),
                        product.get("slug"),
                        product.get("description"),
                        " ".join(str(tag) for tag in product.get("tags", [])),
                    )
                ).lower()
                if all(term in haystack for term in query_terms):
                    filtered.append(product)
            if filtered:
                products = filtered
        required_tags = {tag.lower() for tag in (tags or []) if tag}
        if required_tags:
            products = [
                product
                for product in products
                if required_tags.intersection({str(tag).lower() for tag in product.get("tags", [])})
            ]
        return products

    def catalog_get_product(self, product_id: str, expand_variants: bool = False) -> dict[str, Any]:
        params = {"expand": "variants"} if expand_variants else None
        response = self._request("GET", f"/api/v3/store/products/{product_id}", params=params)
        if response.status_code == 404:
            return {"id": product_id, "status": "not_found"}
        payload = self._json(response)
        return self._transform_product(payload, payload)

    def inventory_check_stock(self, product_id: str, location: str | None = None) -> dict[str, Any]:
        response = self._request("GET", f"/api/v3/store/products/{product_id}", params={"expand": "variants"})
        payload = self._json(response)
        return self._transform_stock(payload, product_id, location)

    def orders_get_order(self, order_id: str, order_token: str | None = None) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"/api/v3/store/orders/{order_id}",
            params={"expand": "line_items,shipments,fulfillments"},
            extra_headers=self._cart_headers(order_token),
        )
        if response.status_code == 404:
            return {"order_id": order_id, "status": "not_found"}
        payload = self._json(response)
        return self._transform_order(payload, payload)

    def customer_orders(self, spree_jwt: str) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/v3/store/customers/me/orders", bearer_token=spree_jwt)
        payload = self._json(response)
        return [self._transform_order(item, payload) for item in self._resources(payload)]

    def returns_check_eligibility(self, order_id: str, return_window_days: int = 30) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"/api/v3/store/orders/{order_id}",
            params={"expand": "line_items,shipments,fulfillments"},
        )
        if response.status_code == 404:
            return {"order_id": order_id, "eligible": False, "policy": f"{return_window_days}-day standard return window", "reason": "order_not_found"}
        payload = self._json(response)
        raw_order = self._resource(payload)
        attrs = raw_order.get("attributes") or {}
        order = self._transform_order(payload, payload)
        completed_at = attrs.get("completed_at") or order.get("completed_at")
        eligible = attrs.get("state") == "complete" and self._within_return_window(completed_at, return_window_days)
        result = {
            "order_id": order_id,
            "eligible": eligible,
            "policy": f"{return_window_days}-day standard return window",
        }
        if not eligible:
            result["reason"] = "outside_return_window_or_incomplete"
        return result

    @staticmethod
    def _within_return_window(completed_at: str | None, return_window_days: int) -> bool:
        if not completed_at:
            return False
        try:
            completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        except ValueError:
            return False
        return completed >= datetime.now(UTC) - timedelta(days=return_window_days)

    def returns_create_return(self, order_id: str, reason: str = "customer_request") -> dict[str, Any]:
        eligibility = self.returns_check_eligibility(order_id)
        if not eligibility.get("eligible"):
            return {"order_id": order_id, "status": "blocked", "reason": eligibility.get("reason", "not_eligible")}
        response = self._request("POST", "/api/v3/store/returns", json={"order_id": order_id, "reason": reason})
        payload = self._json(response)
        record = self._resource(payload)
        attrs = record.get("attributes") or {}
        return {"return_id": str(record.get("id") or attrs.get("number") or ""), "order_id": order_id, "status": attrs.get("state") or "created"}

    def loyalty_get_balance(self, customer_id: str | None = None, spree_jwt: str | None = None) -> dict[str, Any]:
        response = self._request("GET", "/api/v3/store/customers/me/store_credits", bearer_token=spree_jwt)
        balance = self._transform_store_credits(self._resources(self._json(response)))
        if customer_id:
            balance["customer_id"] = customer_id
        return balance

    def promotions_find_offers(self, product_ids: list[str] | None = None) -> dict[str, Any]:
        product_ids = product_ids or []
        response = self._request("GET", "/api/v3/store/products/filters")
        if response.status_code == 404:
            return {"offers": []}
        payload = self._json(response)
        offers = []
        for item in payload.get("promotions") or payload.get("offers") or []:
            if not isinstance(item, dict):
                continue
            eligible = item.get("eligible_product_ids") or item.get("product_ids") or product_ids
            if product_ids and not set(map(str, eligible)).intersection(set(map(str, product_ids))):
                continue
            offers.append(
                {
                    "id": str(item.get("id") or item.get("code") or ""),
                    "description": item.get("description") or item.get("name") or "",
                    "eligible_product_ids": list(eligible),
                }
            )
        return {"offers": offers}

    def cart_create(self) -> dict[str, Any]:
        return self._transform_cart(self._json(self._request("POST", "/api/v3/store/carts")))

    def cart_get(self, cart_id: str, cart_token: str | None = None) -> dict[str, Any]:
        response = self._request(
            "GET",
            f"/api/v3/store/carts/{cart_id}",
            extra_headers=self._cart_headers(cart_token),
        )
        if response.status_code == 404:
            return {"cart_id": cart_id, "status": "not_found"}
        return self._transform_cart(self._json(response))

    def cart_add_item(self, cart_id: str, variant_id: str, quantity: int = 1, cart_token: str | None = None) -> dict[str, Any]:
        payload = {"variant_id": variant_id, "quantity": quantity}
        return self._transform_cart(
            self._json(
                self._request(
                    "POST",
                    f"/api/v3/store/carts/{cart_id}/items",
                    json=payload,
                    extra_headers=self._cart_headers(cart_token),
                )
            )
        )

    def cart_update(
        self,
        cart_id: str,
        *,
        email: str | None = None,
        shipping_address: dict[str, Any] | None = None,
        billing_address: dict[str, Any] | None = None,
        customer_note: str | None = None,
        cart_token: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if email:
            payload["email"] = email
        if customer_note:
            payload["customer_note"] = customer_note
        if shipping_address:
            payload["shipping_address"] = shipping_address
        if billing_address:
            payload["billing_address"] = billing_address
        return self._transform_cart(
            self._json(
                self._request(
                    "PATCH",
                    f"/api/v3/store/carts/{cart_id}",
                    json=payload,
                    extra_headers=self._cart_headers(cart_token),
                )
            )
        )

    def cart_remove_item(self, cart_id: str, line_item_id: str, cart_token: str | None = None) -> dict[str, Any]:
        return self._transform_cart(
            self._json(
                self._request(
                    "DELETE",
                    f"/api/v3/store/carts/{cart_id}/items/{line_item_id}",
                    extra_headers=self._cart_headers(cart_token),
                )
            )
        )

    def cart_apply_discount(self, cart_id: str, code: str, cart_token: str | None = None) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/v3/store/carts/{cart_id}/discount_codes",
            json={"code": code},
            extra_headers=self._cart_headers(cart_token),
        )
        if response.status_code == 422:
            return {"code": "invalid_discount_code", "message": self._error_message(response)}
        return self._transform_cart(self._json(response))

    def cart_apply_store_credit(self, cart_id: str, spree_jwt: str | None = None, cart_token: str | None = None) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/v3/store/carts/{cart_id}/store_credits",
            bearer_token=spree_jwt,
            extra_headers=self._cart_headers(cart_token),
        )
        return self._transform_cart(self._json(response))

    def cart_create_payment(
        self,
        cart_id: str,
        payment_method_id: str,
        *,
        amount: float | None = None,
        cart_token: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"payment_method_id": payment_method_id}
        if amount is not None:
            payload["amount"] = amount
        response = self._request(
            "POST",
            f"/api/v3/store/carts/{cart_id}/payments",
            json=payload,
            extra_headers=self._cart_headers(cart_token),
        )
        return self._transform_payment(self._json(response))

    def cart_complete(self, cart_id: str, cart_token: str | None = None) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/v3/store/carts/{cart_id}/complete",
            extra_headers=self._cart_headers(cart_token),
        )
        payload = self._json(response)
        if response.status_code == 422:
            return {"code": "cart_completion_failed", "message": self._error_message(response), "cart": self._transform_cart(payload)}
        return self._transform_order(payload, payload)


def execute_spree_tool(tool_name: str, arguments: dict[str, Any]) -> Any:
    allow_http = os.environ.get("SPREE_ALLOW_HTTP", "").strip().lower() in {"1", "true", "yes", "on"}
    client = SpreeClient(allow_http=allow_http)
    if tool_name == "catalog.search":
        return client.catalog_search(
            arguments.get("query"),
            arguments.get("category"),
            budget=arguments.get("budget"),
            tags=arguments.get("tags") or [],
            in_stock=arguments.get("in_stock"),
        )
    if tool_name == "catalog.get_product":
        return client.catalog_get_product(arguments.get("product_id"), expand_variants=bool(arguments.get("expand_variants")))
    if tool_name == "inventory.check_stock":
        return client.inventory_check_stock(arguments.get("product_id"), arguments.get("location"))
    if tool_name == "orders.get_order":
        return client.orders_get_order(arguments.get("order_id"), order_token=arguments.get("order_token"))
    if tool_name == "loyalty.get_balance":
        return client.loyalty_get_balance(arguments.get("customer_id"), arguments.get("spree_jwt"))
    if tool_name == "promotions.find_offers":
        return client.promotions_find_offers(arguments.get("product_ids") or [])
    if tool_name == "cart.update":
        return client.cart_update(
            arguments.get("cart_id"),
            email=arguments.get("email"),
            shipping_address=arguments.get("shipping_address"),
            billing_address=arguments.get("billing_address"),
            customer_note=arguments.get("customer_note"),
            cart_token=arguments.get("cart_token"),
        )
    if tool_name == "payments.create":
        return client.cart_create_payment(
            arguments.get("cart_id"),
            arguments.get("payment_method_id"),
            amount=arguments.get("amount"),
            cart_token=arguments.get("cart_token"),
        )
    return {"status": "unsupported", "error": f"Tool {tool_name} not implemented for Spree"}
