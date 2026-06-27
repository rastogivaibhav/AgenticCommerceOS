"""Verify the real Spree + ACOS ecommerce demo stack.

Run after:
  docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml up --build -d
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from typing import Any

import requests


DEFAULT_ACOS_URL = os.environ.get("ACOS_OPS_URL", "http://127.0.0.1:8081").rstrip("/")
DEFAULT_SPREE_URL = os.environ.get("SPREE_PUBLIC_URL", "http://127.0.0.1:3000").rstrip("/")
DEFAULT_SPREE_TOKEN = os.environ.get("SPREE_BEARER_TOKEN", "pk_acos_demo_publishable_key")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ACOS + real Spree ecommerce demo.")
    parser.add_argument("--acos-url", default=DEFAULT_ACOS_URL)
    parser.add_argument("--spree-url", default=DEFAULT_SPREE_URL)
    parser.add_argument("--spree-token", default=DEFAULT_SPREE_TOKEN)
    parser.add_argument("--env-file", default=".env.ecom-demo")
    parser.add_argument("--skip-webhook", action="store_true")
    args = parser.parse_args()

    checks: list[tuple[str, bool, Any]] = []

    checks.append(("ACOS health", True, wait_json(f"{args.acos_url}/health", expected_status=200)))
    checks.append(("Spree health", True, wait_text(f"{args.spree_url}/up", expected_status=200)))

    products_payload = get_json(
        f"{args.spree_url}/api/v3/store/products",
        headers=spree_headers(args.spree_token),
    )
    products = products_payload.get("data") or []
    checks.append(("Spree Store API products", bool(products), {"count": len(products), "first": summarize_product(products[0]) if products else None}))

    message_payload = {
        "tenant_id": "default",
        "channel": "web",
        "channel_user_id": "ecom-demo-user",
        "customer_id": "cust_1001",
        "text": "Find me a product under 250 and check if it is available.",
    }
    journey = post_json(f"{args.acos_url}/api/northstar/messages", message_payload, timeout=45)
    sources = sorted(set(find_values(journey, "source")))
    checks.append(
        (
            "ACOS agent journey uses Spree",
            journey.get("status") == "success" and "spree" in sources,
            {"status": journey.get("status"), "intent": (journey.get("intent") or {}).get("intent"), "sources": sources},
        )
    )

    connector_payload = get_json(
        f"{args.acos_url}/api/v1/connectors/bindings",
        headers=ops_auth_headers(args.env_file),
    )
    bindings = connector_payload.get("bindings") or []
    spree_binding = next((item for item in bindings if item.get("connector_type") == "spree"), None)
    checks.append(("Ops connector registry shows Spree", bool(spree_binding), spree_binding or connector_payload))

    shopper_demo = post_json(
        f"{args.acos_url}/api/northstar/demo/agentic-shopper/run",
        {"message": "Please buy the oxford shirt and tell me my order details from last week."},
        timeout=60,
    )
    shopper_transactions = shopper_demo.get("control_plane", {}).get("transactions") or []
    shopper_surface = shopper_demo.get("spree_surface") or {}
    shopper_timeline = shopper_demo.get("control_plane", {}).get("event_timeline") or []
    checks.append(
        (
            "Shopper demo proves checkout plus webhook",
            shopper_demo.get("status") == "success"
            and any(item.get("label") == "Spree Webhook" for item in shopper_transactions)
            and shopper_surface.get("surface_mode") == "store_api_admin_portal_webhooks"
            and shopper_surface.get("rails_env") == "production"
            and bool(shopper_surface.get("admin_orders_url"))
            and shopper_surface.get("webhook_event") == "order.completed"
            and any(item.get("event_type") == "spree.webhook.received" for item in shopper_timeline),
            {
                "status": shopper_demo.get("status"),
                "response_text": shopper_demo.get("response_text"),
                "surface": {
                    "mode": shopper_surface.get("surface_mode"),
                    "rails_env": shopper_surface.get("rails_env"),
                    "admin_orders_url": shopper_surface.get("admin_orders_url"),
                    "webhook_event": shopper_surface.get("webhook_event"),
                    "webhook_order_number": shopper_surface.get("webhook_order_number"),
                },
                "transactions": shopper_transactions,
            },
        )
    )

    if not args.skip_webhook:
        webhook_result = post_signed_spree_webhook(args.acos_url, args.env_file)
        checks.append(("ACOS accepts signed Spree webhook", webhook_result.get("success") is True, webhook_result))

    failed = False
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        print(json.dumps(detail, indent=2, default=str)[:3000])
        failed = failed or not ok

    print("\nDemo URLs:")
    print(f"- ACOS Ops UI: {args.acos_url}/ui/estate")
    print(f"- Spree backend/API: {args.spree_url}")
    return 1 if failed else 0


def wait_json(url: str, *, expected_status: int, timeout_seconds: int = 180) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == expected_status:
                return response.json()
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
        except requests.RequestException as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
        time.sleep(3)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def wait_text(url: str, *, expected_status: int, timeout_seconds: int = 180) -> str:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == expected_status:
                return response.text[:500]
            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
        except requests.RequestException as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
        time.sleep(3)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def get_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 15) -> dict[str, Any]:
    response = requests.get(url, headers=headers or {}, timeout=timeout)
    response.raise_for_status()
    return response.json()


def post_json(url: str, payload: dict[str, Any], *, timeout: int = 15) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def spree_headers(token: str) -> dict[str, str]:
    return {"X-Spree-API-Key": token} if token else {}


def summarize_product(resource: dict[str, Any]) -> dict[str, Any]:
    attrs = resource.get("attributes") or {}
    price = resource.get("price") if isinstance(resource.get("price"), dict) else {}
    return {
        "id": resource.get("id"),
        "name": resource.get("name") or attrs.get("name"),
        "price": (price or {}).get("amount") or attrs.get("price"),
        "currency": (price or {}).get("currency") or attrs.get("currency"),
        "in_stock": resource.get("in_stock") if resource.get("in_stock") is not None else attrs.get("in_stock"),
    }


def find_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key == key:
                found.append(item_value)
            found.extend(find_values(item_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_values(item, key))
    return found


def ops_auth_headers(env_file: str) -> dict[str, str]:
    secret = env_value(env_file, "OPS_JWT_SECRET", "dev-ops-secret-change-me")
    now = int(time.time())
    token = jwt_hs256(
        {"alg": "HS256", "typ": "JWT"},
        {"sub": "ecom-demo-verifier", "role": "admin", "roles": ["admin"], "iat": now, "exp": now + 3600},
        secret,
    )
    return {"Authorization": f"Bearer {token}"}


def jwt_hs256(header: dict[str, Any], payload: dict[str, Any], secret: str) -> str:
    header_part = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{b64url(signature)}"


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def env_value(env_file: str, key: str, default: str) -> str:
    value = os.environ.get(key)
    if value:
        return value
    try:
        with open(env_file, "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'") or default
    except OSError:
        pass
    return default


def post_signed_spree_webhook(acos_url: str, env_file: str) -> dict[str, Any]:
    secret = env_value(env_file, "SPREE_WEBHOOK_SECRET", "dev-spree-webhook-secret")
    timestamp = str(int(time.time()))
    payload = {
        "id": "evt_acos_demo_order_completed",
        "name": "order.completed",
        "data": {
            "order": {"id": "acos-demo-order", "number": "ACOS-DEMO-ORDER", "total": "199.00"},
            "customer_id": "cust_1001",
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode("utf-8") + body, hashlib.sha256).hexdigest()
    response = requests.post(
        f"{acos_url.rstrip('/')}/api/v1/webhooks/spree",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Spree-Webhook-Timestamp": timestamp,
            "X-Spree-Webhook-Signature": signature,
            "X-Spree-Webhook-Event": "order.completed",
        },
        timeout=15,
    )
    return {"success": response.status_code < 400, "status_code": response.status_code, "body": response.text[:1000]}


if __name__ == "__main__":
    sys.exit(main())
