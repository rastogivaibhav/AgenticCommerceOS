"""Week-10 baseline tests for tenant quota and rate-limit controls."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.shopper_api import main as shopper_main
from acosplatform.tenancy import traffic_control


@pytest.fixture(autouse=True)
def reset_traffic_state():
    traffic_control.reset_tenant_traffic_state()
    yield
    traffic_control.reset_tenant_traffic_state()


def test_rate_limit_blocks_hot_tenant_but_not_neighbors():
    limits = traffic_control.TenantTrafficLimits(
        requests_per_minute=2,
        daily_quota=100,
        max_in_flight=4,
    )

    controller = traffic_control.tenant_traffic_controller
    controller.acquire("default", limits)
    controller.release("default")
    controller.acquire("default", limits)
    controller.release("default")

    with pytest.raises(traffic_control.TenantQuotaExceeded) as exc:
        controller.acquire("default", limits)
    assert exc.value.limit_type == "rate_limit"

    controller.acquire("eu-store", limits)
    controller.release("eu-store")


def test_daily_quota_enforced_per_tenant():
    limits = traffic_control.TenantTrafficLimits(
        requests_per_minute=20,
        daily_quota=2,
        max_in_flight=2,
    )
    controller = traffic_control.tenant_traffic_controller

    controller.acquire("default", limits)
    controller.release("default")
    controller.acquire("default", limits)
    controller.release("default")

    with pytest.raises(traffic_control.TenantQuotaExceeded) as exc:
        controller.acquire("default", limits)
    assert exc.value.limit_type == "daily_quota"


def test_in_flight_limit_enforced():
    limits = traffic_control.TenantTrafficLimits(
        requests_per_minute=20,
        daily_quota=20,
        max_in_flight=1,
    )
    controller = traffic_control.tenant_traffic_controller

    controller.acquire("default", limits)
    try:
        with pytest.raises(traffic_control.TenantQuotaExceeded) as exc:
            controller.acquire("default", limits)
        assert exc.value.limit_type == "in_flight_limit"
    finally:
        controller.release("default")


def test_journey_returns_429_when_tenant_limit_exceeded(monkeypatch):
    client = TestClient(shopper_main.app, raise_server_exceptions=False)

    calls = {"count": 0}

    def fake_run_journey(_payload):
        calls["count"] += 1
        return {
            "run_id": "run-test",
            "journey": "discovery",
            "workflow": {},
            "trace": {"trace_id": "trace-test"},
            "context": {"session_id": "ctx-test"},
            "result": {},
        }

    monkeypatch.setattr(shopper_main, "run_journey", fake_run_journey)
    monkeypatch.setattr(
        traffic_control,
        "resolve_tenant_limits",
        lambda _tenant_id: traffic_control.TenantTrafficLimits(
            requests_per_minute=1,
            daily_quota=100,
            max_in_flight=2,
        ),
    )

    first = client.post("/journey", json={"message": "hello"}, headers={"X-API-Key": "dev-key-insecure"})
    second = client.post("/journey", json={"message": "hello"}, headers={"X-API-Key": "dev-key-insecure"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["limit_type"] == "rate_limit"
    assert int(second.headers["Retry-After"]) >= 1
    assert calls["count"] == 1
