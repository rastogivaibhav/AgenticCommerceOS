"""Spree webhook ingress for the Ops API."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import Response

from acosplatform.db.repository import find_crm_customer_by_phone, get_crm_customer_by_id, save_crm_case
from acosplatform.evidence.store import EvidenceEvent, record_evidence
from acosplatform.journey.engine import run_journey
from integrations.telegram.client import send_telegram_message
from integrations.whatsapp.client import execute_whatsapp_action

logger = logging.getLogger(__name__)
router = APIRouter(tags=["spree-webhooks"])


def verify_spree_webhook_signature(raw_body: bytes, signature: str, timestamp: str, secret: str) -> bool:
    try:
        timestamp_int = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - timestamp_int) > 300:
        return False
    raw_body_str = raw_body.decode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), f"{timestamp}.{raw_body_str}".encode("utf-8"), hashlib.sha256).hexdigest()
    supplied = (signature or "").removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, supplied)


def _is_non_production() -> bool:
    return os.environ.get("OPS_ENVIRONMENT", "dev").strip().lower() in {"dev", "development", "local", "test", "testing"}


def _verify_or_raise(raw_body: bytes, signature: str | None, timestamp: str | None, secret: str | None) -> None:
    secret = secret or ""
    if not secret:
        if _is_non_production():
            logger.warning("Spree webhook secret is empty; signature verification bypassed in non-production.")
            return
        raise HTTPException(status_code=503, detail="Webhook authentication is not configured")
    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Webhook authentication failed")
    if not verify_spree_webhook_signature(raw_body, signature, timestamp, secret):
        raise HTTPException(status_code=401, detail="Webhook authentication failed")


def _webhook_resource(event_data: dict[str, Any]) -> dict[str, Any]:
    resource = event_data.get("order") or event_data.get("resource") or event_data
    return resource if isinstance(resource, dict) else {}


def _receipt_payload(event_name: str | None, event_data: dict[str, Any], tenant_id: str, event_id: str) -> dict[str, Any]:
    resource = _webhook_resource(event_data)
    return {
        "event_id": event_id,
        "event_name": event_name,
        "tenant_id": tenant_id,
        "resource_id": resource.get("id"),
        "order_number": resource.get("number"),
        "status": resource.get("state") or resource.get("status"),
    }


@router.post("/api/v1/webhooks/spree")
async def receive_spree_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_spree_signature: str | None = Header(default=None),
    x_spree_timestamp: str | None = Header(default=None),
    x_spree_webhook_signature: str | None = Header(default=None),
    x_spree_webhook_timestamp: str | None = Header(default=None),
    x_spree_tenant_id: str | None = Header(default=None),
) -> Response:
    raw_body = await request.body()
    signature = x_spree_webhook_signature or x_spree_signature
    timestamp = x_spree_webhook_timestamp or x_spree_timestamp
    _verify_or_raise(raw_body, signature, timestamp, os.environ.get("SPREE_WEBHOOK_SECRET"))
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    event_name = payload.get("event_name") or payload.get("name") or payload.get("event")
    event_data = payload.get("event_data") or payload.get("data") or {}
    tenant_id = x_spree_tenant_id or "default"
    event_id = str(payload.get("id") or payload.get("event_id") or f"spree_evt_{uuid4().hex[:12]}")
    record_evidence(
        EvidenceEvent(
            event_type="spree.webhook.received",
            tenant_id=tenant_id,
            correlation_id=event_id,
            payload=_receipt_payload(event_name, event_data if isinstance(event_data, dict) else {}, tenant_id, event_id),
        )
    )
    background_tasks.add_task(_dispatch_spree_event, event_name, event_data, tenant_id, event_id)
    return Response(status_code=200)


def _dispatch_spree_event(event_name: str | None, event_data: dict[str, Any], tenant_id: str, event_id: str | None = None) -> None:
    handlers = {
        "order.completed": _handle_order_completed,
        "shipment.shipped": _handle_shipment_shipped,
        "return_authorization.received": _handle_return_received,
        "payment.failed": _handle_payment_failed,
        "order.canceled": _handle_order_canceled,
        "variant.stock_changed": _handle_stock_changed,
    }
    handler = handlers.get(event_name or "")
    if not handler:
        logger.info("Ignoring unrecognised Spree webhook event: %s", event_name)
        return
    try:
        handler(event_data or {}, tenant_id)
    except Exception as exc:
        logger.error("Spree webhook handler failed for %s: %s", event_name, exc, exc_info=True)
        record_evidence(
            EvidenceEvent(
                event_type="spree.webhook.failed",
                tenant_id=tenant_id,
                correlation_id=event_id or f"spree_evt_{uuid4().hex[:12]}",
                payload={"event_name": event_name, "event_id": event_id, "status": "failed", "error": exc.__class__.__name__},
            )
        )


def _handle_order_completed(event_data: dict[str, Any], tenant_id: str) -> None:
    order = _order_payload(event_data)
    run_journey(
        {
            "tenant_id": tenant_id,
            "customer_id": _customer_id(event_data),
            "journey_type": "post_purchase",
            "message": f"Spree order completed: {order.get('id') or order.get('number')}",
            "order": order,
        }
    )


def _handle_shipment_shipped(event_data: dict[str, Any], tenant_id: str) -> None:
    customer = _lookup_customer(event_data)
    order = _order_payload(event_data)
    text = f"Your order {order.get('number') or order.get('id') or ''} has shipped.".strip()
    if customer and customer.get("phone"):
        result = execute_whatsapp_action("send_message", {"to": customer["phone"], "text": text})
        if result.get("status") == "ok":
            return
    telegram_chat_id = (customer or {}).get("telegram_chat_id") or (customer or {}).get("metadata", {}).get("telegram_chat_id")
    if telegram_chat_id:
        send_telegram_message(text, chat_id=telegram_chat_id)
        return
    logger.warning("No customer notification channel found for Spree shipment event.")
    record_evidence(
        EvidenceEvent(
            event_type="webhook.notification.no_channel",
            tenant_id=tenant_id,
            correlation_id=str(event_data.get("id") or f"spree_evt_{uuid4().hex[:12]}"),
            payload={"event": "shipment.shipped", "customer": customer or {}, "order": order},
        )
    )


def _handle_return_received(event_data: dict[str, Any], tenant_id: str) -> None:
    order = _order_payload(event_data)
    save_crm_case(
        {
            "id": f"case_spree_{uuid4().hex[:8]}",
            "tenant_id": tenant_id,
            "customer_id": _customer_id(event_data),
            "subject": f"Spree return received for {order.get('number') or order.get('id') or 'order'}",
            "summary": json.dumps(event_data, default=str),
            "channel": "spree_webhook",
            "status": "open",
            "priority": "medium",
        }
    )


def _handle_payment_failed(event_data: dict[str, Any], tenant_id: str) -> None:
    run_journey(
        {
            "tenant_id": tenant_id,
            "customer_id": _customer_id(event_data),
            "journey_type": "service",
            "message": "Spree payment failed",
            "payment": event_data.get("payment") or event_data,
        }
    )


def _handle_order_canceled(event_data: dict[str, Any], tenant_id: str) -> None:
    run_journey(
        {
            "tenant_id": tenant_id,
            "customer_id": _customer_id(event_data),
            "journey_type": "service",
            "message": "Spree order canceled",
            "order": _order_payload(event_data),
        }
    )


def _handle_stock_changed(event_data: dict[str, Any], tenant_id: str) -> None:
    previous_in_stock = _as_bool(event_data.get("previous_in_stock") if "previous_in_stock" in event_data else event_data.get("was_in_stock"))
    current_in_stock = _as_bool(event_data.get("in_stock"))
    if previous_in_stock or not current_in_stock:
        return
    variant_id = str(event_data.get("variant_id") or (event_data.get("variant") or {}).get("id") or "")
    for subscriber in get_wishlist_subscribers(variant_id, tenant_id=tenant_id):
        run_journey(
            {
                "tenant_id": tenant_id,
                "customer_id": subscriber.get("customer_id") or subscriber.get("id") or "unknown",
                "journey_type": "engagement",
                "message": "Wishlist item is back in stock",
                "variant_id": variant_id,
                "subscriber": subscriber,
            }
        )


def get_wishlist_subscribers(variant_id: str, tenant_id: str = "default") -> list[dict[str, Any]]:
    return []


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _order_payload(event_data: dict[str, Any]) -> dict[str, Any]:
    order = event_data.get("order") or event_data.get("resource") or event_data
    return order if isinstance(order, dict) else {}


def _customer_id(event_data: dict[str, Any]) -> str:
    customer = event_data.get("customer") if isinstance(event_data.get("customer"), dict) else {}
    return str(event_data.get("customer_id") or customer.get("id") or "spree-customer")


def _lookup_customer(event_data: dict[str, Any]) -> dict[str, Any] | None:
    customer_id = _customer_id(event_data)
    customer = get_crm_customer_by_id(customer_id)
    if customer:
        return customer
    customer_payload = event_data.get("customer") if isinstance(event_data.get("customer"), dict) else {}
    phone = event_data.get("phone") or customer_payload.get("phone") or customer_payload.get("phone_number")
    return find_crm_customer_by_phone(phone) if phone else None
