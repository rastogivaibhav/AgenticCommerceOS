"""Telegram Bot API helpers for linking, probing, and outbound messaging."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

_DEFAULT_TIMEOUT_SECONDS = 4.0


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    default_chat_id: str = ""
    bot_username: str = ""
    webhook_url: str = ""


def _coerce_config(config_override: dict[str, Any] | None = None) -> TelegramConfig | None:
    override = config_override or {}
    bot_token = (override.get("bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not bot_token:
        return None
    return TelegramConfig(
        bot_token=bot_token,
        default_chat_id=(override.get("default_chat_id") or os.environ.get("TELEGRAM_DEFAULT_CHAT_ID") or "").strip(),
        bot_username=(override.get("bot_username") or os.environ.get("TELEGRAM_BOT_USERNAME") or "").strip(),
        webhook_url=(override.get("webhook_url") or os.environ.get("TELEGRAM_WEBHOOK_URL") or "").strip(),
    )


def load_telegram_config() -> TelegramConfig | None:
    return _coerce_config()


def probe_telegram_bot(
    *,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _coerce_config(config_override)
    if not config:
        return {"status": "skipped", "configured": False, "reason": "telegram_not_configured"}

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{config.bot_token}/getMe",
            timeout=max(float(timeout_seconds), 0.2),
        )
        body = response.json() if response.content else {}
        if response.status_code >= 400 or not body.get("ok"):
            return {
                "status": "error",
                "configured": True,
                "status_code": response.status_code,
                "error": body.get("description") or f"Telegram HTTP {response.status_code}",
            }
        result = body.get("result") or {}
        return {
            "status": "ok",
            "configured": True,
            "username": result.get("username") or config.bot_username,
            "display_name": result.get("first_name"),
            "default_chat_id": config.default_chat_id,
            "webhook_url": config.webhook_url,
        }
    except (requests.Timeout, requests.ConnectionError) as exc:
        return {"status": "error", "configured": True, "error": f"{exc.__class__.__name__}: {exc}"}


def send_telegram_message(
    text: str,
    *,
    chat_id: str | None = None,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _coerce_config(config_override)
    target_chat_id = (chat_id or (config.default_chat_id if config else "") or "").strip()
    if not config or not target_chat_id:
        return {
            "status": "ok",
            "mode": "sandbox",
            "connector_source": "local_fallback",
            "note": "telegram_not_configured",
            "result": {
                "chat_id": target_chat_id or "sandbox-chat",
                "text": text,
            },
        }

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
            json={"chat_id": target_chat_id, "text": text},
            timeout=max(float(timeout_seconds), 0.2),
        )
        body = response.json() if response.content else {}
        if response.status_code >= 400 or not body.get("ok"):
            return {
                "status": "ok",
                "mode": "configured_preview",
                "connector_source": "telegram_bot_api",
                "note": body.get("description") or f"telegram_http_{response.status_code}",
                "result": {
                    "chat_id": target_chat_id,
                    "text": text,
                },
            }
        return {
            "status": "ok",
            "mode": "live",
            "connector_source": "telegram_bot_api",
            "result": body.get("result") or {},
        }
    except (requests.Timeout, requests.ConnectionError) as exc:
        return {
            "status": "ok",
            "mode": "configured_preview",
            "connector_source": "telegram_bot_api",
            "note": f"{exc.__class__.__name__}: {exc}",
            "result": {
                "chat_id": target_chat_id,
                "text": text,
            },
        }
