import pytest
from integrations.whatsapp.client import (
    load_whatsapp_config,
    WhatsAppConfig,
    _coerce_config,
    _DEFAULT_API_VERSION
)

def test_load_whatsapp_config_missing_env(monkeypatch):
    # Ensure environment variables are clear
    monkeypatch.delenv("WHATSAPP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
    monkeypatch.delenv("WHATSAPP_VERIFY_TOKEN", raising=False)

    config = load_whatsapp_config()
    assert config is None

def test_load_whatsapp_config_with_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "test-phone")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "test-verify")

    config = load_whatsapp_config()
    assert config is not None
    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "test-token"
    assert config.phone_number_id == "test-phone"
    assert config.verify_token == "test-verify"
    assert config.api_version == _DEFAULT_API_VERSION

def test_coerce_config_override():
    config_override = {
        "access_token": "override-token",
        "phone_number_id": "override-phone",
        "verify_token": "override-verify",
        "api_version": "v10.0"
    }

    config = _coerce_config(config_override)
    assert config is not None
    assert config.access_token == "override-token"
    assert config.phone_number_id == "override-phone"
    assert config.verify_token == "override-verify"
    assert config.api_version == "v10.0"

def test_coerce_config_partial_override_with_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "env-token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "env-phone")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "env-verify")

    config_override = {
        "access_token": "override-token",
        # phone_number_id uses env
        # verify_token uses env
    }

    config = _coerce_config(config_override)
    assert config is not None
    assert config.access_token == "override-token"
    assert config.phone_number_id == "env-phone"
    assert config.verify_token == "env-verify"

def test_coerce_config_whitespace_handling():
    config_override = {
        "access_token": "  token  ",
        "phone_number_id": "  phone  ",
        "verify_token": "  verify  ",
        "api_version": "  v1.0  "
    }

    config = _coerce_config(config_override)
    assert config is not None
    assert config.access_token == "token"
    assert config.phone_number_id == "phone"
    assert config.verify_token == "verify"
    assert config.api_version == "v1.0"
