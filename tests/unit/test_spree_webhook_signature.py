from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.ops_api.routers.spree_webhooks import _verify_or_raise, router, verify_spree_webhook_signature


def signature(body: bytes, timestamp: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), f"{timestamp}.{body.decode('utf-8')}".encode("utf-8"), hashlib.sha256).hexdigest()


def test_valid_signature():
    body = b'{"event_name":"order.completed"}'
    timestamp = str(int(time.time()))
    assert verify_spree_webhook_signature(body, signature(body, timestamp, "secret"), timestamp, "secret") is True


def test_wrong_signature():
    assert verify_spree_webhook_signature(b"{}", "bad", str(int(time.time())), "secret") is False


def test_stale_timestamp():
    timestamp = str(int(time.time() - 301))
    body = b"{}"
    assert verify_spree_webhook_signature(body, signature(body, timestamp, "secret"), timestamp, "secret") is False


def test_future_timestamp():
    timestamp = str(int(time.time() + 301))
    body = b"{}"
    assert verify_spree_webhook_signature(body, signature(body, timestamp, "secret"), timestamp, "secret") is False


def test_missing_signature():
    with pytest.raises(Exception) as exc_info:
        _verify_or_raise(b"{}", None, str(int(time.time())), "secret")
    assert getattr(exc_info.value, "status_code") == 401


def test_non_numeric_timestamp():
    assert verify_spree_webhook_signature(b"{}", "whatever", "not-a-number", "secret") is False


def test_constant_time_no_exception():
    assert verify_spree_webhook_signature(b"{}", "x" * 128, str(int(time.time())), "secret") is False


def test_verify_or_raise_dev_bypass(monkeypatch):
    monkeypatch.setenv("OPS_ENVIRONMENT", "dev")
    _verify_or_raise(b"{}", None, None, "")


def test_verify_or_raise_production_503(monkeypatch):
    monkeypatch.setenv("OPS_ENVIRONMENT", "production")
    with pytest.raises(Exception) as exc_info:
        _verify_or_raise(b"{}", "sig", str(int(time.time())), "")
    assert getattr(exc_info.value, "status_code") == 503


def test_route_accepts_valid_signature(monkeypatch):
    monkeypatch.setenv("SPREE_WEBHOOK_SECRET", "secret")
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = b'{"event_name":"unknown","event_data":{}}'
    timestamp = str(int(time.time()))
    response = client.post(
        "/api/v1/webhooks/spree",
        content=body,
        headers={"X-Spree-Signature": signature(body, timestamp, "secret"), "X-Spree-Timestamp": timestamp},
    )
    assert response.status_code == 200


def test_route_accepts_spree_webhook_header_names(monkeypatch):
    monkeypatch.setenv("SPREE_WEBHOOK_SECRET", "secret")
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = b'{"event_name":"unknown","event_data":{}}'
    timestamp = str(int(time.time()))
    response = client.post(
        "/api/v1/webhooks/spree",
        content=body,
        headers={
            "X-Spree-Webhook-Signature": signature(body, timestamp, "secret"),
            "X-Spree-Webhook-Timestamp": timestamp,
        },
    )
    assert response.status_code == 200
