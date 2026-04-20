"""Tests for Telegram config loader helpers."""

from __future__ import annotations

import os

from integrations.telegram.client import _coerce_config, load_telegram_config


def test_load_telegram_config_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_DEFAULT_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_USERNAME", raising=False)
    monkeypatch.delenv("TELEGRAM_WEBHOOK_URL", raising=False)

    assert load_telegram_config() is None


def test_load_telegram_config_loads_from_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "env-chat-id")
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "env-bot-username")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "env-webhook-url")

    config = load_telegram_config()
    assert config is not None
    assert config.bot_token == "env-token"
    assert config.default_chat_id == "env-chat-id"
    assert config.bot_username == "env-bot-username"
    assert config.webhook_url == "env-webhook-url"


def test_coerce_config_loads_from_override(monkeypatch):
    # Set env variables to ensure overrides take precedence
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "env-chat-id")
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "env-bot-username")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "env-webhook-url")

    override = {
        "bot_token": "override-token",
        "default_chat_id": "override-chat-id",
        "bot_username": "override-bot-username",
        "webhook_url": "override-webhook-url",
    }

    config = _coerce_config(override)
    assert config is not None
    assert config.bot_token == "override-token"
    assert config.default_chat_id == "override-chat-id"
    assert config.bot_username == "override-bot-username"
    assert config.webhook_url == "override-webhook-url"


def test_coerce_config_partial_override(monkeypatch):
    # Set env variables
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
    monkeypatch.setenv("TELEGRAM_DEFAULT_CHAT_ID", "env-chat-id")
    monkeypatch.delenv("TELEGRAM_BOT_USERNAME", raising=False)
    monkeypatch.delenv("TELEGRAM_WEBHOOK_URL", raising=False)

    override = {
        "default_chat_id": "override-chat-id",
        "webhook_url": "override-webhook-url",
    }

    config = _coerce_config(override)
    assert config is not None
    assert config.bot_token == "env-token"
    assert config.default_chat_id == "override-chat-id"
    assert config.bot_username == ""
    assert config.webhook_url == "override-webhook-url"
