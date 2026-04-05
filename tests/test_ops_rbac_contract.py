"""Contract tests for Ops API endpoint-level RBAC behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from apps.ops_api.main import app


JWT_SECRET = "contract-test-secret"


def _mint_token(role: str) -> str:
    jwt = pytest.importorskip("jwt")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"contract-{role}",
        "role": role,
        "roles": [role],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _auth_header(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_mint_token(role)}"}


@pytest.fixture(autouse=True)
def _secure_auth_env(monkeypatch):
    monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH", "0")
    monkeypatch.setenv("OPS_JWT_SECRET", JWT_SECRET)


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_missing_bearer_rejected(client: TestClient):
    response = client.get("/agents")
    assert response.status_code in (401, 403)


def test_invalid_bearer_rejected(client: TestClient):
    response = client.get("/agents", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_analyst_can_read_agents(client: TestClient, monkeypatch):
    monkeypatch.setattr("apps.ops_api.main.get_agents", lambda: [{"id": "a1"}])
    response = client.get("/agents", headers=_auth_header("analyst"))
    assert response.status_code == 200
    assert response.json()["agents"][0]["id"] == "a1"


def test_analyst_cannot_create_agent(client: TestClient):
    payload = {"id": "agent-1", "name": "Agent 1"}
    response = client.post("/agents", json=payload, headers=_auth_header("analyst"))
    assert response.status_code == 403


def test_ops_can_create_agent(client: TestClient, monkeypatch):
    monkeypatch.setattr("acosplatform.db.repository.save_agent", lambda _agent: None)
    payload = {"id": "agent-2", "name": "Agent 2"}
    response = client.post("/agents", json=payload, headers=_auth_header("ops"))
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_ops_cannot_create_tenant(client: TestClient):
    payload = {"id": "tenant-ops-blocked", "name": "Blocked"}
    response = client.post("/tenants", json=payload, headers=_auth_header("ops"))
    assert response.status_code == 403


def test_admin_can_create_tenant(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "acosplatform.tenancy.manager.add_tenant",
        lambda tenant_id, metadata: {"id": tenant_id, **metadata},
    )
    monkeypatch.setattr("apps.ops_api.main.audit", lambda *args, **kwargs: None)
    monkeypatch.setattr("apps.ops_api.main.save_audit_event", lambda *args, **kwargs: None)

    payload = {"id": "tenant-admin", "name": "Retail North"}
    response = client.post("/tenants", json=payload, headers=_auth_header("admin"))
    assert response.status_code == 200
    assert response.json()["tenant"]["id"] == "tenant-admin"


def test_metrics_requires_auth(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code in (401, 403)


def test_analyst_can_read_metrics(client: TestClient, monkeypatch):
    monkeypatch.setattr("apps.ops_api.main.metrics_endpoint", lambda: {"ok": 1})
    response = client.get("/metrics", headers=_auth_header("analyst"))
    assert response.status_code == 200
    assert response.json() == {"ok": 1}
