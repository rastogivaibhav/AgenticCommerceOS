import pytest
from fastapi import HTTPException, status

from acosplatform.auth.api_key import _decode_jwt, _get_valid_api_keys, _extract_roles


def test_api_keys_fail_closed_when_not_configured(monkeypatch):
    monkeypatch.delenv("SHOPPER_API_KEYS", raising=False)
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    assert _get_valid_api_keys() == set()


def test_api_keys_allow_dev_opt_in(monkeypatch):
    monkeypatch.delenv("SHOPPER_API_KEYS", raising=False)
    monkeypatch.setenv("ALLOW_INSECURE_DEV_AUTH", "1")
    assert _get_valid_api_keys() == {"dev-key-insecure"}


def test_ops_jwt_fail_closed_when_not_configured(monkeypatch):
    monkeypatch.delenv("OPS_JWT_SECRET", raising=False)
    monkeypatch.delenv("ALLOW_INSECURE_DEV_AUTH", raising=False)
    with pytest.raises(HTTPException) as exc:
        _decode_jwt("anything")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_extract_roles_from_multiple_claim_shapes():
    payload = {
        "role": "Admin",
        "roles": ["ops", "analyst"],
        "realm_access": {"roles": ["manager", "OPS"]},
    }
    roles = _extract_roles(payload)
    assert "admin" in roles
    assert "ops" in roles
    assert "analyst" in roles
    assert "manager" in roles
