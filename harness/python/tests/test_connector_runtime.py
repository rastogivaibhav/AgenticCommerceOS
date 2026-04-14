"""Connector runtime tests for Week-8 integration layer."""

from __future__ import annotations

import requests
import pytest

from integrations.connectors.runtime import (
    ConnectorContract,
    ConnectorExecutionError,
    execute_connector,
)


class _FakeResponse:
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self._body = body or {}
        self.content = b"{}"

    def json(self):
        return self._body


def test_local_connector_route_uses_fallback_handler():
    contract = ConnectorContract(
        name="catalog",
        required_request_fields=("tenant_id",),
        required_response_fields=("products",),
    )
    result = execute_connector(
        contract=contract,
        payload={"tenant_id": "default", "query": "laptop"},
        tenant_config={"connectors": {"catalog": {"mode": "local"}}},
        local_handler=lambda payload: {"products": [{"id": "prod-1"}], "query": payload["query"]},
    )
    assert result.source == "local"
    assert result.degraded is False
    assert result.data["products"][0]["id"] == "prod-1"


def test_connector_retries_retryable_status(monkeypatch):
    contract = ConnectorContract(
        name="pricing",
        required_request_fields=("tenant_id", "products"),
        required_response_fields=("products", "currency"),
        retries=2,
        backoff_seconds=0.0,
    )
    calls = {"count": 0}

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(503, {"error": "busy"})
        return _FakeResponse(200, {"products": [{"id": "prod-1"}], "currency": "USD"})

    monkeypatch.setattr(requests, "post", fake_post)
    result = execute_connector(
        contract=contract,
        payload={"tenant_id": "default", "products": [{"id": "prod-1"}]},
        tenant_config={"connectors": {"pricing": {"mode": "remote", "url": "http://pricing.local"}}},
        local_handler=lambda payload: {"products": payload["products"], "currency": "USD"},
    )
    assert calls["count"] == 2
    assert result.source == "remote"
    assert result.attempts == 2


def test_connector_timeout_falls_back_to_local(monkeypatch):
    contract = ConnectorContract(
        name="promotions",
        required_request_fields=("tenant_id", "products"),
        required_response_fields=("products", "total_savings"),
        retries=1,
        backoff_seconds=0.0,
    )

    def fake_post(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests, "post", fake_post)
    result = execute_connector(
        contract=contract,
        payload={"tenant_id": "default", "products": [{"id": "prod-1"}]},
        tenant_config={"connectors": {"promotions": {"mode": "remote", "url": "http://promo.local"}}},
        local_handler=lambda payload: {"products": payload["products"], "total_savings": 0.0},
    )
    assert result.source == "local"
    assert result.degraded is True
    assert "Timeout" in (result.error or "")


def test_connector_contract_rejects_missing_fields():
    contract = ConnectorContract(name="orders", required_request_fields=("tenant_id", "customer_id"))
    with pytest.raises(ConnectorExecutionError):
        execute_connector(
            contract=contract,
            payload={"tenant_id": "default"},
            tenant_config=None,
            local_handler=lambda payload: {"orders": []},
        )
