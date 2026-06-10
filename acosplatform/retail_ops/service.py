"""Retail channel routing and demo dispatch service."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from acosplatform.db.repository import (
    find_crm_customer_by_phone,
    get_channel_binding,
    get_channel_pairing_by_code,
    get_channel_sender_by_external_id,
    get_crm_cases,
    get_crm_customer_by_id,
    get_demo_route,
    get_demo_routes,
    get_order_by_id,
    get_orders_for_customer,
    save_channel_pairing,
    save_channel_sender,
    save_crm_case,
)
from acosplatform.workflows.executor import execute_saved_workflow
from integrations.telegram.client import send_telegram_message
from integrations.whatsapp.client import execute_whatsapp_action

ORDER_RE = re.compile(r"\b(ORD[-\s]?\d+)\b", re.IGNORECASE)
PAIR_RE = re.compile(r"\bPAIR[\s:_-]+([A-Z0-9]{6,32})\b", re.IGNORECASE)
TELEGRAM_START_RE = re.compile(r"^/start(?:\s+|_)?pair[_-]?([A-Z0-9]{6,32})\b", re.IGNORECASE)


def infer_demo_route(message: str) -> str:
    text = (message or "").strip().lower()
    if any(token in text for token in ("where is my order", "track", "tracking", "delivery", "shipment")):
        return "order_status"
    if any(token in text for token in ("return", "refund", "exchange")):
        return "return_refund"
    if any(token in text for token in ("loyalty", "reward", "points", "discount")):
        return "loyalty_rewards"
    if any(token in text for token in ("escalate", "angry", "failed delivery", "manager", "complaint")):
        return "vip_escalation"
    return "order_status"


def ingest_channel_message(
    *,
    channel_binding_id: str,
    sender_external_id: str,
    display_name: str,
    message: str,
    tenant_id: str = "default",
    environment: str = "dev",
    explicit_route_id: str | None = None,
) -> dict:
    binding = get_channel_binding(channel_binding_id)
    if not binding:
        return {"status": "error", "error": "Channel binding not found", "channel_binding_id": channel_binding_id}

    pairing_result = _handle_pairing_message(
        channel_binding_id=channel_binding_id,
        sender_external_id=sender_external_id,
        display_name=display_name,
        message=message,
        tenant_id=tenant_id,
        environment=environment,
    )
    if pairing_result is not None:
        return pairing_result

    sender = get_channel_sender_by_external_id(channel_binding_id, sender_external_id)
    if not sender:
        sender = save_channel_sender(
            {
                "id": f"sender-{uuid4().hex[:10]}",
                "channel_binding_id": channel_binding_id,
                "sender_external_id": sender_external_id,
                "display_name": display_name or sender_external_id,
                "approval_status": "pending",
                "last_message": message,
                "last_seen_at": datetime.now(UTC).isoformat(),
                "metadata": {"channel": binding.get("type")},
            }
        )
        return {
            "status": "queued_for_approval",
            "channel_binding_id": channel_binding_id,
            "sender": sender,
            "message": "Sender queued for approval before workflow execution.",
        }

    sender["last_message"] = message
    sender["last_seen_at"] = datetime.now(UTC).isoformat()
    save_channel_sender(sender)

    if sender.get("approval_status") != "approved":
        return {
            "status": "queued_for_approval",
            "channel_binding_id": channel_binding_id,
            "sender": sender,
            "message": "Sender is not approved yet.",
        }

    return dispatch_demo_route(
        route_id=explicit_route_id or infer_demo_route(message),
        channel_binding_id=channel_binding_id,
        sender=sender,
        message=message,
        tenant_id=tenant_id,
        environment=environment,
    )


def dispatch_demo_route(
    *,
    route_id: str,
    channel_binding_id: str,
    sender: dict,
    message: str,
    tenant_id: str = "default",
    environment: str = "dev",
    allow_live_send: bool | None = None,
) -> dict:
    route = get_demo_route(route_id)
    if not route:
        return {"status": "error", "error": "Demo route not found", "route_id": route_id}

    binding = get_channel_binding(channel_binding_id) or {}
    live_send_allowed = bool(binding.get("mode") == "live") if allow_live_send is None else bool(allow_live_send and binding.get("mode") == "live")
    customer = _resolve_customer(sender)
    workflow_result = execute_saved_workflow(
        workflow_id=route.get("workflow_id") or "",
        tenant_id=tenant_id,
        customer_id=(customer or {}).get("id") or sender.get("customer_id") or "anon",
        environment=environment,
        message=message,
        order_id=_extract_order_id(message) or (customer or {}).get("last_order_id") or None,
        channel_binding_id=channel_binding_id,
        sender_external_id=sender.get("sender_external_id", ""),
        requested_provider=route.get("preferred_runtime") or "local_fallback",
        allow_live_send=live_send_allowed,
        persist_run=True,
    )

    response_text = workflow_result.get("response_text") or ""
    channel_reply = workflow_result.get("channel_reply")
    tool_trace = workflow_result.get("tool_trace") or []
    customer = workflow_result.get("customer") or customer
    crm_cases = workflow_result.get("crm_cases") or []
    notification_text = _build_notification_text(route, customer, response_text, tool_trace)
    notifications = _send_notifications(binding, notification_text, allow_live_send=live_send_allowed)

    return {
        "status": "dispatched",
        "route": route,
        "sender": sender,
        "customer": customer,
        "workflow": workflow_result.get("workflow"),
        "run_id": workflow_result.get("run_id"),
        "journey": workflow_result.get("journey"),
        "tool_trace": tool_trace,
        "crm_cases": crm_cases,
        "agent": ((workflow_result.get("result") or {}).get("graph_execution") or {}),
        "response_text": response_text,
        "channel_reply": channel_reply,
        "notifications": notifications,
        "node_trace": workflow_result.get("node_trace") or [],
    }


def list_demo_routes_with_mode() -> list[dict]:
    return get_demo_routes()


def _resolve_customer(sender: dict) -> dict | None:
    customer_id = sender.get("customer_id")
    if customer_id:
        customer = get_crm_customer_by_id(customer_id)
        if customer:
            return customer
    return find_crm_customer_by_phone(_strip_channel_prefix(sender.get("sender_external_id", "")))


def _extract_order_id(message: str) -> str | None:
    match = ORDER_RE.search(message or "")
    if not match:
        return None
    return match.group(1).upper().replace(" ", "-")


def _lookup_order(customer: dict | None, order_id: str) -> dict:
    customer_id = (customer or {}).get("id") or "anon"
    local_order = get_order_by_id(order_id) if order_id else None
    if not local_order:
        customer_orders = get_orders_for_customer(customer_id)
        if customer_orders:
            local_order = customer_orders[0]
    payload = {"order_id": order_id or (local_order or {}).get("order_id") or ""}
    shopify_result = execute_shopify_action("get_order", payload)
    result = shopify_result.get("result") or local_order or {}
    return {
        "trace": {
            "system": "shopify",
            "tool": "get_order",
            "mode": shopify_result.get("mode", "sandbox"),
            "status": shopify_result.get("status", "ok") if result else "not_found",
            "result": result,
            "note": shopify_result.get("note"),
        }
    }


def _compose_customer_response(*, route_id: str, customer: dict | None, order_trace: dict, crm_cases: list[dict], adk_result: dict) -> str:
    customer_name = (customer or {}).get("name") or "there"
    order = order_trace.get("result") or {}
    explanation = ((adk_result.get("explanation") or {}).get("explanation_text") or "").strip()
    if route_id == "order_status":
        order_id = order.get("order_id") or order.get("name") or (customer or {}).get("last_order_id") or "your order"
        status = order.get("status") or "processing"
        base = f"Hi {customer_name}, {order_id} is currently {status}."
        if explanation:
            return f"{base} {explanation}"
        return base
    if route_id == "return_refund":
        return f"Hi {customer_name}, I have prepared the return path for your latest order and logged the request for review."
    if route_id == "loyalty_rewards":
        tier = (customer or {}).get("loyalty_tier") or "standard"
        return f"Hi {customer_name}, your current loyalty tier is {tier} and I have checked your available benefits."
    open_case_count = len(crm_cases or [])
    return f"Hi {customer_name}, I have escalated this issue with priority handling. Open case count is now {open_case_count}."


def _send_channel_reply(binding: dict, sender_external_id: str, response_text: str, *, allow_live_send: bool = False) -> dict:
    channel_type = (binding.get("type") or "").strip().lower()
    metadata = binding.get("metadata") or {}
    if channel_type == "telegram":
        if not allow_live_send:
            return {
                "status": "ok",
                "mode": "configured_preview",
                "connector_source": "telegram_bot_api",
                "note": "live_send_disabled",
                "result": {"chat_id": _strip_channel_prefix(sender_external_id), "text": response_text},
            }
        return send_telegram_message(
            response_text,
            chat_id=_strip_channel_prefix(sender_external_id),
            config_override=metadata,
        )
    return execute_whatsapp_action(
        "send_message",
        {"to": _strip_channel_prefix(sender_external_id), "message": response_text},
        allow_live_send=allow_live_send,
        config_override=metadata,
    )


def _send_notifications(binding: dict, text: str, *, allow_live_send: bool = False) -> list[dict]:
    notifications = []
    for target_id in binding.get("notification_targets") or []:
        target = get_channel_binding(target_id)
        if not target:
            continue
        target_metadata = target.get("metadata") or {}
        if target.get("type") == "telegram":
            notifications.append(
                {
                    "target": target_id,
                    "delivery": (
                        send_telegram_message(
                            text,
                            chat_id=target_metadata.get("default_chat_id"),
                            config_override=target_metadata,
                        )
                        if allow_live_send
                        else {
                            "status": "ok",
                            "mode": "configured_preview",
                            "connector_source": "telegram_bot_api",
                            "note": "live_send_disabled",
                            "result": {
                                "chat_id": target_metadata.get("default_chat_id"),
                                "text": text,
                            },
                        }
                    ),
                }
            )
        elif target.get("type") == "whatsapp":
            notifications.append(
                {
                    "target": target_id,
                    "delivery": execute_whatsapp_action(
                        "send_message",
                        {
                            "to": target_metadata.get("default_recipient") or "",
                            "message": text,
                        },
                        allow_live_send=allow_live_send,
                        config_override=target_metadata,
                    ),
                }
            )
    return notifications


def _build_notification_text(route: dict, customer: dict | None, response_text: str, tool_trace: list[dict]) -> str:
    customer_name = (customer or {}).get("name") or "Unknown customer"
    systems = ", ".join(sorted({step.get("system", "unknown") for step in tool_trace}))
    return (
        f"ACOS route '{route.get('name')}' dispatched for {customer_name}. "
        f"Systems touched: {systems}. Customer response: {response_text}"
    )


def _strip_channel_prefix(value: str) -> str:
    raw = (value or "").strip()
    if ":" not in raw:
        return raw
    return raw.split(":", 1)[1]


def _handle_pairing_message(
    *,
    channel_binding_id: str,
    sender_external_id: str,
    display_name: str,
    message: str,
    tenant_id: str,
    environment: str,
) -> dict | None:
    binding = get_channel_binding(channel_binding_id) or {}
    pair_code, follow_up_message = _extract_pair_code_and_message(binding.get("type"), message)
    if not pair_code:
        return None

    pairing = get_channel_pairing_by_code(channel_binding_id, pair_code)
    if not pairing or pairing.get("status") != "active":
        return {
            "status": "pairing_error",
            "channel_binding_id": channel_binding_id,
            "message": "Pairing code is invalid or no longer active.",
            "pair_code": pair_code,
        }

    customer = find_crm_customer_by_phone(_strip_channel_prefix(sender_external_id))
    sender = get_channel_sender_by_external_id(channel_binding_id, sender_external_id) or {
        "id": f"sender-{uuid4().hex[:10]}",
        "channel_binding_id": channel_binding_id,
        "sender_external_id": sender_external_id,
    }
    sender.update(
        {
            "display_name": display_name or sender.get("display_name") or sender_external_id,
            "customer_id": sender.get("customer_id") or (customer or {}).get("id"),
            "approval_status": "approved",
            "last_message": message,
            "last_seen_at": datetime.now(UTC).isoformat(),
            "metadata": {
                **dict(sender.get("metadata") or {}),
                "channel": binding.get("type"),
                "paired_via": "scan_to_start",
                "pairing_id": pairing.get("id"),
                "paired_at": datetime.now(UTC).isoformat(),
            },
        }
    )
    sender = save_channel_sender(sender)

    pairing["used_at"] = datetime.now(UTC).isoformat()
    save_channel_pairing(pairing)

    routed_message = follow_up_message or (pairing.get("metadata") or {}).get("sample_trigger") or ""
    if not routed_message:
        return {
            "status": "paired",
            "channel_binding_id": channel_binding_id,
            "pairing": pairing,
            "sender": sender,
            "message": "Sender approved through scan-to-start pairing.",
        }

    dispatched = dispatch_demo_route(
        route_id=pairing.get("route_id") or "order_status",
        channel_binding_id=channel_binding_id,
        sender=sender,
        message=routed_message,
        tenant_id=tenant_id,
        environment=environment,
    )
    return {
        "status": "paired_and_dispatched",
        "channel_binding_id": channel_binding_id,
        "pairing": pairing,
        "sender": sender,
        "trigger_message": routed_message,
        "dispatch": dispatched,
    }


def _extract_pair_code_and_message(channel_type: str | None, message: str) -> tuple[str | None, str]:
    text = (message or "").strip()
    if not text:
        return None, ""

    channel = (channel_type or "").strip().lower()
    if channel == "telegram":
        start_match = TELEGRAM_START_RE.match(text)
        if start_match:
            return start_match.group(1).upper(), ""

    pair_match = PAIR_RE.search(text)
    if not pair_match:
        return None, ""

    pair_code = pair_match.group(1).upper()
    remainder = text[pair_match.end():].strip(" :-|")
    if remainder.startswith("::"):
        remainder = remainder[2:].strip()
    return pair_code, remainder
