"""WhatsApp Cloud API helpers for inbound verification and outbound messaging."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

_DEFAULT_TIMEOUT_SECONDS = 4.0
_DEFAULT_API_VERSION = "v22.0"


@dataclass(frozen=True)
class WhatsAppConfig:
    access_token: str
    phone_number_id: str
    verify_token: str
    api_version: str = _DEFAULT_API_VERSION


def _coerce_config(config_override: dict[str, Any] | None = None) -> WhatsAppConfig | None:
    override = config_override or {}
    access_token = (override.get("access_token") or os.environ.get("WHATSAPP_ACCESS_TOKEN") or "").strip()
    phone_number_id = (override.get("phone_number_id") or os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or "").strip()
    verify_token = (override.get("verify_token") or os.environ.get("WHATSAPP_VERIFY_TOKEN") or "").strip()
    api_version = (override.get("api_version") or os.environ.get("WHATSAPP_API_VERSION") or _DEFAULT_API_VERSION).strip()
    if not access_token or not phone_number_id or not verify_token:
        return None
    return WhatsAppConfig(
        access_token=access_token,
        phone_number_id=phone_number_id,
        verify_token=verify_token,
        api_version=api_version or _DEFAULT_API_VERSION,
    )


def load_whatsapp_config() -> WhatsAppConfig | None:
    return _coerce_config()


def probe_whatsapp_cloud(
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _coerce_config(config_override)
    if not config:
        return {"status": "skipped", "configured": False, "reason": "whatsapp_not_configured"}

    try:
        response = requests.get(
            f"https://graph.facebook.com/{config.api_version}/{config.phone_number_id}",
            params={"fields": "display_phone_number,verified_name"},
            headers={"Authorization": f"Bearer {config.access_token}"},
            timeout=max(float(timeout_seconds), 0.2),
        )
        if response.status_code >= 400:
            return {
                "status": "error",
                "configured": True,
                "status_code": response.status_code,
                "error": f"WhatsApp HTTP {response.status_code}",
            }
        body = response.json() if response.content else {}
        return {
            "status": "ok",
            "configured": True,
            "api_version": config.api_version,
            "phone_number_id": config.phone_number_id,
            "display_phone_number": body.get("display_phone_number"),
            "verified_name": body.get("verified_name"),
        }
    except (requests.Timeout, requests.ConnectionError) as exc:
        return {
            "status": "error",
            "configured": True,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def verify_whatsapp_webhook(
    mode: str,
    token: str,
    challenge: str,
    config_override: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    config = _coerce_config(config_override)
    if not config:
        return False, ""
    if mode == "subscribe" and token == config.verify_token:
        return True, challenge
    return False, ""


def execute_whatsapp_action(
    action: str,
    payload: dict[str, Any],
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    allow_live_send: bool = False,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _coerce_config(config_override)
    action_key = (action or "").strip().lower()
    if not config:
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action_key,
            "connector_source": "local_fallback",
            "note": "whatsapp_not_configured",
            "result": _whatsapp_sandbox_result(action_key, payload),
        }

    if action_key == "inbound_message_trigger":
        return {
            "status": "ok",
            "mode": "live",
            "action": action_key,
            "connector_source": "whatsapp_cloud_api",
            "result": {
                "channel": "whatsapp",
                "verified": True,
                "phone_number_id": config.phone_number_id,
                "preview": payload.get("message") or payload.get("sampleMessage") or "Inbound message received",
            },
        }

    if action_key not in {"send_message", "send_template_message", "handoff_tag"}:
        return {
            "status": "ok",
            "mode": "sandbox",
            "action": action_key,
            "connector_source": "local_fallback",
            "note": "unsupported_action",
            "result": _whatsapp_sandbox_result(action_key, payload),
        }

    if not allow_live_send:
        return {
            "status": "ok",
            "mode": "configured_preview",
            "action": action_key,
            "connector_source": "whatsapp_cloud_api",
            "note": "live_send_disabled",
            "result": _whatsapp_sandbox_result(action_key, payload, phone_number_id=config.phone_number_id),
        }

    to = str(payload.get("to") or "").strip()
    if not to:
        return {
            "status": "ok",
            "mode": "configured_preview",
            "action": action_key,
            "connector_source": "whatsapp_cloud_api",
            "note": "missing_recipient",
            "result": _whatsapp_sandbox_result(action_key, payload, phone_number_id=config.phone_number_id),
        }

    body = {
        "messaging_product": "whatsapp",
        "to": to,
    }
    if action_key == "send_template_message":
        body["type"] = "template"
        body["template"] = {
            "name": payload.get("template_name") or "hello_world",
            "language": {"code": payload.get("language_code") or "en_US"},
        }
    else:
        body["type"] = "text"
        body["text"] = {"preview_url": False, "body": payload.get("message") or "Hello from ACOS"}

    try:
        response = requests.post(
            f"https://graph.facebook.com/{config.api_version}/{config.phone_number_id}/messages",
            headers={
                "Authorization": f"Bearer {config.access_token}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=max(float(timeout_seconds), 0.2),
        )
        response.raise_for_status()
        result = response.json() if response.content else {}
        return {
            "status": "ok",
            "mode": "live",
            "action": action_key,
            "connector_source": "whatsapp_cloud_api",
            "result": result,
        }
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
        return {
            "status": "ok",
            "mode": "configured_preview",
            "action": action_key,
            "connector_source": "whatsapp_cloud_api",
            "note": f"live_send_failed: {exc}",
            "result": _whatsapp_sandbox_result(action_key, payload, phone_number_id=config.phone_number_id),
        }


def _whatsapp_sandbox_result(action: str, payload: dict[str, Any], *, phone_number_id: str | None = None) -> dict[str, Any]:
    return {
        "channel": "whatsapp",
        "action": action,
        "phone_number_id": phone_number_id or "sandbox-phone-number",
        "to": payload.get("to") or "+440000000000",
        "preview": payload.get("message") or payload.get("sampleMessage") or "WhatsApp reply prepared",
    }
