import os
import pytest
from integrations.whatsapp.client import _coerce_config, load_whatsapp_config, WhatsAppConfig, _DEFAULT_API_VERSION

def test_coerce_config_returns_none_if_missing_required_fields():
    # All missing
    assert _coerce_config({}) is None

    # Missing access_token
    assert _coerce_config({"phone_number_id": "123", "verify_token": "abc"}) is None

    # Missing phone_number_id
    assert _coerce_config({"access_token": "xyz", "verify_token": "abc"}) is None

    # Missing verify_token
    assert _coerce_config({"access_token": "xyz", "phone_number_id": "123"}) is None

def test_coerce_config_uses_override():
    config = _coerce_config({
        "access_token": "token123",
        "phone_number_id": "phone123",
        "verify_token": "verify123",
        "api_version": "v1.0"
    })

    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "token123"
    assert config.phone_number_id == "phone123"
    assert config.verify_token == "verify123"
    assert config.api_version == "v1.0"

def test_coerce_config_uses_env_variables(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "env_token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "env_phone")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "env_verify")
    monkeypatch.setenv("WHATSAPP_API_VERSION", "v2.0")

    config = _coerce_config()

    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "env_token"
    assert config.phone_number_id == "env_phone"
    assert config.verify_token == "env_verify"
    assert config.api_version == "v2.0"

def test_coerce_config_prioritizes_override_over_env(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "env_token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "env_phone")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "env_verify")

    config = _coerce_config({
        "access_token": "override_token",
        "phone_number_id": "override_phone",
        "verify_token": "override_verify"
    })

    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "override_token"
    assert config.phone_number_id == "override_phone"
    assert config.verify_token == "override_verify"

def test_coerce_config_strips_whitespace():
    config = _coerce_config({
        "access_token": "  token  ",
        "phone_number_id": "  phone  ",
        "verify_token": "  verify  ",
        "api_version": "  v3.0  "
    })

    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "token"
    assert config.phone_number_id == "phone"
    assert config.verify_token == "verify"
    assert config.api_version == "v3.0"

def test_coerce_config_uses_default_api_version():
    config = _coerce_config({
        "access_token": "token",
        "phone_number_id": "phone",
        "verify_token": "verify"
    })

    assert isinstance(config, WhatsAppConfig)
    assert config.api_version == _DEFAULT_API_VERSION

def test_load_whatsapp_config(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "load_token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "load_phone")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "load_verify")

    config = load_whatsapp_config()

    assert isinstance(config, WhatsAppConfig)
    assert config.access_token == "load_token"
    assert config.phone_number_id == "load_phone"
    assert config.verify_token == "load_verify"
