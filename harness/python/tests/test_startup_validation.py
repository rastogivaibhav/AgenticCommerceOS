import pytest

from acosplatform.config.startup_validation import validate_auth_configuration


def test_non_dev_ops_requires_jwt_secret(monkeypatch):
    monkeypatch.delenv("OPS_JWT_SECRET", raising=False)
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    with pytest.raises(RuntimeError):
        validate_auth_configuration(service="ops-api", environment="production")


def test_non_dev_shopper_requires_api_keys(monkeypatch):
    monkeypatch.delenv("SHOPPER_API_KEYS", raising=False)
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    with pytest.raises(RuntimeError):
        validate_auth_configuration(service="shopper-api", environment="staging")


def test_non_dev_rejects_insecure_dev_auth(monkeypatch):
    monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH", "1")
    monkeypatch.setenv("OPS_JWT_SECRET", "secret")
    with pytest.raises(RuntimeError):
        validate_auth_configuration(service="ops-api", environment="production")


def test_dev_allows_missing_secrets(monkeypatch):
    monkeypatch.delenv("OPS_JWT_SECRET", raising=False)
    monkeypatch.delenv("SHOPPER_API_KEYS", raising=False)
    validate_auth_configuration(service="ops-api", environment="dev")
    validate_auth_configuration(service="shopper-api", environment="development")


def test_non_dev_chat_requires_jwt_and_slack_signing_secret(monkeypatch):
    monkeypatch.delenv("CHAT_JWT_SECRET", raising=False)
    monkeypatch.delenv("OPS_JWT_SECRET", raising=False)
    monkeypatch.delenv("SLACK_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    with pytest.raises(RuntimeError):
        validate_auth_configuration(service="chat-api", environment="production")


def test_non_dev_chat_accepts_ops_jwt_and_slack_signing_secret(monkeypatch):
    monkeypatch.delenv("CHAT_JWT_SECRET", raising=False)
    monkeypatch.setenv("OPS_JWT_SECRET", "ops-secret")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "slack-secret")
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    validate_auth_configuration(service="chat-api", environment="staging")
